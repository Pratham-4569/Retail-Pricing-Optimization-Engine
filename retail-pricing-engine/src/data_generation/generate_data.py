"""
generate_data.py — Synthetic Retail Data Generator
====================================================

Generates realistic retail transaction data for the Indian market.

Outputs (saved to data/raw/):
    - products.csv   : 50 products across 6 categories
    - stores.csv     : 5 stores in major Indian cities
    - transactions.csv : daily transactions over 2 years
    - inventory.csv  : stock snapshots per product × store
    - promotions.csv : discount events
"""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Resolve project root so we can import config regardless of cwd
import sys
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config as cfg

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def _short_id(prefix: str, index: int) -> str:
    """Return a zero-padded ID like P001, S002, etc."""
    return f"{prefix}{index:03d}"


# ────────────────────────────────────────────────────────────────────────────────
# Product catalogue
# ────────────────────────────────────────────────────────────────────────────────

def generate_products(rng: np.random.RandomState) -> pd.DataFrame:
    """Create a catalogue of *NUM_PRODUCTS* products across all categories.

    Each product receives a deterministic base price, cost, and base daily
    demand drawn from its category's configured ranges.
    """
    rows: list[dict[str, Any]] = []
    pid = 1

    for cat_name, cat_cfg in cfg.CATEGORIES.items():
        for product_name in cat_cfg["products"]:
            lo, hi = cat_cfg["price_range"]
            base_price = round(rng.uniform(lo, hi), 2)

            cost_lo, cost_hi = cat_cfg["cost_factor"]
            cost = round(base_price * rng.uniform(cost_lo, cost_hi), 2)

            demand_lo, demand_hi = cat_cfg["base_demand"]
            base_demand = int(rng.uniform(demand_lo, demand_hi))

            rows.append(
                {
                    "product_id": _short_id("P", pid),
                    "product_name": product_name,
                    "category": cat_name,
                    "base_price": base_price,
                    "cost": cost,
                    "base_demand": base_demand,
                    "elasticity": cat_cfg["elasticity"],
                }
            )
            pid += 1

    df = pd.DataFrame(rows)
    logger.info("Generated %d products across %d categories.", len(df), df["category"].nunique())
    return df


# ────────────────────────────────────────────────────────────────────────────────
# Stores
# ────────────────────────────────────────────────────────────────────────────────

def generate_stores() -> pd.DataFrame:
    """Return the pre-defined store list from config."""
    df = pd.DataFrame(cfg.STORES)
    logger.info("Generated %d stores.", len(df))
    return df


# ────────────────────────────────────────────────────────────────────────────────
# Transactions + promotions + competitor prices
# ────────────────────────────────────────────────────────────────────────────────

def generate_transactions(
    products: pd.DataFrame,
    stores: pd.DataFrame,
    rng: np.random.RandomState,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate daily transactions for every (product, store, date) triple.

    Demand model
    ------------
    ``quantity = base_demand × seasonality × dow_effect × price_sensitivity
                 × random_noise``

    Returns
    -------
    transactions : pd.DataFrame
    promotions   : pd.DataFrame
    """
    dates = pd.date_range(cfg.START_DATE, cfg.END_DATE, freq="D")
    logger.info("Generating transactions for %d days × %d products × %d stores …",
                len(dates), len(products), len(stores))

    txn_rows: list[dict[str, Any]] = []
    promo_rows: list[dict[str, Any]] = []
    txn_id = 1

    for _, prod in products.iterrows():
        product_id = prod["product_id"]
        base_price = prod["base_price"]
        cost = prod["cost"]
        base_demand = prod["base_demand"]
        elasticity = prod["elasticity"]

        for _, store in stores.iterrows():
            store_id = store["store_id"]

            for dt in dates:
                # ── seasonality ──
                month = dt.month
                seasonality = cfg.SEASONALITY.get(month, 1.0)

                # ── day-of-week ──
                dow = dt.dayofweek
                dow_effect = cfg.DAY_OF_WEEK_EFFECT.get(dow, 1.0)

                # ── promotion? ──
                is_promo = rng.random() < cfg.PROMOTION_PROBABILITY
                discount_pct = 0.0
                if is_promo:
                    discount_pct = round(
                        rng.uniform(*cfg.PROMOTION_DISCOUNT_RANGE), 2
                    )

                selling_price = round(base_price * (1 - discount_pct), 2)

                # ── price sensitivity ──
                price_ratio = selling_price / base_price
                price_sensitivity = price_ratio ** elasticity  # demand multiplier

                # ── random noise ──
                noise = max(0.3, rng.normal(1.0, 0.15))

                quantity = max(
                    0,
                    int(base_demand * seasonality * dow_effect * price_sensitivity * noise),
                )

                # ── competitor price ──
                comp_factor = rng.uniform(*cfg.COMPETITOR_PRICE_FACTOR)
                competitor_price = round(base_price * comp_factor, 2)

                revenue = round(selling_price * quantity, 2)
                profit = round((selling_price - cost) * quantity, 2)

                txn_rows.append(
                    {
                        "transaction_id": f"TXN{txn_id:08d}",
                        "date": dt.strftime("%Y-%m-%d"),
                        "product_id": product_id,
                        "store_id": store_id,
                        "quantity": quantity,
                        "selling_price": selling_price,
                        "base_price": base_price,
                        "cost": cost,
                        "competitor_price": competitor_price,
                        "is_promotion": int(is_promo),
                        "discount_pct": discount_pct,
                        "revenue": revenue,
                        "profit": profit,
                    }
                )

                if is_promo:
                    promo_rows.append(
                        {
                            "promo_id": f"PRM{len(promo_rows) + 1:07d}",
                            "transaction_id": f"TXN{txn_id:08d}",
                            "product_id": product_id,
                            "store_id": store_id,
                            "date": dt.strftime("%Y-%m-%d"),
                            "discount_pct": discount_pct,
                            "promo_type": rng.choice(
                                ["Clearance", "Festival", "Flash Sale", "Seasonal"]
                            ),
                        }
                    )

                txn_id += 1

    transactions = pd.DataFrame(txn_rows)
    promotions = pd.DataFrame(promo_rows)
    logger.info(
        "Generated %s transactions and %s promotions.",
        f"{len(transactions):,}",
        f"{len(promotions):,}",
    )
    return transactions, promotions


# ────────────────────────────────────────────────────────────────────────────────
# Inventory snapshots
# ────────────────────────────────────────────────────────────────────────────────

def generate_inventory(
    products: pd.DataFrame,
    stores: pd.DataFrame,
    transactions: pd.DataFrame,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """Compute current inventory per (product, store).

    Logic
    -----
    ``current_stock = initial_stock − total_sold + replenishment``

    Replenishment is a random multiplier of total sold to ensure stock
    doesn't drop below zero unrealistically.
    """
    rows: list[dict[str, Any]] = []

    sold_agg = (
        transactions.groupby(["product_id", "store_id"])["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "total_sold"})
    )

    for _, prod in products.iterrows():
        for _, store in stores.iterrows():
            pid = prod["product_id"]
            sid = store["store_id"]

            initial_stock = int(prod["base_demand"] * rng.uniform(60, 120))

            match = sold_agg[
                (sold_agg["product_id"] == pid) & (sold_agg["store_id"] == sid)
            ]
            total_sold = int(match["total_sold"].iloc[0]) if len(match) else 0

            replenishment = int(total_sold * rng.uniform(0.85, 1.05))
            current_stock = max(0, initial_stock - total_sold + replenishment)

            rows.append(
                {
                    "product_id": pid,
                    "store_id": sid,
                    "initial_stock": initial_stock,
                    "total_sold": total_sold,
                    "replenishment": replenishment,
                    "current_stock": current_stock,
                }
            )

    df = pd.DataFrame(rows)
    logger.info("Generated inventory for %d product-store pairs.", len(df))
    return df


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(output_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Generate all datasets and persist to CSV.

    Parameters
    ----------
    output_dir : Path, optional
        Override the default ``cfg.RAW_DATA_DIR``.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys: ``products``, ``stores``, ``transactions``,
        ``promotions``, ``inventory``.
    """
    rng = np.random.RandomState(cfg.RANDOM_SEED)
    out = output_dir or cfg.RAW_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    products = generate_products(rng)
    stores = generate_stores()
    transactions, promotions = generate_transactions(products, stores, rng)
    inventory = generate_inventory(products, stores, transactions, rng)

    datasets = {
        "products": products,
        "stores": stores,
        "transactions": transactions,
        "promotions": promotions,
        "inventory": inventory,
    }

    for name, df in datasets.items():
        filepath = out / f"{name}.csv"
        df.to_csv(filepath, index=False)
        logger.info("Saved %s → %s (%s rows)", name, filepath, f"{len(df):,}")

    return datasets


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    run()
