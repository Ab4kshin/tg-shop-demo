"""Подключение к SQLite и инициализация схемы."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import get_settings

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Открыть соединение с БД (row_factory = Row, включены внешние ключи)."""
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Лёгкие миграции для БД, созданных раньше (ADD COLUMN идемпотентно)."""
    try:
        conn.execute(
            "ALTER TABLE orders ADD COLUMN payment_method TEXT NOT NULL DEFAULT ''"
        )
    except sqlite3.OperationalError:
        pass  # колонка уже есть
    for ddl in (
        "ALTER TABLE orders ADD COLUMN pay_amount_nano INTEGER",
        "ALTER TABLE orders ADD COLUMN pay_comment TEXT",
        "ALTER TABLE orders ADD COLUMN user_lang TEXT NOT NULL DEFAULT ''",
    ):
        try:
            conn.execute(ddl)
        except sqlite3.OperationalError:
            pass  # колонка уже есть


DEFAULT_CATEGORIES = ["День рождения", "Свадьба", "Извинение", "Без повода"]


def _drop_category_check(conn: sqlite3.Connection) -> None:
    """Убрать CHECK со столбца products.category (нужно для кастомных категорий)."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='products'"
    ).fetchone()
    if not row or "category IN (" not in (row["sql"] or ""):
        return
    conn.executescript(
        """
        PRAGMA foreign_keys=OFF;
        BEGIN;
        CREATE TABLE products_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            description   TEXT    NOT NULL DEFAULT '',
            price_kopecks INTEGER NOT NULL CHECK (price_kopecks >= 0),
            photo_url     TEXT    NOT NULL DEFAULT '',
            category      TEXT    NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );
        INSERT INTO products_new
            (id, title, description, price_kopecks, photo_url, category, is_active, created_at)
            SELECT id, title, description, price_kopecks, photo_url, category, is_active, created_at
            FROM products;
        DROP TABLE products;
        ALTER TABLE products_new RENAME TO products;
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        COMMIT;
        PRAGMA foreign_keys=ON;
        """
    )


def _ensure_categories(conn: sqlite3.Connection) -> None:
    """Гарантировать таблицу categories и наполнить дефолтами + текущими."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS categories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )"""
    )
    count = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()["c"]
    if count == 0:
        for name in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,)
            )
    for r in conn.execute("SELECT DISTINCT category FROM products").fetchall():
        if r["category"]:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)", (r["category"],)
            )


def init_db() -> None:
    """Создать таблицы из schema.sql (идемпотентно) + миграции."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        _migrate(conn)
        _drop_category_check(conn)
        _ensure_categories(conn)


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    """Транзакционная сессия: commit при успехе, rollback при ошибке."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
