"""Публичные метаданные витрины: категории и валюты."""
from typing import List

from fastapi import APIRouter

from .. import rates
from .. import repository as repo
from ..config import get_settings
from ..db import db_session

router = APIRouter(prefix="/api", tags=["meta"])

# Метаданные валют витрины. Базовая валюта цен в БД — RUB.
_CURRENCY_META = [
    {"code": "RUB", "symbol": "\u20bd", "locale": "ru-RU"},
    {"code": "USD", "symbol": "$", "locale": "en-US"},
    {"code": "EUR", "symbol": "\u20ac", "locale": "de-DE"},
]


@router.get("/categories", response_model=List[str])
def list_categories():
    with db_session() as conn:
        return repo.list_categories(conn)


@router.get("/currencies")
def list_currencies():
    """Курсы для витрины: rub_per_unit = сколько ₽ стоит 1 единица валюты."""
    settings = get_settings()
    fiat = rates.get_fiat_rates(
        settings.fiat_rate_ttl,
        settings.rub_per_usd_fallback,
        settings.rub_per_eur_fallback,
    )
    currencies = [
        {**meta, "rub_per_unit": round(float(fiat.get(meta["code"], 1.0)), 6)}
        for meta in _CURRENCY_META
    ]
    return {"base": "RUB", "currencies": currencies}
