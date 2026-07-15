"""Robokassa: Result URL (вебхук с подписью) + Success/Fail страницы.

После оплаты Robokassa дёргает Result URL (server-to-server) — проверяем
подпись (Пароль#2), ставим заказ paid, шлём уведомления, отвечаем OK{InvId}.
"""
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, PlainTextResponse

from .. import messages
from .. import notifier
from .. import paymethods
from .. import repository as repo
from ..config import get_settings
from ..db import db_session

router = APIRouter(prefix="/api", tags=["robokassa"])


def _finalize(order_id: int) -> None:
    with db_session() as conn:
        order = repo.get_order(conn, order_id)
        if not order or order["status"] != "new":
            return  # идемпотентно: уже обработан
        repo.set_order_status(conn, order_id, "paid")
        items = repo.get_order_items(conn, order_id)

    total = order["total_kopecks"] / 100
    lines = ", ".join(f"{i['title']} x{i['qty']}" for i in items)
    # Уведомление админу — на языке, который покупатель выбрал в /start.
    user_lang = messages.norm_lang(order.get("user_lang"))
    notifier.notify_user(
        order["user_tg_id"],
        messages.user_paid(user_lang, order_id, total, "Robokassa"),
    )
    notifier.notify_admin(
        messages.admin_paid(
            user_lang,
            order_id,
            total,
            order["user_name"],
            lines,
            asset="Robokassa",
        )
    )


@router.api_route(
    "/robokassa/result", methods=["GET", "POST"], response_class=PlainTextResponse
)
async def robokassa_result(request: Request):
    settings = get_settings()
    data = dict(request.query_params)
    if request.method == "POST":
        body = (await request.body()).decode("utf-8", errors="ignore")
        data.update(dict(parse_qsl(body)))

    out_sum = data.get("OutSum", "")
    inv_id = data.get("InvId", "")
    signature = data.get("SignatureValue", "")

    if not paymethods.verify_robokassa_result(settings, out_sum, inv_id, signature):
        return PlainTextResponse("bad sign", status_code=400)
    try:
        oid = int(inv_id)
    except ValueError:
        return PlainTextResponse("bad invid", status_code=400)

    await run_in_threadpool(_finalize, oid)
    return PlainTextResponse(f"OK{inv_id}")


_PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;text-align:center;padding:48px 24px;color:#1c1c1e">
<div style="font-size:56px">{icon}</div>
<h1 style="font-size:22px">{title}</h1>
<p style="color:#8e8e93">{text}</p>
</body></html>"""


@router.get("/robokassa/success", response_class=HTMLResponse)
def robokassa_success():
    return _PAGE.format(
        icon="✅",
        title="Оплата прошла",
        text="Заказ оплачен. Вернитесь в Telegram — бот прислал подтверждение.",
    )


@router.get("/robokassa/fail", response_class=HTMLResponse)
def robokassa_fail():
    return _PAGE.format(
        icon="⚠️",
        title="Оплата не завершена",
        text="Платёж не прошёл. Можно попробовать ещё раз из корзины.",
    )
