"""Роутер заказов: способы оплаты, создание, список, подтверждение оплаты."""
import time
from typing import Callable, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from .. import messages
from .. import notifier
from .. import paymethods
from .. import rates
from .. import repository as repo
from ..config import Settings, get_settings
from ..db import db_session
from ..deps import full_name, get_current_user
from ..models import (
    OrderCreate,
    OrderCreateResult,
    OrderOut,
    PaymentMethodOut,
    TonPaymentOut,
)

router = APIRouter(prefix="/api", tags=["orders"])


@router.get("/payment-methods", response_model=List[PaymentMethodOut])
def payment_methods(user: dict = Depends(get_current_user)):
    return paymethods.available_methods(get_settings())


def _result_mock(conn, settings: Settings, order_id: int, total: int, method: str):
    payment_id = f"mock_{order_id}_{uuid4().hex[:8]}"
    repo.set_order_payment(conn, order_id, payment_id)
    url = f"{settings.api_base_url}/api/mock/pay/{order_id}"
    return OrderCreateResult(order_id=order_id, kind="redirect", confirmation_url=url)


def _result_robokassa(conn, settings: Settings, order_id: int, total: int, method: str):
    repo.set_order_payment(conn, order_id, f"rk_{order_id}")
    url = paymethods.robokassa_payment_url(
        settings, order_id, total, f"Заказ №{order_id}"
    )
    return OrderCreateResult(order_id=order_id, kind="redirect", confirmation_url=url)


def _result_ton(conn, settings: Settings, order_id: int, total: int, method: str):
    rub = total / 100
    try:
        rate = rates.get_ton_rub_rate(settings.ton_rate_ttl, settings.ton_rub_fallback)
        amount_nano = rates.rub_to_nanoton(rub, rate)
    except rates.RateError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if amount_nano <= 0:
        raise HTTPException(status_code=503, detail="Не удалось рассчитать сумму TON")
    comment = f"o{order_id}"
    repo.set_order_payment(conn, order_id, f"ton_{order_id}")
    repo.set_order_ton(conn, order_id, amount_nano, comment)
    ton = TonPaymentOut(
        order_id=order_id,
        address=settings.ton_receive_address,
        amount_nano=str(amount_nano),
        amount_ton=f"{amount_nano / 1_000_000_000:.4f}",
        amount_rub=round(rub, 2),
        comment=comment,
        network=settings.ton_network,
        manifest_url=settings.ton_manifest_url,
        expires_at=int(time.time()) + settings.ton_payment_ttl,
        asset="ton",
        asset_label="TON",
    )
    return OrderCreateResult(order_id=order_id, kind="ton", ton=ton)


def _result_usdt_ton(conn, settings: Settings, order_id: int, total: int, method: str):
    rub = total / 100
    try:
        rate = rates.get_usdt_rub_rate(
            settings.ton_rate_ttl, settings.usdt_rub_fallback
        )
        units = rates.rub_to_jetton_units(rub, rate, settings.ton_usdt_decimals)
    except rates.RateError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if units <= 0:
        raise HTTPException(status_code=503, detail="Не удалось рассчитать сумму USDT")
    comment = f"o{order_id}"
    repo.set_order_payment(conn, order_id, f"usdtton_{order_id}")
    repo.set_order_ton(conn, order_id, units, comment)
    ton = TonPaymentOut(
        order_id=order_id,
        address=settings.ton_usdt_receive_address or settings.ton_receive_address,
        amount_nano=str(units),
        amount_ton=f"{units / (10 ** settings.ton_usdt_decimals):.2f}",
        amount_rub=round(rub, 2),
        comment=comment,
        network=settings.ton_network,
        manifest_url=settings.ton_manifest_url,
        expires_at=int(time.time()) + settings.ton_payment_ttl,
        asset="usdt",
        asset_label="USDT",
        jetton_master=settings.ton_usdt_master,
        amount_units=str(units),
        usdt_decimals=settings.ton_usdt_decimals,
    )
    return OrderCreateResult(order_id=order_id, kind="ton", ton=ton)


def _result_manual(conn, settings: Settings, order_id: int, total: int, method: str):
    """Ручные методы (crypto/card): возвращаем инструкции для перевода."""
    instructions = paymethods.manual_instructions(method, settings, order_id, total)
    return OrderCreateResult(
        order_id=order_id, kind="manual", instructions=instructions
    )


# Таблица обработчиков вместо лестницы if по body.method. Неизвестные методы,
# прошедшие paymethods.is_enabled (crypto/card), обрабатываются как ручные.
_ORDER_HANDLERS: Dict[str, Callable] = {
    "mock": _result_mock,
    "robokassa": _result_robokassa,
    "ton": _result_ton,
    "usdt_ton": _result_usdt_ton,
}


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
                user_lang=repo.get_user_lang(conn, int(user["id"]))
                or messages.norm_lang(user.get("language_code")),
            )
        except repo.OrderError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        handler = _ORDER_HANDLERS.get(body.method, _result_manual)
        return handler(conn, settings, order_id, total, body.method)


@router.post("/orders/{order_id}/claim")
def claim_paid(order_id: int, user: dict = Depends(get_current_user)):
    """Покупатель отмечает, что оплатил (ручной метод) — уведомляем админа."""
    with db_session() as conn:
        order = repo.get_order(conn, order_id)
        if not order or int(order["user_tg_id"]) != int(user["id"]):
            raise HTTPException(status_code=404, detail="Заказ не найден")
        items = repo.get_order_items(conn, order_id)

    total = order["total_kopecks"] / 100
    # Уведомление админу — на языке, который покупатель выбрал в /start.
    lang = messages.norm_lang(order.get("user_lang"))
    method_label = messages.method_label(lang, order["payment_method"])
    lines = ", ".join(f"{i['title']} x{i['qty']}" for i in items)
    notifier.notify_admin(
        messages.admin_claim(
            lang, order_id, method_label, total, order["user_name"], lines
        )
    )
    return {"ok": True}


@router.get("/orders", response_model=List[OrderOut])
def my_orders(user: dict = Depends(get_current_user)):
    with db_session() as conn:
        return repo.list_orders_by_user(conn, int(user["id"]))
