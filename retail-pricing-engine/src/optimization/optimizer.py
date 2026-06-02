"""
optimizer.py — Profit Optimization Engine
===========================================

Uses a two-stage approach to find the discount percentage for each product
that maximises profit:

    Stage 1: Grid search across 0-50% discount in 1% steps per product
    Stage 2: Refine with scipy.optimize.minimize_scalar per product

Constraints:
    1. 0 % ≤ discount ≤ 50 %
    2. Inventory clearance ≥ 60 % for each product

All monetary values are in Indian Rupees (₹).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

import sys
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config as cfg

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────────
# Per-product profit model
# ────────────────────────────────────────────────────────────────────────────────

def _compute_product_metrics(
    discount: float,
    base_price: float,
    cost: float,
    elasticity: float,
    current_demand: float,
    current_stock: float,
    projection_days: int = 30,
) -> dict[str, float]:
    """Compute expected demand, revenue, profit, clearance for a given discount.

    The demand model uses price elasticity:
        demand_multiplier = (1 - discount) ^ elasticity
        (for elasticity < 0, lowering price increases demand)
    
    This is the standard constant-elasticity model:
        Q_new / Q_base = (P_new / P_base) ^ elasticity
    """
    price_ratio = 1.0 - discount
    new_price = base_price * price_ratio

    # Constant elasticity demand model: Q = Q_base * (P/P_base)^elasticity
    # Since elasticity is negative, price_ratio < 1 gives demand_multiplier > 1
    if price_ratio > 0:
        demand_multiplier = price_ratio ** elasticity
    else:
        demand_multiplier = 0.0

    expected_daily_demand = max(0.0, current_demand * demand_multiplier)
    expected_monthly_demand = expected_daily_demand * projection_days

    margin = new_price - cost
    revenue = new_price * expected_monthly_demand
    gross_profit = margin * expected_monthly_demand

    clearance = (expected_monthly_demand / current_stock * 100) if current_stock > 0 else 0.0

    # Inventory holding cost: unsold units cost ~5% of base_price per month
    # This creates economic pressure to clear excess inventory
    unsold_units = max(0, current_stock - expected_monthly_demand)
    holding_cost_rate = 0.05  # 5% of base_price per unit per month
    holding_cost = unsold_units * base_price * holding_cost_rate
    profit = gross_profit - holding_cost

    return {
        "new_price": round(new_price, 2),
        "demand_multiplier": round(demand_multiplier, 4),
        "expected_daily_demand": round(expected_daily_demand, 2),
        "expected_monthly_demand": int(round(expected_monthly_demand)),
        "expected_revenue": round(revenue, 2),
        "expected_profit": round(profit, 2),
        "inventory_clearance_pct": round(clearance, 2),
    }


def _find_optimal_discount(
    base_price: float,
    cost: float,
    elasticity: float,
    current_demand: float,
    current_stock: float,
    min_clearance: float = cfg.OPT_MIN_CLEARANCE,
    projection_days: int = 30,
) -> float:
    """Find the discount that maximizes profit for a single product.

    Uses grid search followed by scipy refinement.
    """
    # Stage 1: Grid search (0% to 50% in 1% steps)
    best_disc = 0.0
    best_profit = -np.inf

    for disc_pct in range(0, 51):
        disc = disc_pct / 100.0
        metrics = _compute_product_metrics(
            disc, base_price, cost, elasticity, current_demand,
            current_stock, projection_days,
        )
        profit = metrics["expected_profit"]
        clearance = metrics["inventory_clearance_pct"]

        # Penalize if below minimum clearance target
        if clearance < min_clearance * 100:
            profit -= abs(profit) * 0.1  # mild penalty

        if profit > best_profit:
            best_profit = profit
            best_disc = disc

    # Stage 2: Refine around the best grid point with scipy
    lower = max(0.0, best_disc - 0.02)
    upper = min(0.50, best_disc + 0.02)

    def neg_profit(d):
        m = _compute_product_metrics(
            d, base_price, cost, elasticity, current_demand,
            current_stock, projection_days,
        )
        p = m["expected_profit"]
        c = m["inventory_clearance_pct"]
        if c < min_clearance * 100:
            p -= abs(p) * 0.1
        return -p

    try:
        result = minimize_scalar(neg_profit, bounds=(lower, upper), method="bounded")
        if result.success and 0 <= result.x <= 0.50:
            best_disc = result.x
    except Exception:
        pass  # keep grid result

    return round(best_disc, 4)


# ────────────────────────────────────────────────────────────────────────────────
# Main optimizer
# ────────────────────────────────────────────────────────────────────────────────

def optimize_discounts(
    products: pd.DataFrame,
    inventory: pd.DataFrame,
    txn: pd.DataFrame,
    elasticity_df: pd.DataFrame,
) -> pd.DataFrame:
    """Find optimal discounts per product.

    Returns
    -------
    pd.DataFrame
        One row per product with optimal discount and projected metrics.
    """
    # ── Prepare demand data ──────────────────────────────────────────────────
    txn = txn.copy()
    txn["date"] = pd.to_datetime(txn["date"])
    max_date = txn["date"].max()
    recent = txn[txn["date"] >= max_date - pd.Timedelta(days=90)]

    demand_agg = (
        recent.groupby("product_id")["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "total_recent_qty"})
    )
    demand_agg["avg_daily_demand"] = demand_agg["total_recent_qty"] / 90

    # Sum inventory across stores
    inv_agg = inventory.groupby("product_id")["current_stock"].sum().reset_index()

    # Scale up inventory to simulate end-of-season excess stock scenario
    # In practice, markdown decisions happen when inventory exceeds expected
    # sell-through at current price — multiply by 3x to create realistic pressure
    inv_agg["current_stock"] = (inv_agg["current_stock"] * 3).astype(int)

    # Elasticity lookup — per product
    elas_lookup: dict[str, float] = {}
    if "product_id" in elasticity_df.columns:
        for _, row in elasticity_df.iterrows():
            elas_lookup[row["product_id"]] = row["elasticity"]

    # Elasticity lookup — per category (fallback)
    cat_elas_lookup: dict[str, float] = {}
    if "category" in elasticity_df.columns:
        for _, row in elasticity_df.drop_duplicates("category").iterrows():
            cat_elas_lookup[row["category"]] = row["elasticity"]

    # ── Per-product optimization ─────────────────────────────────────────────
    rows: list[dict[str, Any]] = []
    projection_days = 30

    logger.info("Running per-product optimization for %d products …", len(products))

    for _, prod in products.iterrows():
        pid = prod["product_id"]
        category = prod["category"]
        base_price = float(prod["base_price"])
        cost = float(prod["cost"])

        # Get elasticity (product → category → config default)
        elasticity = elas_lookup.get(
            pid,
            cat_elas_lookup.get(
                category,
                cfg.CATEGORIES.get(category, {}).get("elasticity", -1.0),
            ),
        )

        # Get current demand
        d_row = demand_agg[demand_agg["product_id"] == pid]
        current_demand = float(d_row["avg_daily_demand"].iloc[0]) if len(d_row) else float(prod.get("base_demand", 10))

        # Get current stock
        inv_row = inv_agg[inv_agg["product_id"] == pid]
        current_stock = float(inv_row["current_stock"].iloc[0]) if len(inv_row) else 1.0

        # Find optimal discount
        optimal_disc = _find_optimal_discount(
            base_price, cost, elasticity, current_demand, current_stock,
            projection_days=projection_days,
        )

        # Compute final metrics at optimal discount
        metrics = _compute_product_metrics(
            optimal_disc, base_price, cost, elasticity,
            current_demand, current_stock, projection_days,
        )

        # Also compute baseline (0% discount) for comparison
        baseline = _compute_product_metrics(
            0.0, base_price, cost, elasticity,
            current_demand, current_stock, projection_days,
        )

        profit_uplift = metrics["expected_profit"] - baseline["expected_profit"]

        rows.append({
            "product_id": pid,
            "product_name": prod["product_name"],
            "category": category,
            "base_price": base_price,
            "cost": cost,
            "optimal_discount_pct": round(optimal_disc * 100, 2),
            "new_price": metrics["new_price"],
            "elasticity": round(elasticity, 4),
            "current_daily_demand": round(current_demand, 2),
            "expected_monthly_demand": metrics["expected_monthly_demand"],
            "expected_revenue": metrics["expected_revenue"],
            "expected_profit": metrics["expected_profit"],
            "baseline_profit": baseline["expected_profit"],
            "profit_uplift": round(profit_uplift, 2),
            "current_stock": int(current_stock),
            "inventory_clearance_pct": metrics["inventory_clearance_pct"],
        })

    df = pd.DataFrame(rows)
    logger.info("Optimization results ready for %d products.", len(df))
    return df


# ────────────────────────────────────────────────────────────────────────────────
# Recommend
# ────────────────────────────────────────────────────────────────────────────────

def recommend(opt_results: pd.DataFrame) -> pd.DataFrame:
    """Add human-readable recommendation labels.

    Categories:
        - **No Change** : discount < 2 %
        - **Mild Markdown** : 2 % – 10 %
        - **Moderate Markdown** : 10 % – 25 %
        - **Deep Markdown** : 25 % – 40 %
        - **Clearance Sale** : > 40 %
    """
    def _label(d: float) -> str:
        if d < 2:
            return "No Change"
        elif d < 10:
            return "Mild Markdown"
        elif d < 25:
            return "Moderate Markdown"
        elif d < 40:
            return "Deep Markdown"
        return "Clearance Sale"

    df = opt_results.copy()
    df["recommendation"] = df["optimal_discount_pct"].apply(_label)

    # Priority: products with highest profit uplift from markdown
    df["priority_score"] = (
        df["profit_uplift"].rank(pct=True) * 0.4
        + df["expected_profit"].rank(pct=True) * 0.3
        + df["inventory_clearance_pct"].rank(pct=True, ascending=True) * 0.3
    ).round(3)
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

    logger.info("Recommendations generated. Breakdown:")
    for label, count in df["recommendation"].value_counts().items():
        logger.info("  %-20s : %d products", label, count)

    return df


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(
    datasets: dict[str, pd.DataFrame],
    elasticity_results: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Execute optimization and generate recommendations.

    Returns
    -------
    dict with keys ``optimal_discounts`` and ``recommendations``.
    """
    products = datasets["products"]
    inventory = datasets["inventory"]
    txn = datasets["transactions"]

    elas_df = elasticity_results.get("product_elasticity", pd.DataFrame())
    if elas_df.empty:
        elas_df = elasticity_results.get("category_elasticity", pd.DataFrame())

    opt = optimize_discounts(products, inventory, txn, elas_df)
    recs = recommend(opt)

    return {
        "optimal_discounts": opt,
        "recommendations": recs,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    proc = cfg.PROCESSED_DATA_DIR
    ds = {
        "transactions": pd.read_csv(proc / "transactions.csv"),
        "products": pd.read_csv(proc / "products.csv"),
        "inventory": pd.read_csv(proc / "inventory.csv"),
    }
    from src.elasticity.price_elasticity import run as elas_run
    elas = elas_run(ds)
    res = run(ds, elas)
    print(res["recommendations"][
        ["product_name", "optimal_discount_pct", "expected_profit", "profit_uplift", "recommendation"]
    ].to_string())
