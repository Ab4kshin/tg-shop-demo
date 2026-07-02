"""Синхронная отправка уведомлений в Telegram через Bot API.

Уведомления не должны ронять обработку запроса — ошибки глушатся.
"""
import logging

import httpx

from .config import get_settings

log = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"


def _send(chat_id: int, text: str) -> None:
    settings = get_settings()
    if not settings.bot_token or not chat_id:
        return
    url = TELEGRAM_API + "/bot" + settings.bot_token + "/sendMessage"
    try:
        httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Не удалось отправить уведомление: %s", exc)


def notify_user(user_tg_id: int, text: str) -> None:
    _send(user_tg_id, text)


def notify_admin(text: str) -> None:
    _send(get_settings().admin_chat_id, text)
