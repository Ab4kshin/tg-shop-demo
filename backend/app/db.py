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


def init_db() -> None:
    """Создать таблицы из schema.sql (идемпотентно) + миграции."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        _migrate(conn)


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
