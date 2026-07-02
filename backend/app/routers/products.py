"""Роутер товаров."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .. import repository as repo
from ..db import db_session
from ..models import ProductOut

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=List[ProductOut])
def list_products(category: Optional[str] = Query(default=None)):
    with db_session() as conn:
        return repo.list_products(conn, category=category)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    with db_session() as conn:
        product = repo.get_product(conn, product_id)
    if not product or not product["is_active"]:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product
