"""Доступ к данным. Весь SQL — только параметризованные запросы."""
import sqlite3
from typing import List, Optional, Tuple

_NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
_ALLOWED_PRODUCT_COLS = {
    "title",
    "description",
    "price_kopecks",
    "photo_url",
    "category",
    "is_active",
}


class OrderError(Exception):
    """Ошибка бизнес-логики при создании заказа."""


def _product_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "price_kopecks": row["price_kopecks"],
        "photo_url": row["photo_url"],
        "category": row["category"],
        "is_active": bool(row["is_active"]),
    }


def list_products(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    include_inactive: bool = False,
) -> List[dict]:
    query = "SELECT * FROM products"
    conds, params = [], []
    if not include_inactive:
        conds.append("is_active = 1")
    if category:
        conds.append("category = ?")
        params.append(category)
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY id"
    return [_product_to_dict(r) for r in conn.execute(query, params).fetchall()]


def get_product(conn: sqlite3.Connection, product_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    return _product_to_dict(row) if row else None


def create_product(conn: sqlite3.Connection, data: dict) -> dict:
    cur = conn.execute(
        """INSERT INTO products
               (title, description, price_kopecks, photo_url, category, is_active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data["title"],
            data.get("description", ""),
            data["price_kopecks"],
            data.get("photo_url", ""),
            data["category"],
            1 if data.get("is_active", True) else 0,
        ),
    )
    return get_product(conn, cur.lastrowid)


def update_product(
    conn: sqlite3.Connection, product_id: int, fields: dict
) -> Optional[dict]:
    fields = {k: v for k, v in fields.items() if k in _ALLOWED_PRODUCT_COLS}
    if not fields:
        return get_product(conn, product_id)
    cols, params = [], []
    for key, value in fields.items():
        if key == "is_active":
            value = 1 if value else 0
        cols.append(f"{key} = ?")
        params.append(value)
    params.append(product_id)
    cur = conn.execute(
        f"UPDATE products SET {', '.join(cols)} WHERE id = ?", params
    )
    if cur.rowcount == 0:
        return None
    return get_product(conn, product_id)


def create_order(
    conn: sqlite3.Connection,
    user_tg_id: int,
    user_name: str,
    items: List[Tuple[int, int]],
    note: str = "",
    method: str = "mock",
    user_lang: str = "",
) -> Tuple[int, int]:
    """Создать заказ. Сумма считается НА СЕРВЕРЕ по ценам из БД."""
    if not items:
        raise OrderError("Пустой заказ")
    aggregated: dict = {}
    for product_id, qty in items:
        if qty < 1:
            raise OrderError("Неверное количество")
        aggregated[product_id] = aggregated.get(product_id, 0) + qty

    total = 0
    resolved: List[Tuple[int, int, int]] = []
    for product_id, qty in aggregated.items():
        row = conn.execute(
            "SELECT price_kopecks, is_active FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if not row or not row["is_active"]:
            raise OrderError(f"Товар {product_id} недоступен")
        price = row["price_kopecks"]
        total += price * qty
        resolved.append((product_id, qty, price))

    cur = conn.execute(
        """INSERT INTO orders
               (user_tg_id, user_name, user_lang, status, total_kopecks, note, payment_method)
           VALUES (?, ?, ?, 'new', ?, ?, ?)""",
        (user_tg_id, user_name, user_lang, total, note, method),
    )
    order_id = cur.lastrowid
    conn.executemany(
        """INSERT INTO order_items
               (order_id, product_id, qty, price_at_purchase_kopecks)
           VALUES (?, ?, ?, ?)""",
        [(order_id, pid, qty, price) for pid, qty, price in resolved],
    )
    return order_id, total


def set_order_payment(
    conn: sqlite3.Connection, order_id: int, payment_id: str
) -> None:
    conn.execute(
        f"UPDATE orders SET payment_id = ?, updated_at = {_NOW} WHERE id = ?",
        (payment_id, order_id),
    )


def set_order_ton(
    conn: sqlite3.Connection, order_id: int, amount_nano: int, comment: str
) -> None:
    """Сохранить выставленную сумму (нано-TON / единицы жетона) и комментарий."""
    conn.execute(
        f"UPDATE orders SET pay_amount_nano = ?, pay_comment = ?, updated_at = {_NOW} WHERE id = ?",
        (amount_nano, comment, order_id),
    )


def get_order(conn: sqlite3.Connection, order_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    return dict(row) if row else None


def get_order_items(conn: sqlite3.Connection, order_id: int) -> List[dict]:
    rows = conn.execute(
        """SELECT oi.product_id, oi.qty, oi.price_at_purchase_kopecks, p.title
           FROM order_items oi
           JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = ?
           ORDER BY oi.id""",
        (order_id,),
    ).fetchall()
    return [
        {
            "product_id": r["product_id"],
            "title": r["title"],
            "qty": r["qty"],
            "price_at_purchase_kopecks": r["price_at_purchase_kopecks"],
        }
        for r in rows
    ]


def _order_to_dict(
    conn: sqlite3.Connection, row: sqlite3.Row, admin: bool = False
) -> dict:
    data = {
        "id": row["id"],
        "status": row["status"],
        "total_kopecks": row["total_kopecks"],
        "note": row["note"],
        "created_at": row["created_at"],
        "items": get_order_items(conn, row["id"]),
    }
    if admin:
        data.update(
            {
                "user_tg_id": row["user_tg_id"],
                "user_name": row["user_name"],
                "payment_id": row["payment_id"],
                "payment_method": row["payment_method"],
                "updated_at": row["updated_at"],
            }
        )
    return data


def list_orders_by_user(conn: sqlite3.Connection, user_tg_id: int) -> List[dict]:
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_tg_id = ? ORDER BY id DESC",
        (user_tg_id,),
    ).fetchall()
    return [_order_to_dict(conn, r) for r in rows]


def list_all_orders(conn: sqlite3.Connection) -> List[dict]:
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return [_order_to_dict(conn, r, admin=True) for r in rows]


def mark_order_paid_by_payment(
    conn: sqlite3.Connection, payment_id: str
) -> Optional[dict]:
    """Идемпотентно выставить 'paid'. Вернёт заказ ТОЛЬКО при первом переходе."""
    row = conn.execute(
        "SELECT * FROM orders WHERE payment_id = ?", (payment_id,)
    ).fetchone()
    if not row:
        return None
    if row["status"] != "new":
        return None
    conn.execute(
        f"UPDATE orders SET status = 'paid', updated_at = {_NOW} WHERE id = ?",
        (row["id"],),
    )
    result = dict(row)
    result["status"] = "paid"
    return result


def set_order_status(
    conn: sqlite3.Connection, order_id: int, status: str
) -> bool:
    cur = conn.execute(
        f"UPDATE orders SET status = ?, updated_at = {_NOW} WHERE id = ?",
        (status, order_id),
    )
    return cur.rowcount > 0


def stats(conn: sqlite3.Connection) -> dict:
    paid = ("paid", "shipped", "done")
    ph = ",".join("?" * len(paid))
    total_orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    paid_orders = conn.execute(
        f"SELECT COUNT(*) c FROM orders WHERE status IN ({ph})", paid
    ).fetchone()["c"]
    revenue = conn.execute(
        f"SELECT COALESCE(SUM(total_kopecks), 0) s FROM orders WHERE status IN ({ph})",
        paid,
    ).fetchone()["s"]
    top = conn.execute(
        f"""SELECT p.id, p.title,
                   SUM(oi.qty) qty,
                   SUM(oi.qty * oi.price_at_purchase_kopecks) revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.status IN ({ph})
            GROUP BY p.id
            ORDER BY qty DESC
            LIMIT 5""",
        paid,
    ).fetchall()
    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "revenue_kopecks": revenue,
        "top_products": [
            {
                "id": r["id"],
                "title": r["title"],
                "qty": r["qty"],
                "revenue_kopecks": r["revenue"],
            }
            for r in top
        ],
    }


# Категории
def list_categories(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
    return [r["name"] for r in rows]


def create_category(conn: sqlite3.Connection, name: str) -> str:
    conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    return name


def category_in_use(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM products WHERE category = ? LIMIT 1", (name,)
    ).fetchone()
    return row is not None


def delete_category(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("DELETE FROM categories WHERE name = ?", (name,))


def get_user_lang(conn: sqlite3.Connection, user_tg_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT lang FROM user_prefs WHERE user_tg_id = ?", (user_tg_id,)
    ).fetchone()
    if row and row["lang"] in ("ru", "en"):
        return row["lang"]
    return None


def set_user_lang(conn: sqlite3.Connection, user_tg_id: int, lang: str) -> None:
    conn.execute(
        "INSERT INTO user_prefs (user_tg_id, lang) VALUES (?, ?) "
        "ON CONFLICT(user_tg_id) DO UPDATE SET lang = excluded.lang",
        (user_tg_id, lang),
    )


def get_setting(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM app_settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def get_admin_lang(conn: sqlite3.Connection) -> Optional[str]:
    """Язык админских уведомлений из настроек (или None — тогда берём из .env)."""
    val = get_setting(conn, "admin_lang")
    return val if val in ("ru", "en") else None


def product_in_orders(conn: sqlite3.Connection, product_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM order_items WHERE product_id = ? LIMIT 1", (product_id,)
    ).fetchone()
    return row is not None


def delete_product(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
