-- ============================================================
-- Retail Pricing & Markdown Decision Engine
-- Database Schema (SQLite)
-- ============================================================

-- Products Master Table
CREATE TABLE IF NOT EXISTS products (
    product_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    subcategory     TEXT,
    base_price      REAL NOT NULL CHECK(base_price > 0),
    cost            REAL NOT NULL CHECK(cost > 0),
    supplier        TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Stores Master Table
CREATE TABLE IF NOT EXISTS stores (
    store_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    city            TEXT NOT NULL,
    region          TEXT NOT NULL,
    store_type      TEXT DEFAULT 'Retail',
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Sales Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    product_id      TEXT NOT NULL,
    store_id        TEXT NOT NULL,
    quantity_sold   INTEGER NOT NULL CHECK(quantity_sold >= 0),
    selling_price   REAL NOT NULL CHECK(selling_price > 0),
    base_price      REAL NOT NULL CHECK(base_price > 0),
    cost            REAL NOT NULL CHECK(cost > 0),
    discount_pct    REAL DEFAULT 0 CHECK(discount_pct >= 0 AND discount_pct <= 100),
    revenue         REAL GENERATED ALWAYS AS (selling_price * quantity_sold) STORED,
    profit          REAL GENERATED ALWAYS AS ((selling_price - cost) * quantity_sold) STORED,
    gross_margin    REAL GENERATED ALWAYS AS (
        CASE WHEN selling_price > 0 
        THEN ((selling_price - cost) / selling_price) * 100 
        ELSE 0 END
    ) STORED,
    is_promotion    INTEGER DEFAULT 0 CHECK(is_promotion IN (0, 1)),
    is_holiday      INTEGER DEFAULT 0 CHECK(is_holiday IN (0, 1)),
    is_weekend      INTEGER DEFAULT 0 CHECK(is_weekend IN (0, 1)),
    day_of_week     INTEGER,
    month           INTEGER,
    quarter         INTEGER,
    competitor_price REAL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      TEXT NOT NULL,
    store_id        TEXT NOT NULL,
    current_stock   INTEGER NOT NULL CHECK(current_stock >= 0),
    warehouse_stock INTEGER DEFAULT 0 CHECK(warehouse_stock >= 0),
    reorder_level   INTEGER DEFAULT 50,
    last_updated    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Promotions Table
CREATE TABLE IF NOT EXISTS promotions (
    promo_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      TEXT NOT NULL,
    campaign_type   TEXT NOT NULL,
    discount_pct    REAL NOT NULL CHECK(discount_pct > 0 AND discount_pct <= 100),
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    description     TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ============================================================
-- Indexes for Query Performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_trans_date 
    ON transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_trans_product 
    ON transactions(product_id);

CREATE INDEX IF NOT EXISTS idx_trans_store 
    ON transactions(store_id);

CREATE INDEX IF NOT EXISTS idx_trans_date_product 
    ON transactions(transaction_date, product_id);

CREATE INDEX IF NOT EXISTS idx_trans_category 
    ON transactions(product_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_inventory_product 
    ON inventory(product_id);

CREATE INDEX IF NOT EXISTS idx_inventory_store 
    ON inventory(store_id);

CREATE INDEX IF NOT EXISTS idx_promo_product 
    ON promotions(product_id);

CREATE INDEX IF NOT EXISTS idx_promo_dates 
    ON promotions(start_date, end_date);

-- ============================================================
-- Views for Common Analytics
-- ============================================================

-- Product Performance Summary View
CREATE VIEW IF NOT EXISTS v_product_performance AS
SELECT 
    p.product_id,
    p.name AS product_name,
    p.category,
    p.base_price,
    p.cost,
    COUNT(t.transaction_id) AS total_transactions,
    SUM(t.quantity_sold) AS total_units_sold,
    ROUND(SUM(t.revenue), 2) AS total_revenue,
    ROUND(SUM(t.profit), 2) AS total_profit,
    ROUND(AVG(t.selling_price), 2) AS avg_selling_price,
    ROUND(AVG(t.discount_pct), 2) AS avg_discount,
    ROUND(AVG(t.gross_margin), 2) AS avg_margin_pct
FROM products p
LEFT JOIN transactions t ON p.product_id = t.product_id
GROUP BY p.product_id, p.name, p.category, p.base_price, p.cost;

-- Category Performance Summary View
CREATE VIEW IF NOT EXISTS v_category_performance AS
SELECT 
    p.category,
    COUNT(DISTINCT p.product_id) AS product_count,
    COUNT(t.transaction_id) AS total_transactions,
    SUM(t.quantity_sold) AS total_units_sold,
    ROUND(SUM(t.revenue), 2) AS total_revenue,
    ROUND(SUM(t.profit), 2) AS total_profit,
    ROUND(AVG(t.discount_pct), 2) AS avg_discount,
    ROUND(AVG(t.gross_margin), 2) AS avg_margin_pct
FROM products p
LEFT JOIN transactions t ON p.product_id = t.product_id
GROUP BY p.category;

-- Monthly Trends View
CREATE VIEW IF NOT EXISTS v_monthly_trends AS
SELECT 
    strftime('%Y-%m', transaction_date) AS month,
    COUNT(transaction_id) AS total_orders,
    SUM(quantity_sold) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(discount_pct), 2) AS avg_discount,
    ROUND(AVG(gross_margin), 2) AS avg_margin
FROM transactions
GROUP BY strftime('%Y-%m', transaction_date)
ORDER BY month;

-- Inventory Status View
CREATE VIEW IF NOT EXISTS v_inventory_status AS
SELECT 
    p.product_id,
    p.name AS product_name,
    p.category,
    i.current_stock,
    i.warehouse_stock,
    (i.current_stock + i.warehouse_stock) AS total_stock,
    COALESCE(sold.total_sold, 0) AS total_sold,
    CASE 
        WHEN (i.current_stock + i.warehouse_stock) > 0 
        THEN ROUND(CAST(COALESCE(sold.total_sold, 0) AS REAL) / 
             (i.current_stock + i.warehouse_stock + COALESCE(sold.total_sold, 0)) * 100, 2)
        ELSE 0 
    END AS sell_through_rate
FROM products p
JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN (
    SELECT product_id, SUM(quantity_sold) AS total_sold
    FROM transactions
    GROUP BY product_id
) sold ON p.product_id = sold.product_id;
