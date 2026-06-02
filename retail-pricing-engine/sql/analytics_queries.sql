-- ============================================================
-- Retail Pricing & Markdown Decision Engine
-- Analytics Queries
-- ============================================================

-- ============================================================
-- 1. REVENUE & PROFIT ANALYTICS
-- ============================================================

-- 1.1 Overall Revenue Summary
SELECT 
    COUNT(DISTINCT transaction_id) AS total_orders,
    SUM(quantity_sold) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(revenue), 2) AS avg_order_value,
    ROUND(SUM(profit) / SUM(revenue) * 100, 2) AS overall_margin_pct
FROM transactions;

-- 1.2 Monthly Revenue & Profit Trend
SELECT 
    strftime('%Y-%m', transaction_date) AS month,
    ROUND(SUM(revenue), 2) AS monthly_revenue,
    ROUND(SUM(profit), 2) AS monthly_profit,
    SUM(quantity_sold) AS monthly_units,
    COUNT(DISTINCT transaction_id) AS monthly_orders
FROM transactions
GROUP BY strftime('%Y-%m', transaction_date)
ORDER BY month;

-- 1.3 Revenue by Category
SELECT 
    p.category,
    ROUND(SUM(t.revenue), 2) AS category_revenue,
    ROUND(SUM(t.profit), 2) AS category_profit,
    ROUND(SUM(t.revenue) * 100.0 / (SELECT SUM(revenue) FROM transactions), 2) AS revenue_share_pct
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- ============================================================
-- 2. PRODUCT PERFORMANCE
-- ============================================================

-- 2.1 Top 10 Best Selling Products (by Revenue)
SELECT 
    p.product_id,
    p.name,
    p.category,
    SUM(t.quantity_sold) AS total_units,
    ROUND(SUM(t.revenue), 2) AS total_revenue,
    ROUND(SUM(t.profit), 2) AS total_profit,
    ROUND(AVG(t.gross_margin), 2) AS avg_margin
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue DESC
LIMIT 10;

-- 2.2 Bottom 10 Worst Selling Products (by Revenue)
SELECT 
    p.product_id,
    p.name,
    p.category,
    SUM(t.quantity_sold) AS total_units,
    ROUND(SUM(t.revenue), 2) AS total_revenue,
    ROUND(SUM(t.profit), 2) AS total_profit,
    ROUND(AVG(t.gross_margin), 2) AS avg_margin
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue ASC
LIMIT 10;

-- ============================================================
-- 3. SELL-THROUGH RATE
-- ============================================================

-- 3.1 Sell-Through Rate per Product
-- STR = Units Sold / (Units Sold + Current Stock)
SELECT 
    p.product_id,
    p.name,
    p.category,
    COALESCE(s.total_sold, 0) AS total_units_sold,
    i.current_stock + i.warehouse_stock AS total_available,
    ROUND(
        CAST(COALESCE(s.total_sold, 0) AS REAL) / 
        (COALESCE(s.total_sold, 0) + i.current_stock + i.warehouse_stock) * 100, 
    2) AS sell_through_rate
FROM products p
JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN (
    SELECT product_id, SUM(quantity_sold) AS total_sold
    FROM transactions
    GROUP BY product_id
) s ON p.product_id = s.product_id
ORDER BY sell_through_rate ASC;

-- ============================================================
-- 4. INVENTORY TURNOVER
-- ============================================================

-- 4.1 Inventory Turnover by Product
-- Turnover = Total Sales / Average Inventory
SELECT 
    p.product_id,
    p.name,
    p.category,
    ROUND(SUM(t.revenue), 2) AS total_sales,
    i.current_stock + i.warehouse_stock AS avg_inventory_value,
    ROUND(
        SUM(t.revenue) / 
        NULLIF((i.current_stock + i.warehouse_stock) * p.cost, 0), 
    2) AS inventory_turnover
FROM transactions t
JOIN products p ON t.product_id = p.product_id
JOIN inventory i ON p.product_id = i.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY inventory_turnover DESC;

-- ============================================================
-- 5. DISCOUNT EFFECTIVENESS
-- ============================================================

-- 5.1 Discount Effectiveness Analysis
-- Revenue per % discount applied
SELECT 
    CASE 
        WHEN discount_pct = 0 THEN 'No Discount'
        WHEN discount_pct <= 10 THEN '1-10%'
        WHEN discount_pct <= 20 THEN '11-20%'
        WHEN discount_pct <= 30 THEN '21-30%'
        ELSE '31%+'
    END AS discount_band,
    COUNT(*) AS num_transactions,
    ROUND(AVG(quantity_sold), 2) AS avg_units_per_txn,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(gross_margin), 2) AS avg_margin_pct,
    ROUND(SUM(revenue) / NULLIF(AVG(discount_pct), 0), 2) AS revenue_per_pct_discount
FROM transactions
GROUP BY discount_band
ORDER BY discount_band;

-- 5.2 Promotion vs Non-Promotion Performance
SELECT 
    CASE WHEN is_promotion = 1 THEN 'Promotion' ELSE 'Regular' END AS sale_type,
    COUNT(*) AS num_transactions,
    SUM(quantity_sold) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(quantity_sold), 2) AS avg_units_per_txn,
    ROUND(AVG(discount_pct), 2) AS avg_discount
FROM transactions
GROUP BY is_promotion;

-- ============================================================
-- 6. TIME-BASED ANALYTICS
-- ============================================================

-- 6.1 Day-of-Week Performance
SELECT 
    day_of_week,
    CASE day_of_week
        WHEN 0 THEN 'Monday'
        WHEN 1 THEN 'Tuesday'
        WHEN 2 THEN 'Wednesday'
        WHEN 3 THEN 'Thursday'
        WHEN 4 THEN 'Friday'
        WHEN 5 THEN 'Saturday'
        WHEN 6 THEN 'Sunday'
    END AS day_name,
    COUNT(*) AS num_transactions,
    ROUND(AVG(revenue), 2) AS avg_revenue_per_txn,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM transactions
GROUP BY day_of_week
ORDER BY day_of_week;

-- 6.2 Quarterly Performance
SELECT 
    quarter,
    strftime('%Y', transaction_date) AS year,
    COUNT(*) AS num_transactions,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(discount_pct), 2) AS avg_discount
FROM transactions
GROUP BY year, quarter
ORDER BY year, quarter;

-- ============================================================
-- 7. PRICE ANALYSIS
-- ============================================================

-- 7.1 Price vs Quantity Correlation by Category
SELECT 
    p.category,
    ROUND(AVG(t.selling_price), 2) AS avg_price,
    ROUND(AVG(t.quantity_sold), 2) AS avg_quantity,
    ROUND(AVG(t.discount_pct), 2) AS avg_discount,
    COUNT(*) AS sample_size
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY avg_price DESC;

-- 7.2 Competitor Price Comparison
SELECT 
    p.product_id,
    p.name,
    p.category,
    p.base_price AS our_base_price,
    ROUND(AVG(t.selling_price), 2) AS our_avg_selling_price,
    ROUND(AVG(t.competitor_price), 2) AS avg_competitor_price,
    ROUND(
        (AVG(t.selling_price) - AVG(t.competitor_price)) / 
        AVG(t.competitor_price) * 100, 
    2) AS price_diff_pct
FROM transactions t
JOIN products p ON t.product_id = p.product_id
WHERE t.competitor_price IS NOT NULL
GROUP BY p.product_id, p.name, p.category, p.base_price
ORDER BY price_diff_pct DESC;

-- ============================================================
-- 8. PRODUCTS NEEDING MARKDOWN
-- ============================================================

-- 8.1 Products with High Inventory and Low Sell-Through
SELECT 
    p.product_id,
    p.name,
    p.category,
    p.base_price,
    i.current_stock + i.warehouse_stock AS total_stock,
    COALESCE(s.total_sold, 0) AS total_sold,
    ROUND(
        CAST(COALESCE(s.total_sold, 0) AS REAL) / 
        NULLIF(COALESCE(s.total_sold, 0) + i.current_stock + i.warehouse_stock, 0) * 100, 
    2) AS sell_through_rate,
    ROUND(COALESCE(s.avg_discount, 0), 2) AS current_avg_discount
FROM products p
JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN (
    SELECT 
        product_id, 
        SUM(quantity_sold) AS total_sold,
        AVG(discount_pct) AS avg_discount
    FROM transactions
    GROUP BY product_id
) s ON p.product_id = s.product_id
WHERE (i.current_stock + i.warehouse_stock) > 100  -- High inventory
ORDER BY sell_through_rate ASC
LIMIT 20;
