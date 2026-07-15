"""Способы оплаты: доступность, инструкции/QR, ссылка Robokassa.

mock      — тестовая мгновенная оплата (redirect на /api/mock/pay).
robokassa — реальный шлюз: redirect на страницу Robokassa + Result URL (вебхук).
crypto    — перевод USDT на адрес (ручное подтверждение админом). QR = адрес.
card      — перевод на карту/СБП по номеру (ручное подтверждение). Без QR.
"""
import base64
import hashlib
import io
from urllib.parse import urlencode

from .config import Settings

MANUAL_METHODS = ("crypto", "card")
_HASH_ALGOS = ("md5", "sha1", "sha256", "sha384", "sha512")


def _robokassa_enabled(settings: Settings) -> bool:
    return bool(
        settings.robokassa_login
        and settings.robokassa_password1
        and settings.robokassa_password2
    )


def _ton_enabled(settings: Settings) -> bool:
    return bool(settings.ton_receive_address)


def _usdt_ton_enabled(settings: Settings) -> bool:
    # USDT-жетон живёт только в mainnet; нужен адрес-получатель и мастер жетона.
    return bool(
        settings.ton_receive_address
        and settings.ton_usdt_master
        and settings.ton_network == "mainnet"
    )


def available_methods(settings: Settings) -> list[dict]:
    methods: list[dict] = []
    if settings.payments_mock:
        methods.append(
            {
                "id": "mock",
                "title": "Тестовая оплата",
                "description": "Мгновенно, без реальных денег",
            }
        )
    if _robokassa_enabled(settings):
        methods.append(
            {
                "id": "robokassa",
                "title": "Банковская карта / СБП",
                "description": "Онлайн-оплата через Robokassa",
            }
        )
    if _ton_enabled(settings):
        methods.append(
            {
                "id": "ton",
                "title": "Оплата в TON",
                "description": "Криптокошелёк TON (TON Connect)",
            }
        )
    if _usdt_ton_enabled(settings):
        methods.append(
            {
                "id": "usdt_ton",
                "title": "USDT (в сети TON)",
                "description": "Стейблкоин USDT через TON Connect",
            }
        )
    if settings.crypto_address:
        methods.append(
            {
                "id": "crypto",
                "title": "Криптовалюта",
                "description": settings.crypto_network,
            }
        )
    if settings.card_details:
        methods.append(
            {
                "id": "card",
                "title": "Перевод на карту / СБП",
                "description": "Оплата переводом по номеру",
            }
        )
    return methods


def is_enabled(settings: Settings, method: str) -> bool:
    return any(m["id"] == method for m in available_methods(settings))


def _qr_data_uri(payload: str) -> str:
    """SVG-QR в виде data-uri. При отсутствии библиотеки — пустая строка."""
    if not payload:
        return ""
    try:
        import qrcode
        import qrcode.image.svg

        img = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage)
        buf = io.BytesIO()
        img.save(buf)
        return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def manual_instructions(
    method: str, settings: Settings, order_id: int, total_kopecks: int
) -> dict:
    rub = total_kopecks / 100
    if method == "crypto":
        title = "Криптовалюта"
        details = (
            f"Сеть: {settings.crypto_network}\n"
            f"Адрес: {settings.crypto_address}\n"
            f"Сумма: {rub:.2f} ₽ (эквивалент в USDT по курсу)\n"
            f"Комментарий: заказ №{order_id}"
        )
        qr_svg = _qr_data_uri(settings.crypto_address)
    else:  # card
        title = "Перевод на карту / СБП"
        details = (
            f"{settings.card_details}\n\n"
            "Скопируйте номер и вставьте в приложении своего банка — "
            "оно само откроет экран перевода.\n\n"
            f"Сумма: {rub:.2f} ₽\n"
            f"Назначение: заказ №{order_id}"
        )
        qr_svg = ""
    return {
        "method": method,
        "title": title,
        "details": details,
        "amount_kopecks": total_kopecks,
        "qr_svg": qr_svg,
    }


def _rk_hash(algo: str, value: str) -> str:
    name = (algo or "md5").lower()
    if name not in _HASH_ALGOS:
        name = "md5"
    return hashlib.new(name, value.encode()).hexdigest()


def robokassa_payment_url(
    settings: Settings, order_id: int, total_kopecks: int, description: str
) -> str:
    """Ссылка на страницу оплаты Robokassa.

    Подпись: hash(MerchantLogin:OutSum:InvId:Пароль#1).
    """
    out_sum = f"{total_kopecks / 100:.2f}"
    inv_id = str(order_id)
    signature = _rk_hash(
        settings.robokassa_hash,
        f"{settings.robokassa_login}:{out_sum}:{inv_id}:{settings.robokassa_password1}",
    )
    params = {
        "MerchantLogin": settings.robokassa_login,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": description,
        "SignatureValue": signature,
        "Culture": "ru",
        "Encoding": "utf-8",
    }
    if settings.robokassa_test:
        params["IsTest"] = "1"
    return settings.robokassa_url + "?" + urlencode(params)


def verify_robokassa_result(
    settings: Settings, out_sum: str, inv_id: str, signature: str
) -> bool:
    """Проверка подписи Result URL: hash(OutSum:InvId:Пароль#2)."""
    computed = _rk_hash(
        settings.robokassa_hash,
        f"{out_sum}:{inv_id}:{settings.robokassa_password2}",
    )
    return bool(signature) and computed.lower() == signature.lower()
