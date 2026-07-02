"""Админские эндпоинты. Защита по ADMIN_TOKEN (заголовок X-Admin-Token)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .. import repository as repo
from ..config import get_settings
from ..db import db_session
from ..deps import require_admin
from ..models import (
    AdminLogin,
    AdminLoginResult,
    AdminOrderOut,
    OrderStatusUpdate,
    ProductIn,
    ProductOut,
    ProductUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResult)
def login(body: AdminLogin):
    settings = get_settings()
    import hmac as _hmac

    if not settings.admin_password or not _hmac.compare_digest(
        body.password, settings.admin_password
    ):
        raise HTTPException(status_code=401, detail="Неверный пароль")
    return AdminLoginResult(token=settings.admin_token)


@router.get(
    "/orders",
    response_model=List[AdminOrderOut],
    dependencies=[Depends(require_admin)],
)
def all_orders():
    with db_session() as conn:
        return repo.list_all_orders(conn)


@router.patch("/orders/{order_id}", dependencies=[Depends(require_admin)])
def update_order_status(order_id: int, body: OrderStatusUpdate):
    with db_session() as conn:
        if not repo.set_order_status(conn, order_id, body.status):
            raise HTTPException(status_code=404, detail="Заказ не найден")
    return {"ok": True}


@router.get(
    "/products",
    response_model=List[ProductOut],
    dependencies=[Depends(require_admin)],
)
def admin_products():
    with db_session() as conn:
        return repo.list_products(conn, include_inactive=True)


@router.post(
    "/products", response_model=ProductOut, dependencies=[Depends(require_admin)]
)
def create_product(body: ProductIn):
    with db_session() as conn:
        return repo.create_product(conn, body.model_dump())


@router.patch(
    "/products/{product_id}",
    response_model=ProductOut,
    dependencies=[Depends(require_admin)],
)
def update_product(product_id: int, body: ProductUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    with db_session() as conn:
        product = repo.update_product(conn, product_id, fields)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@router.get("/stats", dependencies=[Depends(require_admin)])
def stats():
    with db_session() as conn:
        return repo.stats(conn)
