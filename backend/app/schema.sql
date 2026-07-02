-- Схема БД интернет-магазина. Цены хранятся в КОПЕЙКАХ (INTEGER).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    description   TEXT    NOT NULL DEFAULT '',
    price_kopecks INTEGER NOT NULL CHECK (price_kopecks >= 0),
    photo_url     TEXT    NOT NULL DEFAULT '',
    category      TEXT    NOT NULL CHECK (
        category IN ('День рождения', 'Свадьба', 'Извинение', 'Без повода')
    ),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_tg_id     INTEGER NOT NULL,
    user_name      TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'new' CHECK (
        status IN ('new', 'paid', 'shipped', 'done', 'canceled')
    ),
    total_kopecks  INTEGER NOT NULL DEFAULT 0 CHECK (total_kopecks >= 0),
    -- UNIQUE и NULL-able: ключ идемпотентности оплаты (мок-платёж/будущий платёжный шлюз).
    payment_id     TEXT    UNIQUE,
    -- Способ оплаты: mock | crypto | card (или пусто).
    payment_method TEXT    NOT NULL DEFAULT '',
    note           TEXT    NOT NULL DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_orders_user   ON orders(user_tg_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

CREATE TABLE IF NOT EXISTS order_items (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id                  INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id                INTEGER NOT NULL REFERENCES products(id),
    qty                       INTEGER NOT NULL CHECK (qty > 0),
    price_at_purchase_kopecks INTEGER NOT NULL CHECK (price_at_purchase_kopecks >= 0)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
