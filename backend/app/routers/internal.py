"""Внутренние эндпоинты для бота (защита по INTERNAL_SECRET).

Бот не имеет Telegram initData в обычном чате, поэтому для /orders
он ходит сюда с общим секретом и указывает user_tg_id явно.
"""
from typing import List

from fastapi import APIRouter, Header, HTTPException

from .. import repository as repo
from ..config import get_settings
from ..db import db_session
from ..models import OrderOut

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.get("/orders/{user_tg_id}", response_model=List[OrderOut])
def bot_orders(user_tg_id: int, x_internal_secret: str = Header(default="")):
    settings = get_settings()
    import hmac as _hmac

    if not settings.internal_secret or not _hmac.compare_digest(
        x_internal_secret, settings.internal_secret
    ):
        raise HTTPException(status_code=401, detail="Нет доступа")
    with db_session() as conn:
        return repo.list_orders_by_user(conn, user_tg_id)
