# Database Schema Documentation
## Retail Pricing & Markdown Decision Engine

---

## Entity-Relationship Diagram

```
┌─────────────────────┐          ┌──────────────────────┐
│     PRODUCTS         │          │      STORES           │
│─────────────────────│          │──────────────────────│
│ product_id (PK)     │          │ store_id (PK)        │
│ name                │          │ name                 │
│ category            │          │ city                 │
│ subcategory         │          │ region               │
│ base_price          │          │ store_type           │
│ cost                │          │ created_at           │
│ supplier            │          └──────────┬───────────┘
│ created_at          │                     │
└──────────┬──────────┘                     │
           │                                │
           │          ┌─────────────────────┴──────────────┐
           │          │         TRANSACTIONS                │
           ├──────────┤─────────────────────────────────────│
           │          │ transaction_id (PK)                 │
           │          │ transaction_date                    │
           │          │ product_id (FK) ──── products       │
           │          │ store_id (FK) ────── stores         │
           │          │ quantity_sold                       │
           │          │ selling_price                       │
           │          │ base_price                          │
           │          │ cost                                │
           │          │ discount_pct                        │
           │          │ revenue (COMPUTED)                  │
           │          │ profit (COMPUTED)                   │
           │          │ gross_margin (COMPUTED)             │
           │          │ is_promotion                        │
           │          │ is_holiday                          │
           │          │ is_weekend                          │
           │          │ day_of_week                         │
           │          │ month                               │
           │          │ quarter                             │
           │          │ competitor_price                    │
           │          └────────────────────────────────────┘
           │
           ├──────────┐
           │          │         INVENTORY
           │          │─────────────────────────────────────│
           │          │ inventory_id (PK)                   │
           │          │ product_id (FK) ──── products       │
           │          │ store_id (FK) ────── stores         │
           │          │ current_stock                       │
           │          │ warehouse_stock                     │
           │          │ reorder_level                       │
           │          │ last_updated                        │
           │          └────────────────────────────────────┘
           │
           └──────────┐
                      │         PROMOTIONS
                      │─────────────────────────────────────│
                      │ promo_id (PK)                       │
                      │ product_id (FK) ──── products       │
                      │ campaign_type                       │
                      │ discount_pct                        │
                      │ start_date                          │
                      │ end_date                            │
                      │ description                         │
                      └────────────────────────────────────┘
```

## Relationships

| Parent | Child | Relationship | Cardinality |
|--------|-------|-------------|-------------|
| Products | Transactions | product_id | 1 : Many |
| Products | Inventory | product_id | 1 : Many |
| Products | Promotions | product_id | 1 : Many |
| Stores | Transactions | store_id | 1 : Many |
| Stores | Inventory | store_id | 1 : Many |

## Indexes

| Index Name | Table | Column(s) | Purpose |
|-----------|-------|-----------|---------|
| `idx_trans_date` | transactions | transaction_date | Date range queries |
| `idx_trans_product` | transactions | product_id | Product-level analytics |
| `idx_trans_store` | transactions | store_id | Store-level analytics |
| `idx_trans_date_product` | transactions | transaction_date, product_id | Time-series by product |
| `idx_inventory_product` | inventory | product_id | Inventory lookups |
| `idx_promo_product` | promotions | product_id | Promotion lookups |
| `idx_promo_dates` | promotions | start_date, end_date | Active promotions query |

## Views

| View Name | Description |
|-----------|-------------|
| `v_product_performance` | Aggregated product metrics (revenue, profit, margin) |
| `v_category_performance` | Category-level performance summary |
| `v_monthly_trends` | Monthly revenue, profit, and order trends |
| `v_inventory_status` | Current inventory with sell-through rates |

## Data Volume Estimates

| Table | Expected Rows | Avg Row Size | Total Size |
|-------|--------------|-------------|------------|
| Products | 50 | ~200 bytes | ~10 KB |
| Stores | 5 | ~150 bytes | ~1 KB |
| Transactions | ~100,000+ | ~300 bytes | ~30 MB |
| Inventory | 250 (50 × 5) | ~100 bytes | ~25 KB |
| Promotions | ~200 | ~150 bytes | ~30 KB |
| **Total** | | | **~30 MB** |
