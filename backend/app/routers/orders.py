"""Роутер заказов: способы оплаты, создание, список, подтверждение оплаты."""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from .. import notifier
from .. import paymethods
from .. import repository as repo
from ..config import get_settings
from ..db import db_session
from ..deps import full_name, get_current_user
from ..models import (
    OrderCreate,
    OrderCreateResult,
    OrderOut,
    PaymentMethodOut,
)

router = APIRouter(prefix="/api", tags=["orders"])

METHOD_LABELS = {"mock": "Тестовая", "crypto": "Крипта", "card": "Карта/СБП"}


@router.get("/payment-methods", response_model=List[PaymentMethodOut])
def payment_methods(user: dict = Depends(get_current_user)):
    return paymethods.available_methods(get_settings())


@router.post("/orders", response_model=OrderCreateResult)
def create_order(body: OrderCreate, user: dict = Depends(get_current_user)):
    settings = get_settings()
    if not paymethods.is_enabled(settings, body.method):
        raise HTTPException(status_code=400, detail="Способ оплаты недоступен")

    with db_session() as conn:
        try:
            order_id, total = repo.create_order(
                conn,
                user_tg_id=int(user["id"]),
                user_name=full_name(user),
                items=[(item.product_id, item.qty) for item in body.items],
                note=body.note,
                method=body.method,
            )
        except repo.OrderError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if body.method == "mock":
            payment_id = f"mock_{order_id}_{uuid4().hex[:8]}"
            repo.set_order_payment(conn, order_id, payment_id)
            confirmation_url = f"{settings.api_base_url}/api/mock/pay/{order_id}"
            return OrderCreateResult(
                order_id=order_id, kind="redirect", confirmation_url=confirmation_url
            )

        # Ручные методы (crypto/card): возвращаем инструкции.
        instructions = paymethods.manual_instructions(
            body.method, settings, order_id, total
        )
    return OrderCreateResult(
        order_id=order_id, kind="manual", instructions=instructions
    )


@router.post("/orders/{order_id}/claim")
def claim_paid(order_id: int, user: dict = Depends(get_current_user)):
    """Покупатель отмечает, что оплатил (ручной метод) — уведомляем админа."""
    with db_session() as conn:
        order = repo.get_order(conn, order_id)
        if not order or int(order["user_tg_id"]) != int(user["id"]):
            raise HTTPException(status_code=404, detail="Заказ не найден")
        items = repo.get_order_items(conn, order_id)

    total = order["total_kopecks"] / 100
    method_label = METHOD_LABELS.get(order["payment_method"], order["payment_method"])
    lines = ", ".join(f"{i['title']} x{i['qty']}" for i in items)
    notifier.notify_admin(
        f"🔔 Покупатель отметил оплату заказа №{order_id} ({method_label}) на {total:.2f} ₽\n"
        f"От: {order['user_name']}\nСостав: {lines}\n"
        f"Проверьте поступление и подтвердите заказ в админке (статус -> Оплачен)."
    )
    return {"ok": True}


@router.get("/orders", response_model=List[OrderOut])
def my_orders(user: dict = Depends(get_current_user)):
    with db_session() as conn:
        return repo.list_orders_by_user(conn, int(user["id"]))
