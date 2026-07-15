"""Pydantic-схемы запросов и ответов API."""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

CATEGORIES = ["День рождения", "Свадьба", "Извинение", "Без повода"]
STATUSES = ["new", "paid", "shipped", "done", "canceled"]
METHODS = ["mock", "robokassa", "ton", "usdt_ton", "crypto", "card"]


class ProductOut(BaseModel):
    id: int
    title: str
    description: str
    price_kopecks: int
    photo_url: str
    category: str
    is_active: bool


class OrderItemIn(BaseModel):
    product_id: int
    qty: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    items: List[OrderItemIn] = Field(min_length=1)
    note: str = ""
    method: str = "mock"

    @field_validator("method")
    @classmethod
    def _check_method(cls, v: str) -> str:
        if v not in METHODS:
            raise ValueError(f"недопустимый способ оплаты: {v}")
        return v


class OrderItemOut(BaseModel):
    product_id: int
    title: str
    qty: int
    price_at_purchase_kopecks: int


class OrderOut(BaseModel):
    id: int
    status: str
    total_kopecks: int
    note: str
    created_at: str
    items: List[OrderItemOut] = []


class AdminOrderOut(OrderOut):
    user_tg_id: int
    user_name: str
    payment_id: Optional[str] = None
    payment_method: str = ""
    updated_at: str


class ManualInstructions(BaseModel):
    method: str
    title: str
    details: str
    amount_kopecks: int
    qr_svg: str = ""


class TonPaymentOut(BaseModel):
    order_id: int
    address: str
    amount_nano: str
    amount_ton: str
    amount_rub: float
    comment: str
    network: str
    manifest_url: str = ""
    expires_at: int
    # Актив: "ton" (нативная монета) или "usdt" (жетон jUSDT).
    asset: str = "ton"
    asset_label: str = "TON"
    jetton_master: str = ""       # адрес мастер-контракта жетона (для usdt)
    amount_units: str = ""        # минимальные единицы жетона (для usdt)
    usdt_decimals: int = 6


class TonStatusOut(BaseModel):
    status: str


class OrderCreateResult(BaseModel):
    order_id: int
    kind: str  # "redirect" | "manual" | "ton"
    confirmation_url: Optional[str] = None
    instructions: Optional[ManualInstructions] = None
    ton: Optional[TonPaymentOut] = None


class PaymentMethodOut(BaseModel):
    id: str
    title: str
    description: str = ""


class AdminLogin(BaseModel):
    password: str


class AdminLoginResult(BaseModel):
    token: str


class ProductIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    price_kopecks: int = Field(ge=0)
    photo_url: str = ""
    category: str
    is_active: bool = True

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("категория не может быть пустой")
        return v.strip()


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price_kopecks: Optional[int] = Field(default=None, ge=0)
    photo_url: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("категория не может быть пустой")
        return v.strip() if v is not None else v


class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in STATUSES:
            raise ValueError(f"недопустимый статус: {v}")
        return v


class CategoryIn(BaseModel):
    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("название категории не может быть пустым")
        return v


class UserLangIn(BaseModel):
    user_tg_id: int
    lang: str


class AdminLangIn(BaseModel):
    lang: str
