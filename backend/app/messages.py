"""Локализация текстов уведомлений (RU/EN).

Язык покупателя берётся из его Telegram language_code (сохраняется в заказе).
Язык админских уведомлений — из настройки ADMIN_LANG.
"""
from typing import Optional


def norm_lang(code: Optional[str]) -> str:
    """Нормализовать код языка в  'ru' | 'en' (пустота -> 'ru')."""
    if not code:
        return "ru"
    return "ru" if str(code).strip().lower().startswith("ru") else "en"


_METHOD = {
    "ru": {
        "mock": "Тестовая",
        "robokassa": "Robokassa",
        "ton": "TON",
        "usdt_ton": "USDT",
        "crypto": "Крипта",
        "card": "Карта/СБП",
    },
    "en": {
        "mock": "Test",
        "robokassa": "Robokassa",
        "ton": "TON",
        "usdt_ton": "USDT",
        "crypto": "Crypto",
        "card": "Card/SBP",
    },
}


def method_label(lang: str, method: str) -> str:
    return _METHOD.get(lang, _METHOD["ru"]).get(method, method)


def _fmt_total(total: float) -> str:
    # Базовая валюта цен — рубли; суммы в уведомлениях всегда в ₽.
    return f"{total:.2f} \u20bd"


def user_paid(lang: str, order_id: int, total: float, asset: str = "") -> str:
    """Уведомление покупателю об успешной оплате."""
    total_str = _fmt_total(total)
    if lang == "en":
        text = f"\u2705 Payment received!\nOrder #{order_id} for {total_str} has been paid"
        return text + (f" ({asset})." if asset else ".")
    text = f"\u2705 Оплата получена!\nЗаказ №{order_id} на {total_str} оплачен"
    return text + (f" ({asset})." if asset else ".")


def admin_paid(
    lang: str,
    order_id: int,
    total: float,
    user_name: str,
    items: str,
    asset: str = "",
    test: bool = False,
) -> str:
    """Уведомление админу о новом оплаченном заказе."""
    total_str = _fmt_total(total)
    if lang == "en":
        tag = " (TEST)" if test else ""
        head = f"\U0001f7e2{tag} New paid order #{order_id} for {total_str}"
        if asset:
            head += f" ({asset})"
        return head + f"\nFrom: {user_name}\nItems: {items}"
    tag = " (ТЕСТ)" if test else ""
    head = f"\U0001f7e2{tag} Новый оплаченный заказ №{order_id} на {total_str}"
    if asset:
        head += f" ({asset})"
    return head + f"\nОт: {user_name}\nСостав: {items}"


def admin_claim(
    lang: str,
    order_id: int,
    method_label_str: str,
    total: float,
    user_name: str,
    items: str,
) -> str:
    """Уведомление админу: покупатель отметил ручную оплату."""
    total_str = _fmt_total(total)
    if lang == "en":
        return (
            f"\U0001f514 Customer marked order #{order_id} ({method_label_str}) as paid for {total_str}\n"
            f"From: {user_name}\nItems: {items}\n"
            "Check the incoming payment and confirm the order in the admin panel (status -> Paid)."
        )
    return (
        f"\U0001f514 Покупатель отметил оплату заказа №{order_id} ({method_label_str}) на {total_str}\n"
        f"От: {user_name}\nСостав: {items}\n"
        "Проверьте поступление и подтвердите заказ в админке (статус -> Оплачен)."
    )
