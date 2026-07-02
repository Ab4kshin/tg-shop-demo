"""Эмуляция оплаты — работает ТОЛЬКО при PAYMENTS_MOCK=true.

Для демо/портфолио без реального платёжного шлюза: открытие confirmation_url
сразу помечает заказ оплаченным и шлёт уведомления.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .. import notifier
from .. import repository as repo
from ..config import get_settings
from ..db import db_session

router = APIRouter(prefix="/api", tags=["mock"])


@router.get("/mock/pay/{order_id}", response_class=HTMLResponse)
def mock_pay(order_id: int):
    settings = get_settings()
    if not settings.payments_mock:
        raise HTTPException(status_code=404, detail="Not found")

    newly_paid = False
    order = None
    items = []
    with db_session() as conn:
        order = repo.get_order(conn, order_id)
        if order and order["status"] == "new":
            repo.set_order_status(conn, order_id, "paid")
            items = repo.get_order_items(conn, order_id)
            newly_paid = True

    if newly_paid and order:
        total = order["total_kopecks"] / 100
        lines = ", ".join(f"{i['title']} x{i['qty']}" for i in items)
        notifier.notify_user(
            order["user_tg_id"],
            f"✅ Оплата получена!\nЗаказ №{order_id} на {total:.2f} ₽ оплачен.",
        )
        notifier.notify_admin(
            f"🟢 (ТЕСТ) Новый оплаченный заказ №{order_id} на {total:.2f} ₽\n"
            f"От: {order['user_name']}\nСостав: {lines}",
        )

    return """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Оплата (тест)</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;text-align:center;padding:48px 24px;color:#1c1c1e">
<div style="font-size:56px">✅</div>
<h1 style="font-size:22px">Оплата прошла (тестовый режим)</h1>
<p style="color:#8e8e93">Заказ отмечен как оплаченный.<br>Вернитесь в Telegram — бот прислал подтверждение.</p>
</body></html>"""
