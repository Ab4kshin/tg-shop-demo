"""Конфигурация приложения. Все значения читаются из .env."""
import json
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Адреса внешних API хранятся в данных (endpoints.json), а не в коде.
_ENDPOINTS = json.loads(
    (Path(__file__).parent / "endpoints.json").read_text(encoding="utf-8")
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram
    bot_token: str = ""
    admin_chat_id: int = 0

    # Способы оплаты
    payments_mock: bool = False           # тестовая мгновенная оплата
    crypto_address: str = ""              # адрес криптокошелька (пусто = выкл)
    crypto_network: str = "USDT (TRC20)"
    card_details: str = ""               # реквизиты карты/СБП (пусто = выкл)

    # Robokassa (реальный платёжный шлюз; пустой login = выкл)
    robokassa_login: str = ""
    robokassa_password1: str = ""
    robokassa_password2: str = ""
    robokassa_test: bool = True           # IsTest=1 (тестовый режим)
    robokassa_hash: str = "md5"           # метод хэша подписи (md5/sha256/...)

    # TON (криптооплата через TON Connect; пустой адрес = выкл)
    ton_receive_address: str = ""        # адрес-получатель TON
    ton_network: str = "mainnet"         # mainnet | testnet
    ton_manifest_url: str = ""           # URL tonconnect-manifest.json (домен мини-аппки)
    toncenter_api_key: str = ""          # опц. ключ toncenter (выше лимиты)
    ton_rate_ttl: int = 120              # TTL кэша курса -> RUB, сек
    ton_payment_ttl: int = 1800          # срок годности выставленной суммы, сек
    ton_amount_tolerance: float = 0.995  # допуск по сумме (0.995 = -0.5%)
    # USDT (жетон jUSDT в сети TON). ТОЛЬКО mainnet. Пустой master = выкл.
    # Мастер jUSDT (mainnet): EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
    ton_usdt_master: str = ""            # адрес мастер-контракта USDT-жетона
    ton_usdt_decimals: int = 6           # десятичные знаки USDT (jUSDT = 6)
    tonapi_api_key: str = ""             # опц. ключ tonapi.io (для проверки жетон-переводов)
    # Отдельный кошелёк-получатель USDT (в сети TON). Пусто = тот же, что TON.
    ton_usdt_receive_address: str = ""
    # Запасные курсы (₽ за 1 монету), если CoinGecko недоступен (0 = только авто).
    ton_rub_fallback: float = 0.0
    usdt_rub_fallback: float = 0.0

    # Фиат-валюты витрины (только отображение). Базовая валюта цен — RUB.
    fiat_rate_ttl: int = 600              # TTL кэша FX-курсов, сек
    rub_per_usd_fallback: float = 90.0    # запасной курс: ₽ за 1 $
    rub_per_eur_fallback: float = 98.0    # запасной курс: ₽ за 1 €

    # URLs
    miniapp_url: str = ""
    api_base_url: str = "http://localhost:8000"

    # Внешние API: адреса вынесены в endpoints.json; можно переопределить
    # одноимённой переменной окружения / в .env.
    robokassa_url: str = _ENDPOINTS["robokassa_url"]
    ton_rate_url: str = _ENDPOINTS["ton_rate_url"]
    usdt_rate_url: str = _ENDPOINTS["usdt_rate_url"]
    fiat_rate_url: str = _ENDPOINTS["fiat_rate_url"]

    # Админ-дашборд
    admin_password: str = ""
    admin_token: str = ""
    admin_lang: str = "ru"                # язык админских уведомлений: ru | en

    # Внутренний секрет для запросов бота к /api/internal/*
    internal_secret: str = ""

    # Прочее
    database_path: str = "data/shop.sqlite3"
    cors_origins: str = "*"
    initdata_max_age: int = 86400

    @field_validator("admin_chat_id", "initdata_max_age", mode="before")
    @classmethod
    def _empty_to_default(cls, value, info):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return 0 if info.field_name == "admin_chat_id" else 86400
        return value

    @field_validator("admin_lang", mode="before")
    @classmethod
    def _norm_admin_lang(cls, value):
        if value is None or not str(value).strip():
            return "ru"
        return "ru" if str(value).strip().lower().startswith("ru") else "en"

    @field_validator("ton_network", mode="before")
    @classmethod
    def _norm_network(cls, value):
        if value is None or not str(value).strip():
            return "mainnet"
        return "testnet" if str(value).strip().lower() == "testnet" else "mainnet"

    @field_validator("payments_mock", "robokassa_test", mode="before")
    @classmethod
    def _parse_bool(cls, value, info):
        # Пусто: robokassa_test по умолчанию True, payments_mock — False.
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return info.field_name == "robokassa_test"
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on", "da")
        return value

    @field_validator("ton_rub_fallback", "usdt_rub_fallback", mode="before")
    @classmethod
    def _empty_float(cls, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @field_validator("rub_per_usd_fallback", "rub_per_eur_fallback", mode="before")
    @classmethod
    def _empty_fiat(cls, value, info):
        default = 90.0 if info.field_name == "rub_per_usd_fallback" else 98.0
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @field_validator("fiat_rate_ttl", mode="before")
    @classmethod
    def _empty_fiat_ttl(cls, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return 600
        try:
            return int(value)
        except (TypeError, ValueError):
            return 600


@lru_cache
def get_settings() -> Settings:
    return Settings()
