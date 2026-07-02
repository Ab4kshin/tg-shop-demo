"""Способы оплаты: доступность и инструкции (для ручных методов).

mock   — тестовая мгновенная оплата (redirect на /api/mock/pay).
crypto — перевод USDT на указанный адрес (ручное подтверждение админом). QR содержит
          адрес кошелька — крипто-кошельки такие QR корректно сканируют.
card   — перевод на карту/СБП по номеру (ручное подтверждение админом). Без QR:
          банковские приложения не распознают QR с номером телефона/карты как
          стандартный платёжный QR — только сам номер, введённый вручную.
"""
import base64
import io

from .config import Settings

MANUAL_METHODS = ("crypto", "card")


def available_methods(settings: Settings) -> list[dict]:
    methods: list[dict] = []
    if settings.payments_mock:
        methods.append(
            {
                "id": "mock",
                "title": "Тестовая оплата",
                "description": "Мгновенно, без реальных денег",
            }
        )
    if settings.crypto_address:
        methods.append(
            {
                "id": "crypto",
                "title": "Криптовалюта",
                "description": settings.crypto_network,
            }
        )
    if settings.card_details:
        methods.append(
            {
                "id": "card",
                "title": "Перевод на карту / СБП",
                "description": "Оплата переводом по номеру",
            }
        )
    return methods


def is_enabled(settings: Settings, method: str) -> bool:
    return any(m["id"] == method for m in available_methods(settings))


def _qr_data_uri(payload: str) -> str:
    """SVG-QR в виде data-uri. При отсутствии библиотеки — пустая строка."""
    if not payload:
        return ""
    try:
        import qrcode
        import qrcode.image.svg

        img = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage)
        buf = io.BytesIO()
        img.save(buf)
        svg = buf.getvalue()
        return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
    except Exception:
        return ""


def manual_instructions(
    method: str, settings: Settings, order_id: int, total_kopecks: int
) -> dict:
    rub = total_kopecks / 100
    if method == "crypto":
        # Адрес кошелька — в QR смысле, кошельки его корректно сканируют.
        title = "Криптовалюта"
        details = (
            f"Сеть: {settings.crypto_network}\n"
            f"Адрес: {settings.crypto_address}\n"
            f"Сумма: {rub:.2f} ₽ (эквивалент в USDT по курсу)\n"
            f"Комментарий: заказ №{order_id}"
        )
        qr_svg = _qr_data_uri(settings.crypto_address)
    else:  # card
        # QR для перевода по номеру не нужен — банки его не распознают, показываем текст.
        title = "Перевод на карту / СБП"
        details = (
            f"{settings.card_details}\n\n"
            "Скопируйте номер и вставьте в приложении своего банка — "
            "оно само откроет экран перевода.\n\n"
            f"Сумма: {rub:.2f} ₽\n"
            f"Назначение: заказ №{order_id}"
        )
        qr_svg = ""
    return {
        "method": method,
        "title": title,
        "details": details,
        "amount_kopecks": total_kopecks,
        "qr_svg": qr_svg,
    }
