"""Внутренние эндпоинты для бота (защита по INTERNAL_SECRET).

Бот не имеет Telegram initData в обычном чате, поэтому для /orders и
сохранения выбранного языка он ходит сюда с общим секретом и указывает
user_tg_id явно.
"""
import hmac
from typing import List

from fastapi import APIRouter, Header, HTTPException

from .. import messages
from .. import repository as repo
from ..config import get_settings
from ..db import db_session
from ..models import OrderOut, UserLangIn

router = APIRouter(prefix="/api/internal", tags=["internal"])


def _check_secret(secret: str) -> None:
    settings = get_settings()
    if not settings.internal_secret or not hmac.compare_digest(
        secret, settings.internal_secret
    ):
        raise HTTPException(status_code=401, detail="Нет доступа")


@router.get("/orders/{user_tg_id}", response_model=List[OrderOut])
def bot_orders(user_tg_id: int, x_internal_secret: str = Header(default="")):
    _check_secret(x_internal_secret)
    with db_session() as conn:
        return repo.list_orders_by_user(conn, user_tg_id)


@router.post("/user-lang")
def set_user_lang(body: UserLangIn, x_internal_secret: str = Header(default="")):
    """Сохранить выбранный в /start язык пользователя (ru|en)."""
    _check_secret(x_internal_secret)
    lang = "en" if messages.norm_lang(body.lang) == "en" else "ru"
    with db_session() as conn:
        repo.set_user_lang(conn, body.user_tg_id, lang)
    return {"ok": True, "lang": lang}


@router.get("/user-lang/{user_tg_id}")
def get_user_lang(user_tg_id: int, x_internal_secret: str = Header(default="")):
    """Отдать сохранённый язык пользователя (или null)."""
    _check_secret(x_internal_secret)
    with db_session() as conn:
        return {"lang": repo.get_user_lang(conn, user_tg_id)}
