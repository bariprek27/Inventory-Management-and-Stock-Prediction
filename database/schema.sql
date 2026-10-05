-- ============================================================
--  StockWise Database Schema
--  Database: stockwise
-- ============================================================

CREATE DATABASE IF NOT EXISTS stockwise
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE stockwise;

-- USERS
CREATE TABLE IF NOT EXISTS users (
    user_id       INT            AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)   NOT NULL,
    username      VARCHAR(50)    NOT NULL UNIQUE,
    password_hash VARCHAR(255)   NOT NULL,
    role          ENUM('admin','staff') NOT NULL DEFAULT 'staff',
    created_at    DATETIME       DEFAULT CURRENT_TIMESTAMP
);

-- CATEGORIES
CREATE TABLE IF NOT EXISTS categories (
    category_id   INT            AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100)   NOT NULL UNIQUE,
    description   TEXT
);

-- SUPPLIERS
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT            AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150)   NOT NULL,
    phone         VARCHAR(20),
    email         VARCHAR(100),
    address       TEXT,
    lead_time     INT            NOT NULL DEFAULT 7
);

-- PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    product_id     INT             AUTO_INCREMENT PRIMARY KEY,
    product_name   VARCHAR(200)    NOT NULL,
    category_id    INT             NOT NULL,
    supplier_id    INT             NOT NULL,
    purchase_price DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    selling_price  DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    current_stock  INT             NOT NULL DEFAULT 0,
    reorder_level  INT             NOT NULL DEFAULT 10,
    safety_stock   INT             NOT NULL DEFAULT 5,
    created_at     DATETIME        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prod_cat  FOREIGN KEY (category_id)  REFERENCES categories(category_id),
    CONSTRAINT fk_prod_supp FOREIGN KEY (supplier_id)  REFERENCES suppliers(supplier_id)
);

-- PURCHASES (header)
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id   INT             AUTO_INCREMENT PRIMARY KEY,
    supplier_id   INT             NOT NULL,
    purchase_date DATE            NOT NULL,
    total_amount  DECIMAL(14,2)   NOT NULL DEFAULT 0.00,
    notes         TEXT,
    created_at    DATETIME        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pur_supp FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- PURCHASE ITEMS (lines)
CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id INT            AUTO_INCREMENT PRIMARY KEY,
    purchase_id      INT            NOT NULL,
    product_id       INT            NOT NULL,
    quantity         INT            NOT NULL CHECK (quantity > 0),
    unit_price       DECIMAL(12,2)  NOT NULL,
    CONSTRAINT fk_pi_pur  FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id),
    CONSTRAINT fk_pi_prod FOREIGN KEY (product_id)  REFERENCES products(product_id)
);

-- SALES (header)
CREATE TABLE IF NOT EXISTS sales (
    sale_id      INT             AUTO_INCREMENT PRIMARY KEY,
    user_id      INT             NOT NULL,
    sale_date    DATE            NOT NULL,
    total_amount DECIMAL(14,2)   NOT NULL DEFAULT 0.00,
    created_at   DATETIME        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sale_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- SALE ITEMS (lines)
CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT            AUTO_INCREMENT PRIMARY KEY,
    sale_id      INT            NOT NULL,
    product_id   INT            NOT NULL,
    quantity     INT            NOT NULL CHECK (quantity > 0),
    unit_price   DECIMAL(12,2)  NOT NULL,
    CONSTRAINT fk_si_sale FOREIGN KEY (sale_id)    REFERENCES sales(sale_id),
    CONSTRAINT fk_si_prod FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- INVENTORY TRANSACTIONS
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id   INT         AUTO_INCREMENT PRIMARY KEY,
    product_id       INT         NOT NULL,
    transaction_type ENUM('PURCHASE','SALE','ADJUSTMENT') NOT NULL,
    quantity         INT         NOT NULL,
    transaction_date DATE        NOT NULL,
    reference_id     INT,
    notes            TEXT,
    created_at       DATETIME    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_it_prod FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- FORECASTS
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id      INT             AUTO_INCREMENT PRIMARY KEY,
    product_id       INT             NOT NULL,
    forecast_date    DATE            NOT NULL,
    predicted_demand DECIMAL(10,2)   NOT NULL,
    model_used       VARCHAR(50)     NOT NULL,
    created_at       DATETIME        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fc_prod FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- VIEWS
CREATE OR REPLACE VIEW v_inventory_overview AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    s.supplier_name,
    p.current_stock,
    p.reorder_level,
    p.safety_stock,
    p.purchase_price,
    p.selling_price,
    (p.current_stock * p.purchase_price) AS stock_value,
    CASE
        WHEN p.current_stock = 0                            THEN 'Out of Stock'
        WHEN p.current_stock <= p.reorder_level             THEN 'Low Stock'
        WHEN p.current_stock >= (p.reorder_level * 3)       THEN 'Overstock'
        ELSE 'Healthy'
    END AS stock_status,
    s.lead_time
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN suppliers  s ON p.supplier_id  = s.supplier_id;

CREATE OR REPLACE VIEW v_daily_sales AS
SELECT
    s.sale_date,
    COUNT(DISTINCT s.sale_id)          AS total_orders,
    SUM(si.quantity)                   AS total_units,
    SUM(si.quantity * si.unit_price)   AS total_revenue
FROM sales s
JOIN sale_items si ON s.sale_id = si.sale_id
GROUP BY s.sale_date;

CREATE OR REPLACE VIEW v_product_sales_summary AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    SUM(si.quantity)                 AS total_sold,
    SUM(si.quantity * si.unit_price) AS total_revenue,
    MIN(s.sale_date)                 AS first_sale,
    MAX(s.sale_date)                 AS last_sale
FROM sale_items si
JOIN sales    s ON si.sale_id    = s.sale_id
JOIN products p ON si.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
GROUP BY p.product_id, p.product_name, c.category_name;
