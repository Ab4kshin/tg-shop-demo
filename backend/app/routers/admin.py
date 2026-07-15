"""Админские эндпоинты. Защита по ADMIN_TOKEN (заголовок X-Admin-Token)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .. import messages
from .. import repository as repo
from ..config import get_settings
from ..db import db_session
from ..deps import require_admin
from ..models import (
    AdminLangIn,
    AdminLogin,
    AdminLoginResult,
    AdminOrderOut,
    CategoryIn,
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


@router.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int):
    with db_session() as conn:
        if repo.product_in_orders(conn, product_id):
            raise HTTPException(
                status_code=400,
                detail="Товар есть в заказах — его можно только скрыть",
            )
        repo.delete_product(conn, product_id)
    return {"ok": True}


@router.post("/admin-lang", dependencies=[Depends(require_admin)])
def set_admin_lang(body: AdminLangIn):
    """Язык админских уведомлений (синхронизируется с языком дашборда)."""
    lang = "en" if messages.norm_lang(body.lang) == "en" else "ru"
    with db_session() as conn:
        repo.set_setting(conn, "admin_lang", lang)
    return {"ok": True, "lang": lang}


@router.get("/stats", dependencies=[Depends(require_admin)])
def stats():
    with db_session() as conn:
        return repo.stats(conn)


@router.get(
    "/categories",
    response_model=List[str],
    dependencies=[Depends(require_admin)],
)
def admin_categories():
    with db_session() as conn:
        return repo.list_categories(conn)


@router.post(
    "/categories",
    response_model=List[str],
    dependencies=[Depends(require_admin)],
)
def add_category(body: CategoryIn):
    with db_session() as conn:
        repo.create_category(conn, body.name)
        return repo.list_categories(conn)


@router.delete("/categories/{name}", dependencies=[Depends(require_admin)])
def remove_category(name: str):
    with db_session() as conn:
        if repo.category_in_use(conn, name):
            raise HTTPException(
                status_code=400, detail="Категория используется товарами"
            )
        repo.delete_category(conn, name)
    return {"ok": True}
