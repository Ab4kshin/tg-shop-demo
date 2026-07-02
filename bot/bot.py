"""Telegram-бот (aiogram 3).

  /start   — приветствие + WebApp-кнопка «Открыть магазин» (открывает TMA)
  /orders  — список заказов пользователя (через внутренний API backend)

Уведомления об оплате шлёт сам backend (через Telegram Bot API), боту ничего
ловить не нужно — он только обрабатывает команды.

Запуск:
    python bot.py
"""
import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
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

STATUS_LABELS = {
    "new": "🆕 Ожидает оплаты",
    "paid": "✅ Оплачен",
    "shipped": "📦 Отправлен",
    "done": "🎉 Завершён",
    "canceled": "❌ Отменён",
}

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not MINIAPP_URL.startswith("https://"):
        await message.answer(
            "Привет! 🎁 Магазин почти готов, но не задан адрес мини-аппки.\n\n"
            "Добавьте MINIAPP_URL (https-ссылка на Netlify) в bot/.env и перезапустите бота."
        )
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍️ Открыть магазин",
                    web_app=WebAppInfo(url=MINIAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "Привет! Это демо-магазин подарков 🎁\n\n"
        "Нажмите кнопку ниже, чтобы открыть каталог, "
        "или отправьте /orders — посмотреть свои заказы.",
        reply_markup=keyboard,
    )


@dp.message(Command("orders"))
async def cmd_orders(message: Message) -> None:
    if not INTERNAL_SECRET:
        await message.answer("Список заказов недоступен: сервер не настроен.")
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
        await message.answer("Не удалось получить заказы. Попробуйте позже.")
        return

    if not orders:
        await message.answer("У вас пока нет заказов. Откройте магазин через /start.")
        return

    lines = ["<b>Ваши заказы:</b>", ""]
    for order in orders:
        total = order["total_kopecks"] / 100
        label = STATUS_LABELS.get(order["status"], order["status"])
        lines.append(f"№{order['id']} — {label} — {total:.2f} ₽")
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
