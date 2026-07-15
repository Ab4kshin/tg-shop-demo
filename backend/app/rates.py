"""Курсы криптовалют к рублю (CoinGecko) с кэшем в памяти."""
import logging
import threading
import time

import httpx

from .config import get_settings

log = logging.getLogger(__name__)


class RateError(Exception):
    """Не удалось получить курс."""


_ton_lock = threading.Lock()
_ton_cache = {"rate": 0.0, "ts": 0.0}


def _fetch_price(url: str, coin_id: str, attempts: int = 3) -> float | None:
    """Тянет курс монеты к RUB с CoinGecko с несколькими попытками."""
    for i in range(attempts):
        try:
            resp = httpx.get(
                url, timeout=20, headers={"accept": "application/json"}
            )
            resp.raise_for_status()
            value = float(resp.json()[coin_id]["rub"])
            if value > 0:
                return value
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "Курс %s: попытка %d/%d не удалась: %s",
                coin_id, i + 1, attempts, exc,
            )
            time.sleep(0.6)
    return None


def get_ton_rub_rate(ttl: int = 120, fallback: float = 0.0) -> float:
    """Сколько RUB за 1 TON. Кэш на ttl сек. Бросает RateError при неудаче."""
    now = time.time()
    with _ton_lock:
        if _ton_cache["rate"] > 0 and now - _ton_cache["ts"] < ttl:
            return _ton_cache["rate"]
    rate = _fetch_price(get_settings().ton_rate_url, "the-open-network")
    if not rate or rate <= 0:
        with _ton_lock:
            if _ton_cache["rate"] > 0:
                return _ton_cache["rate"]
        if fallback and fallback > 0:
            log.warning("Использую запасной курс TON из .env: %s ₽", fallback)
            return float(fallback)
        raise RateError("Курс TON временно недоступен")
    with _ton_lock:
        _ton_cache["rate"] = rate
        _ton_cache["ts"] = now
    return rate


def rub_to_nanoton(rub: float, rate: float) -> int:
    """RUB -> нано-TON (1 TON = 1e9 нано)."""
    if rate <= 0:
        raise RateError("Некорректный курс TON")
    ton = rub / rate
    return int(round(ton * 1_000_000_000))


_usdt_lock = threading.Lock()
_usdt_cache = {"rate": 0.0, "ts": 0.0}


def get_usdt_rub_rate(ttl: int = 120, fallback: float = 0.0) -> float:
    """Сколько RUB за 1 USDT. Кэш на ttl сек. Бросает RateError при неудаче."""
    now = time.time()
    with _usdt_lock:
        if _usdt_cache["rate"] > 0 and now - _usdt_cache["ts"] < ttl:
            return _usdt_cache["rate"]
    rate = _fetch_price(get_settings().usdt_rate_url, "tether")
    if not rate or rate <= 0:
        with _usdt_lock:
            if _usdt_cache["rate"] > 0:
                return _usdt_cache["rate"]
        if fallback and fallback > 0:
            log.warning("Использую запасной курс USDT из .env: %s ₽", fallback)
            return float(fallback)
        raise RateError("Курс USDT временно недоступен")
    with _usdt_lock:
        _usdt_cache["rate"] = rate
        _usdt_cache["ts"] = now
    return rate


def rub_to_jetton_units(rub: float, rate: float, decimals: int = 6) -> int:
    """RUB -> минимальные единицы жетона (USDT: decimals=6)."""
    if rate <= 0:
        raise RateError("Некорректный курс USDT")
    amount = rub / rate
    return int(round(amount * (10 ** decimals)))


_fiat_lock = threading.Lock()
_fiat_cache = {"usd": 0.0, "eur": 0.0, "ts": 0.0}


def _fetch_fiat() -> tuple[float, float] | None:
    """Вернёт (₽ за 1 USD, ₽ за 1 EUR) из базы RUB open.er-api.com."""
    url = get_settings().fiat_rate_url
    for i in range(3):
        try:
            resp = httpx.get(
                url, timeout=20, headers={"accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
            fx = data.get("rates") or {}
            usd_per_rub = float(fx.get("USD") or 0)
            eur_per_rub = float(fx.get("EUR") or 0)
            if usd_per_rub > 0 and eur_per_rub > 0:
                return (1.0 / usd_per_rub, 1.0 / eur_per_rub)
        except Exception as exc:  # noqa: BLE001
            log.warning("FX-курсы: попытка %d/3 не удалась: %s", i + 1, exc)
            time.sleep(0.6)
    return None


def get_fiat_rates(
    ttl: int = 600,
    rub_per_usd_fallback: float = 90.0,
    rub_per_eur_fallback: float = 98.0,
) -> dict:
    """{'RUB':1.0,'USD':<₽ за $>,'EUR':<₽ за €>}. Никогда не бросает исключение."""
    now = time.time()
    with _fiat_lock:
        if (
            _fiat_cache["usd"] > 0
            and _fiat_cache["eur"] > 0
            and now - _fiat_cache["ts"] < ttl
        ):
            return {"RUB": 1.0, "USD": _fiat_cache["usd"], "EUR": _fiat_cache["eur"]}
    fetched = _fetch_fiat()
    if fetched:
        usd, eur = fetched
        with _fiat_lock:
            _fiat_cache["usd"] = usd
            _fiat_cache["eur"] = eur
            _fiat_cache["ts"] = now
        return {"RUB": 1.0, "USD": usd, "EUR": eur}
    with _fiat_lock:
        if _fiat_cache["usd"] > 0 and _fiat_cache["eur"] > 0:
            return {"RUB": 1.0, "USD": _fiat_cache["usd"], "EUR": _fiat_cache["eur"]}
    return {
        "RUB": 1.0,
        "USD": float(rub_per_usd_fallback or 90.0),
        "EUR": float(rub_per_eur_fallback or 98.0),
    }
