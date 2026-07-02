"""Наполнение БД демо-товарами.

Запуск из папки backend/:
    python -m app.seed

Цены указаны в КОПЕЙКАХ (например, 3490 руб = 349000).
"""
from .db import db_session, init_db

# (title, description, price_kopecks, photo_url, category)
PRODUCTS = [
    (
        "Букет «Нежность»",
        "Пионовидные розы и эвкалипт в крафтовой упаковке.",
        349000,
        "https://picsum.photos/seed/gift1/600/600",
        "День рождения",
    ),
    (
        "Воздушные шары «С Днём Рождения»",
        "Набор из 15 гелиевых шаров с фольгированными буквами.",
        220000,
        "https://picsum.photos/seed/gift2/600/600",
        "День рождения",
    ),
    (
        "Свадебная композиция «Белый танец»",
        "Белые розы, гортензия и лизиантус в шляпной коробке.",
        890000,
        "https://picsum.photos/seed/gift3/600/600",
        "Свадьба",
    ),
    (
        "Кольцо для помолвки (демо)",
        "Ювелирная бижутерия с фианитом. Демонстрационный товар.",
        450000,
        "https://picsum.photos/seed/gift4/600/600",
        "Свадьба",
    ),
    (
        "Открытка «Прости меня»",
        "Крафтовая открытка ручной работы с доставкой в конверте.",
        59000,
        "https://picsum.photos/seed/gift5/600/600",
        "Извинение",
    ),
    (
        "Мишка Тедди + записка",
        "Плюшевый мишка 40 см и персональная записка от вас.",
        179000,
        "https://picsum.photos/seed/gift6/600/600",
        "Извинение",
    ),
    (
        "Шоколадные конфеты ручной работы",
        "Набор из 12 конфет ручной работы в подарочной коробке.",
        129000,
        "https://picsum.photos/seed/gift7/600/600",
        "Без повода",
    ),
    (
        "Подарочная корзина с фруктами",
        "Сезонные фрукты и мёд в плетёной корзине.",
        399000,
        "https://picsum.photos/seed/gift8/600/600",
        "Без повода",
    ),
]


def seed() -> None:
    init_db()
    with db_session() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if existing:
            print(f"В таблице products уже есть {existing} записей — сид пропущен.")
            return
        conn.executemany(
            """
            INSERT INTO products (title, description, price_kopecks, photo_url, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            PRODUCTS,
        )
        print(f"Добавлено товаров: {len(PRODUCTS)}")


if __name__ == "__main__":
    seed()
