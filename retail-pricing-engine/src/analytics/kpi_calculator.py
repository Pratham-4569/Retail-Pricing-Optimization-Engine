"""
kpi_calculator.py — Business KPI Calculator
=============================================

Computes all key performance indicators from cleaned transaction and
inventory data.

All monetary values are in Indian Rupees (₹).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import sys
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config as cfg

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────────
# Overview KPIs
# ────────────────────────────────────────────────────────────────────────────────

def compute_overview_kpis(txn: pd.DataFrame) -> dict[str, Any]:
    """Return high-level business metrics.

    Keys
    ----
    total_revenue, total_profit, total_orders, total_quantity,
    avg_order_value, avg_selling_price, avg_discount_pct,
    overall_gross_margin
    """
    total_revenue = round(txn["revenue"].sum(), 2)
    total_profit = round(txn["profit"].sum(), 2)
    total_orders = len(txn)
    total_quantity = int(txn["quantity"].sum())
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0.0
    avg_selling_price = round(txn["selling_price"].mean(), 2)
    avg_discount_pct = round(txn["discount_pct"].mean() * 100, 2)
    overall_gross_margin = round(
        (total_revenue - (txn["cost"] * txn["quantity"]).sum()) / total_revenue * 100, 2
    ) if total_revenue else 0.0

    kpis = {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "avg_order_value": avg_order_value,
        "avg_selling_price": avg_selling_price,
        "avg_discount_pct": avg_discount_pct,
        "overall_gross_margin": overall_gross_margin,
        "currency": cfg.CURRENCY_SYMBOL,
    }
    logger.info(
        "Overview KPIs — Revenue: %s%.2f | Profit: %s%.2f | Orders: %s",
        cfg.CURRENCY_SYMBOL, total_revenue,
        cfg.CURRENCY_SYMBOL, total_profit,
        f"{total_orders:,}",
    )
    return kpis


# ────────────────────────────────────────────────────────────────────────────────
# Product-level metrics
# ────────────────────────────────────────────────────────────────────────────────

def compute_product_kpis(
    txn: pd.DataFrame,
    products: pd.DataFrame,
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Per-product KPIs including sell-through and inventory turnover.

    Returns
    -------
    pd.DataFrame with one row per product.
    """
    product_agg = (
        txn.groupby("product_id")
        .agg(
            total_revenue=("revenue", "sum"),
            total_profit=("profit", "sum"),
            total_quantity=("quantity", "sum"),
            total_orders=("transaction_id", "count"),
            avg_selling_price=("selling_price", "mean"),
            avg_discount_pct=("discount_pct", "mean"),
        )
        .reset_index()
    )

    # Merge product metadata
    product_agg = product_agg.merge(
        products[["product_id", "product_name", "category", "base_price", "cost"]],
        on="product_id",
        how="left",
    )

    # Inventory metrics (aggregate across stores)
    inv_agg = (
        inventory.groupby("product_id")
        .agg(
            total_initial_stock=("initial_stock", "sum"),
            total_current_stock=("current_stock", "sum"),
            total_sold_inv=("total_sold", "sum"),
        )
        .reset_index()
    )
    product_agg = product_agg.merge(inv_agg, on="product_id", how="left")

    # Sell-through rate = total_sold / initial_stock × 100
    product_agg["sell_through_rate"] = np.where(
        product_agg["total_initial_stock"] > 0,
        (product_agg["total_sold_inv"] / product_agg["total_initial_stock"] * 100).round(2),
        0.0,
    )

    # Inventory turnover = total_sold / avg_stock  (approx avg = (initial+current)/2)
    avg_stock = (product_agg["total_initial_stock"] + product_agg["total_current_stock"]) / 2
    product_agg["inventory_turnover"] = np.where(
        avg_stock > 0,
        (product_agg["total_sold_inv"] / avg_stock).round(2),
        0.0,
    )

    # Gross margin %
    product_agg["gross_margin_pct"] = np.where(
        product_agg["total_revenue"] > 0,
        ((product_agg["total_profit"] / product_agg["total_revenue"]) * 100).round(2),
        0.0,
    )

    product_agg["avg_discount_pct"] = (product_agg["avg_discount_pct"] * 100).round(2)

    logger.info("Computed KPIs for %d products.", len(product_agg))
    return product_agg


# ────────────────────────────────────────────────────────────────────────────────
# Category-level breakdowns
# ────────────────────────────────────────────────────────────────────────────────

def compute_category_kpis(txn: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Aggregate KPIs by product category."""
    txn_cat = txn.merge(products[["product_id", "category"]], on="product_id", how="left")

    cat_agg = (
        txn_cat.groupby("category")
        .agg(
            total_revenue=("revenue", "sum"),
            total_profit=("profit", "sum"),
            total_quantity=("quantity", "sum"),
            total_orders=("transaction_id", "count"),
            avg_selling_price=("selling_price", "mean"),
            avg_discount_pct=("discount_pct", "mean"),
        )
        .reset_index()
    )

    cat_agg["gross_margin_pct"] = np.where(
        cat_agg["total_revenue"] > 0,
        ((cat_agg["total_profit"] / cat_agg["total_revenue"]) * 100).round(2),
        0.0,
    )
    cat_agg["avg_discount_pct"] = (cat_agg["avg_discount_pct"] * 100).round(2)

    logger.info("Category KPIs computed for %d categories.", len(cat_agg))
    return cat_agg


# ────────────────────────────────────────────────────────────────────────────────
# Discount effectiveness
# ────────────────────────────────────────────────────────────────────────────────

def compute_discount_effectiveness(txn: pd.DataFrame) -> dict[str, Any]:
    """Compare revenue for promoted vs. non-promoted transactions."""
    promo = txn[txn["is_promotion"] == 1]
    no_promo = txn[txn["is_promotion"] == 0]

    promo_revenue = round(promo["revenue"].sum(), 2)
    no_promo_revenue = round(no_promo["revenue"].sum(), 2)
    avg_promo_discount = round(promo["discount_pct"].mean() * 100, 2) if len(promo) else 0.0
    revenue_per_discount_pct = (
        round(promo_revenue / (promo["discount_pct"].mean() * 100), 2)
        if len(promo) and promo["discount_pct"].mean() > 0
        else 0.0
    )

    result = {
        "promo_orders": len(promo),
        "non_promo_orders": len(no_promo),
        "promo_revenue": promo_revenue,
        "non_promo_revenue": no_promo_revenue,
        "avg_promo_discount_pct": avg_promo_discount,
        "revenue_per_discount_pct": revenue_per_discount_pct,
    }
    logger.info("Discount effectiveness — Promo revenue: %s%.2f", cfg.CURRENCY_SYMBOL, promo_revenue)
    return result


# ────────────────────────────────────────────────────────────────────────────────
# Monthly time series
# ────────────────────────────────────────────────────────────────────────────────

def compute_monthly_trends(txn: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue and profit time series."""
    txn["date"] = pd.to_datetime(txn["date"])
    monthly = (
        txn.groupby(txn["date"].dt.to_period("M"))
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            quantity=("quantity", "sum"),
            orders=("transaction_id", "count"),
        )
        .reset_index()
    )
    monthly["date"] = monthly["date"].astype(str)
    monthly = monthly.round(2)
    logger.info("Monthly trends: %d months.", len(monthly))
    return monthly


# ────────────────────────────────────────────────────────────────────────────────
# Top / Bottom sellers
# ────────────────────────────────────────────────────────────────────────────────

def compute_top_bottom_sellers(
    product_kpis: pd.DataFrame, n: int = 10
) -> dict[str, pd.DataFrame]:
    """Return top-*n* and bottom-*n* products by total revenue."""
    sorted_df = product_kpis.sort_values("total_revenue", ascending=False)

    top = sorted_df.head(n)[
        ["product_id", "product_name", "category", "total_revenue", "total_quantity"]
    ].reset_index(drop=True)

    bottom = sorted_df.tail(n)[
        ["product_id", "product_name", "category", "total_revenue", "total_quantity"]
    ].reset_index(drop=True)

    logger.info("Top %d sellers: %s … | Bottom %d: %s …",
                n, top["product_name"].iloc[0], n, bottom["product_name"].iloc[0])
    return {"top_sellers": top, "bottom_sellers": bottom}


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Compute all KPIs and return a consolidated results dictionary.

    Expected keys in *datasets*: ``transactions``, ``products``, ``inventory``.
    """
    txn = datasets["transactions"].copy()
    products = datasets["products"]
    inventory = datasets["inventory"]

    overview = compute_overview_kpis(txn)
    product_kpis = compute_product_kpis(txn, products, inventory)
    category_kpis = compute_category_kpis(txn, products)
    discount_eff = compute_discount_effectiveness(txn)
    monthly_trends = compute_monthly_trends(txn)
    top_bottom = compute_top_bottom_sellers(product_kpis)

    results: dict[str, Any] = {
        "overview": overview,
        "product_kpis": product_kpis,
        "category_kpis": category_kpis,
        "discount_effectiveness": discount_eff,
        "monthly_trends": monthly_trends,
        "top_sellers": top_bottom["top_sellers"],
        "bottom_sellers": top_bottom["bottom_sellers"],
    }
    logger.info("All KPIs computed successfully.")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    # Quick smoke test: load processed data and compute
    proc = cfg.PROCESSED_DATA_DIR
    ds = {
        "transactions": pd.read_csv(proc / "transactions.csv"),
        "products": pd.read_csv(proc / "products.csv"),
        "inventory": pd.read_csv(proc / "inventory.csv"),
    }
    run(ds)
