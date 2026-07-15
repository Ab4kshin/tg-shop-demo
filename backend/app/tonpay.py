"""Проверка входящих платежей в сети TON.

- Нативный TON: смотрим транзакции адреса через toncenter (v2 getTransactions),
  ищем входящее сообщение с нужным текстовым комментарием и суммой.
- USDT (jetton): жетон-переводы не видны как обычные транзакции с
  комментарием. Сначала пробуем tonapi (он декодирует комментарий),
  а если tonapi недоступен — падаем на toncenter (v3 jetton/transfers).

Важно: в некоторых сетях TLS-хендшейк к tonapi.io / coingecko периодически
отваливается (_ssl.c handshake timeout), а toncenter при этом работает.
Поэтому USDT-оплата теперь тоже может подтверждаться через toncenter.
Все внешние запросы идут с несколькими попытками и увеличенным таймаутом.
"""
import logging
import time

import httpx

from .config import Settings

log = logging.getLogger(__name__)


def _get_json(url, params=None, headers=None, attempts=3, timeout=25):
    """GET с повторами. Возвращает распарсенный JSON или None при неудаче."""
    for i in range(attempts):
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "Запрос %s: попытка %d/%d не удалась: %s",
                url, i + 1, attempts, exc,
            )
            time.sleep(0.6)
    return None


def _toncenter_base(settings: Settings) -> str:
    if settings.ton_network == "testnet":
        return "https://testnet.toncenter.com"
    return "https://toncenter.com"


def find_incoming_payment(
    settings: Settings, comment: str, min_nano: int
) -> bool:
    """True, если на адрес пришёл TON с этим комментарием и суммой >= min_nano."""
    address = settings.ton_receive_address
    if not address or not comment or min_nano <= 0:
        return False
    url = _toncenter_base(settings) + "/api/v2/getTransactions"
    params = {"address": address, "limit": 40, "archival": "true"}
    headers = {}
    if settings.toncenter_api_key:
        headers["X-API-Key"] = settings.toncenter_api_key
    data = _get_json(url, params=params, headers=headers)
    if data is None:
        return False
    for tx in data.get("result", []):
        in_msg = tx.get("in_msg") or {}
        msg_text = (in_msg.get("message") or "").strip()
        try:
            value = int(in_msg.get("value") or 0)
        except (TypeError, ValueError):
            value = 0
        if msg_text == comment and value >= min_nano:
            return True
    return False


def _tonapi_base(settings: Settings) -> str:
    if settings.ton_network == "testnet":
        return "https://testnet.tonapi.io"
    return "https://tonapi.io"


def _extract_comment(obj) -> str:
    """Достаём текстовый комментарий из разных форматов toncenter/tonapi.

    У разных версий API комментарий лежит либо прямо (comment/text), либо
    во вложенном forward_payload -> value -> text. base64-BOC не декодируем.
    """
    if isinstance(obj, str):
        return obj.strip()
    if not isinstance(obj, dict):
        return ""
    for key in ("comment", "text"):
        val = obj.get(key)
        if isinstance(val, str) and val:
            return val.strip()
    nested = obj.get("forward_payload")
    if nested is None:
        nested = obj.get("value")
    cur = nested
    for _ in range(5):
        if isinstance(cur, str):
            return cur.strip()
        if not isinstance(cur, dict):
            break
        for key in ("text", "comment"):
            val = cur.get(key)
            if isinstance(val, str) and val:
                return val.strip()
        cur = cur.get("value")
    return ""


def _find_jetton_via_tonapi(
    settings: Settings, address: str, comment: str, min_units: int
) -> bool:
    """История жетонов аккаунта через tonapi (декодирует комментарий)."""
    url = _tonapi_base(settings) + f"/v2/accounts/{address}/jettons/history"
    params = {"limit": 100}
    headers = {}
    if settings.tonapi_api_key:
        headers["Authorization"] = f"Bearer {settings.tonapi_api_key}"
    data = _get_json(url, params=params, headers=headers)
    if data is None:
        return False
    for event in data.get("events", []):
        for action in event.get("actions", []):
            if action.get("type") != "JettonTransfer":
                continue
            jt = action.get("JettonTransfer") or {}
            cmt = _extract_comment(jt)
            try:
                amount = int(jt.get("amount") or 0)
            except (TypeError, ValueError):
                amount = 0
            if cmt == comment and amount >= min_units:
                return True
    return False


def _find_jetton_via_toncenter(
    settings: Settings, address: str, comment: str, min_units: int
) -> bool:
    """Резервный путь через toncenter v3 (когда tonapi недоступен).

    toncenter в некоторых сетях доступен, а tonapi/coingecko — нет.
    Совпадение комментария — основной критерий. Если комментарий
    декодировать не удалось, принимаем входящий перевод по сумме (best-effort).
    """
    url = _toncenter_base(settings) + "/api/v3/jetton/transfers"
    params = {"owner_address": address, "direction": "in", "limit": 50}
    headers = {}
    if settings.toncenter_api_key:
        headers["X-API-Key"] = settings.toncenter_api_key
    data = _get_json(url, params=params, headers=headers)
    if data is None:
        return False
    transfers = data.get("jetton_transfers") or data.get("transfers") or []
    for tr in transfers:
        try:
            amount = int(tr.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount < min_units:
            continue
        cmt = _extract_comment(tr)
        if cmt:
            if cmt == comment:
                return True
        else:
            # Комментарий не декодируется — подтверждаем по сумме входящего перевода.
            return True
    return False


def find_incoming_jetton_payment(
    settings: Settings, comment: str, min_units: int
) -> bool:
    """True, если на адрес-получатель пришёл жетон-перевод (USDT) с этим
    комментарием и суммой >= min_units.

    Пробуем два источника: tonapi (точный комментарий), затем toncenter
    (резерв, когда tonapi недоступен из-за сети). Комментарий уникален на
    заказ (o<id>), а история — только по адресу-получателю.
    """
    address = settings.ton_usdt_receive_address or settings.ton_receive_address
    master = settings.ton_usdt_master
    if not address or not master or not comment or min_units <= 0:
        return False
    if _find_jetton_via_tonapi(settings, address, comment, min_units):
        return True
    return _find_jetton_via_toncenter(settings, address, comment, min_units)
