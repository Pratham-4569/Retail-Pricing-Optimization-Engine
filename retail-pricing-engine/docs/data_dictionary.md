# Data Dictionary
## Retail Pricing & Markdown Decision Engine

---

## 1. Products Table (`products`)

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `product_id` | TEXT | Unique product identifier | "PROD-001" | PRIMARY KEY |
| `name` | TEXT | Product display name | "Basmati Rice 5kg" | NOT NULL |
| `category` | TEXT | Product category | "Grocery" | NOT NULL |
| `subcategory` | TEXT | Product subcategory | "Staples" | Optional |
| `base_price` | REAL | Maximum retail price (MRP) in ₹ | 450.00 | > 0 |
| `cost` | REAL | Cost of goods sold per unit in ₹ | 270.00 | > 0 |
| `supplier` | TEXT | Supplier name | "India Agro Ltd" | Optional |
| `created_at` | TEXT | Record creation timestamp | "2024-01-01 00:00:00" | Auto |

### Categories & Price Ranges

| Category | Products | Base Price Range (₹) | Cost Margin |
|----------|----------|---------------------|-------------|
| Grocery | 10 items | ₹50 – ₹1,500 | 30-40% |
| Electronics | 8 items | ₹500 – ₹50,000 | 60-70% |
| Clothing | 8 items | ₹500 – ₹8,000 | 35-50% |
| Beauty | 8 items | ₹200 – ₹5,000 | 40-55% |
| Home & Kitchen | 8 items | ₹300 – ₹15,000 | 40-55% |
| Sports | 8 items | ₹500 – ₹10,000 | 45-55% |

---

## 2. Stores Table (`stores`)

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `store_id` | TEXT | Unique store identifier | "STORE-MUM" | PRIMARY KEY |
| `name` | TEXT | Store display name | "RetailIQ Mumbai Central" | NOT NULL |
| `city` | TEXT | City location | "Mumbai" | NOT NULL |
| `region` | TEXT | Geographic region | "West" | NOT NULL |
| `store_type` | TEXT | Type of store | "Hypermarket" | DEFAULT 'Retail' |
| `created_at` | TEXT | Record creation timestamp | "2024-01-01 00:00:00" | Auto |

### Store Locations

| Store ID | City | Region | Type |
|----------|------|--------|------|
| STORE-MUM | Mumbai | West | Hypermarket |
| STORE-DEL | Delhi | North | Supermarket |
| STORE-BLR | Bangalore | South | Hypermarket |
| STORE-CHN | Chennai | South | Supermarket |
| STORE-KOL | Kolkata | East | Retail |

---

## 3. Transactions Table (`transactions`)

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `transaction_id` | INTEGER | Auto-increment transaction ID | 1 | PRIMARY KEY |
| `transaction_date` | TEXT | Transaction date (ISO 8601) | "2024-03-15" | NOT NULL |
| `product_id` | TEXT | Reference to products table | "PROD-001" | FOREIGN KEY |
| `store_id` | TEXT | Reference to stores table | "STORE-MUM" | FOREIGN KEY |
| `quantity_sold` | INTEGER | Number of units sold | 5 | >= 0 |
| `selling_price` | REAL | Actual selling price per unit (₹) | 405.00 | > 0 |
| `base_price` | REAL | Original MRP per unit (₹) | 450.00 | > 0 |
| `cost` | REAL | Cost per unit (₹) | 270.00 | > 0 |
| `discount_pct` | REAL | Discount percentage applied | 10.0 | 0-100 |
| `revenue` | REAL | selling_price × quantity_sold (₹) | 2025.00 | COMPUTED |
| `profit` | REAL | (selling_price - cost) × quantity_sold (₹) | 675.00 | COMPUTED |
| `gross_margin` | REAL | ((selling_price - cost) / selling_price) × 100 | 33.33 | COMPUTED |
| `is_promotion` | INTEGER | Whether a promotion was active | 1 | 0 or 1 |
| `is_holiday` | INTEGER | Whether the date was a holiday | 0 | 0 or 1 |
| `is_weekend` | INTEGER | Whether the date was Sat/Sun | 1 | 0 or 1 |
| `day_of_week` | INTEGER | Day of week (0=Mon, 6=Sun) | 5 | 0-6 |
| `month` | INTEGER | Month number | 3 | 1-12 |
| `quarter` | INTEGER | Quarter number | 1 | 1-4 |
| `competitor_price` | REAL | Estimated competitor price (₹) | 430.00 | Optional |

### Computed Fields
- **Revenue** = `selling_price × quantity_sold`
- **Profit** = `(selling_price - cost) × quantity_sold`
- **Gross Margin %** = `((selling_price - cost) / selling_price) × 100`

---

## 4. Inventory Table (`inventory`)

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `inventory_id` | INTEGER | Auto-increment ID | 1 | PRIMARY KEY |
| `product_id` | TEXT | Reference to products table | "PROD-001" | FOREIGN KEY |
| `store_id` | TEXT | Reference to stores table | "STORE-MUM" | FOREIGN KEY |
| `current_stock` | INTEGER | Units in store | 150 | >= 0 |
| `warehouse_stock` | INTEGER | Units in warehouse | 500 | >= 0 |
| `reorder_level` | INTEGER | Minimum stock before reorder | 50 | DEFAULT 50 |
| `last_updated` | TEXT | Last stock update timestamp | "2024-12-31" | Auto |

---

## 5. Promotions Table (`promotions`)

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `promo_id` | INTEGER | Auto-increment promotion ID | 1 | PRIMARY KEY |
| `product_id` | TEXT | Reference to products table | "PROD-001" | FOREIGN KEY |
| `campaign_type` | TEXT | Type of promotion | "Diwali Sale" | NOT NULL |
| `discount_pct` | REAL | Discount percentage | 20.0 | 0-100 |
| `start_date` | TEXT | Promotion start date | "2024-10-15" | NOT NULL |
| `end_date` | TEXT | Promotion end date | "2024-11-15" | NOT NULL |
| `description` | TEXT | Promotion description | "Festival special offer" | Optional |

### Campaign Types

| Campaign | Typical Discount | Duration | Frequency |
|----------|-----------------|----------|-----------|
| Diwali Sale | 15-30% | 2-4 weeks | Annual (Oct-Nov) |
| Republic Day Sale | 10-20% | 1 week | Annual (Jan) |
| Summer Clearance | 20-40% | 2-3 weeks | Annual (May-Jun) |
| Weekend Special | 5-15% | 2 days | Weekly |
| Flash Sale | 15-25% | 1 day | Monthly |
| End of Season | 30-50% | 2-4 weeks | Biannual |

---

## 6. Output Data Structures

### 6.1 KPI Summary (`overview_kpis.json`)
```json
{
    "total_revenue": 12345678.90,
    "total_profit": 4567890.12,
    "total_orders": 98765,
    "avg_order_value": 1234.56,
    "overall_margin_pct": 37.0,
    "total_units_sold": 234567,
    "total_products": 50,
    "total_stores": 5
}
```

### 6.2 Recommendation (`recommendations.json`)
```json
[
    {
        "product_id": "PROD-001",
        "product_name": "Basmati Rice 5kg",
        "category": "Grocery",
        "current_price": 450.00,
        "recommended_discount_pct": 10.0,
        "recommended_price": 405.00,
        "expected_revenue": 520000.00,
        "expected_profit": 190000.00,
        "inventory_clearance_pct": 82.0,
        "current_stock": 700
    }
]
```

---

## 7. Key Business Metrics Definitions

| Metric | Formula | Unit |
|--------|---------|------|
| **Revenue** | Selling Price × Quantity Sold | ₹ |
| **Profit** | (Selling Price - Cost) × Quantity Sold | ₹ |
| **Gross Margin** | (Revenue - Cost) / Revenue × 100 | % |
| **Sell-Through Rate** | Units Sold / (Units Sold + Remaining Stock) × 100 | % |
| **Inventory Turnover** | Total Sales Value / (Avg Inventory × Cost) | Ratio |
| **Discount Effectiveness** | Revenue Generated / Discount % Applied | ₹/% |
| **Price Elasticity** | % Change in Demand / % Change in Price | Coefficient |
| **MAPE** | Mean Absolute Percentage Error of forecasts | % |
