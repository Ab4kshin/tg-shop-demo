"""Telegram-бот (aiogram 3).

  /start   — спрашивает язык (Русский/English), запоминает его и показывает
             приветствие + WebApp-кнопку «Открыть магазин» (открывает TMA)
  /orders  — список заказов пользователя (через внутренний API backend)

Выбранный язык становится основным: бот сохраняет его в backend (для своих
сообщений/уведомлений) и пробрасывает в мини-аппку через ?lang=<ru|en>.

Уведомления об оплате шлёт сам backend (через Telegram Bot API), боту ничего
ловить не нужно — он только обрабатывает команды.

Запуск:
    python bot.py
"""
import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MINIAPP_URL = os.getenv("MINIAPP_URL", "")
BOT_API_URL = os.getenv("BOT_API_URL", "http://127.0.0.1:8000")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")

# Локализация статусов заказа.
STATUS_LABELS = {
    "ru": {
        "new": "🆕 Ожидает оплаты",
        "paid": "✅ Оплачен",
        "shipped": "📦 Отправлен",
        "done": "🎉 Завершён",
        "canceled": "❌ Отменён",
    },
    "en": {
        "new": "🆕 Awaiting payment",
        "paid": "✅ Paid",
        "shipped": "📦 Shipped",
        "done": "🎉 Completed",
        "canceled": "❌ Canceled",
    },
}

# Тексты сообщений бота.
TEXTS = {
    "ru": {
        "choose_lang": "Выберите язык / Choose your language:",
        "no_miniapp": (
            "Привет! 🎁 Магазин почти готов, но не задан адрес мини-аппки.\n\n"
            "Запустите ./tgshop.sh build (при активном ngrok) — он сам пропишет "
            "MINIAPP_URL, либо задайте его вручную: ./tgshop.sh miniapp <https-url>. "
            "Затем перезапустите бота (./tgshop.sh dev)."
        ),
        "open_shop": "🛍️ Открыть магазин",
        "welcome": (
            "Привет! Это демо-магазин подарков 🎁\n\n"
            "Нажмите кнопку ниже, чтобы открыть каталог, "
            "или отправьте /orders — посмотреть свои заказы."
        ),
        "orders_off": "Список заказов недоступен: сервер не настроен.",
        "orders_err": "Не удалось получить заказы. Попробуйте позже.",
        "orders_empty": "У вас пока нет заказов. Откройте магазин через /start.",
        "orders_title": "<b>Ваши заказы:</b>",
    },
    "en": {
        "choose_lang": "Choose your language / Выберите язык:",
        "no_miniapp": (
            "Hi! 🎁 The shop is almost ready, but the mini-app URL is not set.\n\n"
            "Run ./tgshop.sh build (with ngrok active) — it will set MINIAPP_URL "
            "automatically, or set it manually: ./tgshop.sh miniapp <https-url>. "
            "Then restart the bot (./tgshop.sh dev)."
        ),
        "open_shop": "🛍️ Open shop",
        "welcome": (
            "Hi! This is a demo gift shop 🎁\n\n"
            "Tap the button below to open the catalog, "
            "or send /orders to see your orders."
        ),
        "orders_off": "Orders are unavailable: the server is not configured.",
        "orders_err": "Couldn't fetch your orders. Please try again later.",
        "orders_empty": "You have no orders yet. Open the shop via /start.",
        "orders_title": "<b>Your orders:</b>",
    },
}


def _norm(code: str) -> str:
    """language_code -> 'ru' | 'en' (пустота / ru* -> 'ru')."""
    code = (code or "").lower()
    return "ru" if not code or code.startswith("ru") else "en"


def _tg_lang(message: Message) -> str:
    """Язык из Telegram language_code как фоллбэк."""
    code = ""
    if message.from_user and message.from_user.language_code:
        code = message.from_user.language_code
    return _norm(code)


def _webapp_url(lang: str) -> str:
    """MINIAPP_URL с проброшенным ?lang=<ru|en> для мини-аппки."""
    sep = "&" if "?" in MINIAPP_URL else "?"
    return f"{MINIAPP_URL}{sep}lang={lang}"


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский", callback_data="lang:ru"
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English", callback_data="lang:en"
                ),
            ]
        ]
    )


def _shop_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TEXTS[lang]["open_shop"],
                    web_app=WebAppInfo(url=_webapp_url(lang)),
                )
            ]
        ]
    )


async def _save_lang(user_id: int, lang: str) -> None:
    """Сохранить выбранный язык в backend (для уведомлений/сообщений)."""
    if not INTERNAL_SECRET:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{BOT_API_URL}/api/internal/user-lang",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
                json={"user_tg_id": user_id, "lang": lang},
            )
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Не удалось сохранить язык пользователя %s: %s", user_id, exc
        )


async def _stored_lang(user_id: int, fallback: str) -> str:
    """Сохранённый выбор языка из backend; иначе — fallback."""
    if not INTERNAL_SECRET:
        return fallback
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BOT_API_URL}/api/internal/user-lang/{user_id}",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
            resp.raise_for_status()
            lang = resp.json().get("lang")
            if lang in ("ru", "en"):
                return lang
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Не удалось получить язык пользователя %s из backend: %s", user_id, exc
        )
    return fallback


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Предлагаем выбрать язык на двух языках (предварительно — по Telegram).
    lang = _tg_lang(message)
    await message.answer(TEXTS[lang]["choose_lang"], reply_markup=_lang_keyboard())


@dp.callback_query(F.data.startswith("lang:"))
async def on_lang(callback: CallbackQuery) -> None:
    lang = "en" if callback.data.split(":", 1)[1] == "en" else "ru"
    t = TEXTS[lang]
    await _save_lang(callback.from_user.id, lang)
    if not MINIAPP_URL.startswith("https://"):
        await callback.message.edit_text(t["no_miniapp"])
    else:
        await callback.message.edit_text(
            t["welcome"], reply_markup=_shop_keyboard(lang)
        )
    await callback.answer()


@dp.message(Command("orders"))
async def cmd_orders(message: Message) -> None:
    lang = await _stored_lang(message.from_user.id, _tg_lang(message))
    t = TEXTS[lang]
    if not INTERNAL_SECRET:
        await message.answer(t["orders_off"])
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BOT_API_URL}/api/internal/orders/{message.from_user.id}",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
            resp.raise_for_status()
            orders = resp.json()
    except Exception:  # noqa: BLE001
        await message.answer(t["orders_err"])
        return

    if not orders:
        await message.answer(t["orders_empty"])
        return

    labels = STATUS_LABELS[lang]
    lines = [t["orders_title"], ""]
    for order in orders:
        total = order["total_kopecks"] / 100
        label = labels.get(order["status"], order["status"])
        no = "№" if lang == "ru" else "#"
        lines.append(f"{no}{order['id']} — {label} — {total:.2f} \u20bd")
    await message.answer("\n".join(lines))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан в .env")
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
