"""Роутер проверки TON/USDT-оплаты (мини-аппка опрашивает статус)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from .. import messages
from .. import notifier
from .. import paymethods
from .. import repository as repo
from .. import tonpay
from ..config import get_settings
from ..db import db_session
from ..deps import get_current_user
from ..models import TonStatusOut

router = APIRouter(prefix="/api", tags=["ton"])


def _finalize(order_id: int, payment_id: str, asset_label: str) -> None:
    with db_session() as conn:
        result = repo.mark_order_paid_by_payment(conn, payment_id)
        if not result:
            return  # идемпотентно: уже обработан или не найден
        items = repo.get_order_items(conn, order_id)

    total = result["total_kopecks"] / 100
    lines = ", ".join(f"{i['title']} x{i['qty']}" for i in items)
    # Уведомление админу — на языке, который покупатель выбрал в /start.
    user_lang = messages.norm_lang(result.get("user_lang"))
    notifier.notify_user(
        result["user_tg_id"],
        messages.user_paid(user_lang, order_id, total, asset_label),
    )
    notifier.notify_admin(
        messages.admin_paid(
            user_lang, order_id, total, result["user_name"], lines, asset=asset_label
        )
    )


@router.get("/ton/check/{order_id}", response_model=TonStatusOut)
async def ton_check(order_id: int, user: dict = Depends(get_current_user)):
    settings = get_settings()

    with db_session() as conn:
        order = repo.get_order(conn, order_id)
        if not order or int(order["user_tg_id"]) != int(user["id"]):
            raise HTTPException(status_code=404, detail="Заказ не найден")
        method = order["payment_method"]
        if order["status"] != "new":
            return TonStatusOut(status=order["status"])
        comment = order["pay_comment"] or f"o{order_id}"
        expected = int(order["pay_amount_nano"] or 0)

    if method not in ("ton", "usdt_ton") or not paymethods.is_enabled(
        settings, method
    ):
        raise HTTPException(status_code=404, detail="TON-оплата недоступна")

    if expected <= 0:
        return TonStatusOut(status="pending")

    min_amount = int(expected * settings.ton_amount_tolerance)
    if method == "ton":
        paid = await run_in_threadpool(
            tonpay.find_incoming_payment, settings, comment, min_amount
        )
        payment_id, asset_label = f"ton_{order_id}", "TON"
    else:
        paid = await run_in_threadpool(
            tonpay.find_incoming_jetton_payment, settings, comment, min_amount
        )
        payment_id, asset_label = f"usdtton_{order_id}", "USDT"

    if not paid:
        return TonStatusOut(status="pending")

    await run_in_threadpool(_finalize, order_id, payment_id, asset_label)
    return TonStatusOut(status="paid")
