"""Конфигурация приложения. Все значения читаются из .env."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # URLs
    miniapp_url: str = ""
    api_base_url: str = "http://localhost:8000"

    # Админ-дашборд
    admin_password: str = ""
    admin_token: str = ""

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

    @field_validator("payments_mock", mode="before")
    @classmethod
    def _parse_bool(cls, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on", "da")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
