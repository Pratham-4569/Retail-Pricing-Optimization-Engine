"""
markdown_simulator.py — Markdown / Discount Simulation Engine
==============================================================

For every product, simulates a range of discount percentages and
computes the expected revenue, profit, and inventory clearance under
each scenario using estimated price elasticities.
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
# Simulation
# ────────────────────────────────────────────────────────────────────────────────

def simulate_product(
    product_id: str,
    product_name: str,
    category: str,
    base_price: float,
    cost: float,
    elasticity: float,
    current_demand: float,
    current_stock: int,
    discounts: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Simulate multiple markdown scenarios for a single product.

    Parameters
    ----------
    current_demand : float
        Average recent daily demand (units).
    current_stock : int
        Current inventory units.
    discounts : list[float]
        Discount fractions to evaluate (e.g. [0.0, 0.05, …, 0.50]).

    Returns
    -------
    list[dict]
        One dict per discount scenario.
    """
    discounts = discounts or cfg.SIMULATION_DISCOUNTS
    results: list[dict[str, Any]] = []

    for disc in discounts:
        new_price = round(base_price * (1 - disc), 2)
        margin = new_price - cost

        # Constant-elasticity demand model: Q_new = Q_base × (P_new/P_base)^ε
        # For ε < 0 (normal goods), lowering price increases demand
        price_ratio = 1.0 - disc
        if price_ratio > 0 and disc > 0:
            demand_multiplier = price_ratio ** elasticity
            expected_demand = max(0.0, current_demand * demand_multiplier)
        else:
            expected_demand = current_demand

        # Project over 30-day window
        monthly_demand = round(expected_demand * 30, 0)
        expected_revenue = round(new_price * monthly_demand, 2)
        expected_profit = round(margin * monthly_demand, 2)
        clearance = round(monthly_demand / current_stock, 4) if current_stock > 0 else 0.0

        results.append({
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "discount_pct": round(disc * 100, 1),
            "new_price": new_price,
            "cost": cost,
            "margin_per_unit": round(margin, 2),
            "expected_daily_demand": round(expected_demand, 1),
            "expected_monthly_demand": int(monthly_demand),
            "expected_revenue": expected_revenue,
            "expected_profit": expected_profit,
            "current_stock": current_stock,
            "inventory_clearance_pct": round(clearance * 100, 2),
        })

    return results


# ────────────────────────────────────────────────────────────────────────────────
# Bulk simulation
# ────────────────────────────────────────────────────────────────────────────────

def simulate_all(
    products: pd.DataFrame,
    inventory: pd.DataFrame,
    txn: pd.DataFrame,
    elasticity_df: pd.DataFrame,
) -> pd.DataFrame:
    """Run markdown simulation for every product.

    Parameters
    ----------
    products : pd.DataFrame
    inventory : pd.DataFrame
        Must have ``product_id`` and ``current_stock`` (summed across stores).
    txn : pd.DataFrame
        Cleaned transactions for computing recent demand.
    elasticity_df : pd.DataFrame
        Per-product or per-category elasticity with ``product_id`` or
        ``category`` and ``elasticity`` columns.

    Returns
    -------
    pd.DataFrame
        One row per (product, discount) scenario.
    """
    # Recent average daily demand per product (last 90 days)
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
    demand_agg["avg_daily_demand"] = (demand_agg["total_recent_qty"] / 90).round(2)

    # Sum inventory across stores
    inv_agg = (
        inventory.groupby("product_id")["current_stock"]
        .sum()
        .reset_index()
    )

    # Build elasticity lookup (prefer product-level, fallback to category)
    elas_lookup: dict[str, float] = {}
    if "product_id" in elasticity_df.columns:
        for _, row in elasticity_df.iterrows():
            elas_lookup[row["product_id"]] = row["elasticity"]

    # Category fallback
    cat_elas_lookup: dict[str, float] = {}
    if "category" in elasticity_df.columns:
        for _, row in elasticity_df.drop_duplicates("category").iterrows():
            cat_elas_lookup[row["category"]] = row["elasticity"]

    all_scenarios: list[dict[str, Any]] = []

    for _, prod in products.iterrows():
        pid = prod["product_id"]
        pname = prod["product_name"]
        cat = prod["category"]
        base_price = prod["base_price"]
        cost = prod["cost"]

        # Elasticity
        elasticity = elas_lookup.get(pid, cat_elas_lookup.get(cat, cfg.CATEGORIES.get(cat, {}).get("elasticity", -1.0)))

        # Current demand
        demand_row = demand_agg[demand_agg["product_id"] == pid]
        current_demand = float(demand_row["avg_daily_demand"].iloc[0]) if len(demand_row) else float(prod["base_demand"])

        # Current stock
        inv_row = inv_agg[inv_agg["product_id"] == pid]
        current_stock = int(inv_row["current_stock"].iloc[0]) if len(inv_row) else 0

        scenarios = simulate_product(
            product_id=pid,
            product_name=pname,
            category=cat,
            base_price=base_price,
            cost=cost,
            elasticity=elasticity,
            current_demand=current_demand,
            current_stock=current_stock,
        )
        all_scenarios.extend(scenarios)

    df = pd.DataFrame(all_scenarios)
    logger.info(
        "Markdown simulation complete: %d products × %d discounts = %d scenarios.",
        products.shape[0], len(cfg.SIMULATION_DISCOUNTS), len(df),
    )
    return df


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(
    datasets: dict[str, pd.DataFrame],
    elasticity_results: dict[str, Any],
) -> pd.DataFrame:
    """Execute full markdown simulation.

    Parameters
    ----------
    datasets : dict
        Must contain ``products``, ``inventory``, ``transactions``.
    elasticity_results : dict
        Output of ``price_elasticity.run()``.

    Returns
    -------
    pd.DataFrame  — all simulation scenarios.
    """
    products = datasets["products"]
    inventory = datasets["inventory"]
    txn = datasets["transactions"]

    # Prefer product-level elasticity; fall back to category
    elas_df = elasticity_results.get("product_elasticity", pd.DataFrame())
    if elas_df.empty:
        elas_df = elasticity_results.get("category_elasticity", pd.DataFrame())

    return simulate_all(products, inventory, txn, elas_df)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    proc = cfg.PROCESSED_DATA_DIR
    ds = {
        "transactions": pd.read_csv(proc / "transactions.csv"),
        "products": pd.read_csv(proc / "products.csv"),
        "inventory": pd.read_csv(proc / "inventory.csv"),
    }
    # Fake elasticity for smoke test
    from src.elasticity.price_elasticity import run as elas_run
    elas = elas_run(ds)
    result = run(ds, elas)
    print(result.head(20).to_string())
