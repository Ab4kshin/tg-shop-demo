"""Базовые тесты: серверный расчёт суммы и валидация Telegram initData.

Запуск из папки backend/:
    pytest
Не требует fastapi — проверяет чистую логику (repository, auth).
"""
import hashlib
import hmac
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlencode

from app import auth, repository as repo

SCHEMA = (Path(__file__).parents[1] / "app" / "schema.sql").read_text(
    encoding="utf-8"
)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def test_server_computes_total_from_db_prices():
    conn = _conn()
    repo.create_product(
        conn,
        {"title": "A", "price_kopecks": 10000, "category": "Без повода"},
    )
    repo.create_product(
        conn,
        {"title": "B", "price_kopecks": 25000, "category": "Свадьба"},
    )
    # Клиент мог бы подсунуть свою цену — но мы считаем по БД.
    order_id, total = repo.create_order(
        conn, user_tg_id=1, user_name="T", items=[(1, 2), (2, 1)]
    )
    assert order_id == 1
    assert total == 10000 * 2 + 25000  # 45000


def test_inactive_product_rejected():
    conn = _conn()
    repo.create_product(
        conn,
        {
            "title": "Hidden",
            "price_kopecks": 100,
            "category": "Без повода",
            "is_active": False,
        },
    )
    try:
        repo.create_order(conn, user_tg_id=1, user_name="T", items=[(1, 1)])
        assert False, "ожидалась OrderError"
    except repo.OrderError:
        pass


def test_mark_paid_is_idempotent():
    conn = _conn()
    repo.create_product(
        conn, {"title": "A", "price_kopecks": 100, "category": "Без повода"}
    )
    order_id, _ = repo.create_order(
        conn, user_tg_id=1, user_name="T", items=[(1, 1)]
    )
    repo.set_order_payment(conn, order_id, "pay_1")
    first = repo.mark_order_paid_by_payment(conn, "pay_1")
    second = repo.mark_order_paid_by_payment(conn, "pay_1")
    assert first is not None and first["status"] == "paid"
    assert second is None  # повторное подтверждение не меняет состояние


def _make_init_data(bot_token: str, user: dict) -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(user, separators=(",", ":")),
    }
    dcs = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(
        secret, dcs.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(fields)


def test_valid_init_data_accepted():
    token = "123456:TEST"
    init_data = _make_init_data(token, {"id": 42, "first_name": "Ivan"})
    user = auth.validate_init_data(init_data, token, max_age=86400)
    assert user is not None and user["id"] == 42


def test_tampered_init_data_rejected():
    token = "123456:TEST"
    init_data = _make_init_data(token, {"id": 42})
    tampered = init_data.replace("id%3A42", "id%3A999")
    assert auth.validate_init_data(tampered, token, max_age=86400) is None
