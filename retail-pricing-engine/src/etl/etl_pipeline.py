"""
etl_pipeline.py — Extract, Transform, Load Pipeline
=====================================================

Reads raw CSVs, cleans / enriches the data, loads into SQLite,
and saves processed CSVs for downstream analytics.
"""

from __future__ import annotations

import logging
import sqlite3
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

# Indian public-holiday dates (major national holidays across 2023-2024)
_HOLIDAYS: set[str] = {
    # 2023
    "2023-01-26", "2023-03-08", "2023-03-22", "2023-03-30",
    "2023-04-07", "2023-04-14", "2023-04-22", "2023-05-05",
    "2023-06-29", "2023-08-15", "2023-08-30", "2023-09-07",
    "2023-09-28", "2023-10-02", "2023-10-24", "2023-11-01",
    "2023-11-12", "2023-11-27", "2023-12-25",
    # 2024
    "2024-01-26", "2024-03-25", "2024-03-29", "2024-04-11",
    "2024-04-14", "2024-04-17", "2024-04-21", "2024-06-17",
    "2024-07-17", "2024-08-15", "2024-08-26", "2024-09-16",
    "2024-10-02", "2024-10-12", "2024-10-31", "2024-11-01",
    "2024-11-15", "2024-12-25",
}


# ────────────────────────────────────────────────────────────────────────────────
# Extract
# ────────────────────────────────────────────────────────────────────────────────

def extract(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load every CSV from the raw data directory.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are the file stems (e.g. ``"transactions"``).
    """
    raw_dir = raw_dir or cfg.RAW_DATA_DIR
    datasets: dict[str, pd.DataFrame] = {}

    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    for fp in csv_files:
        df = pd.read_csv(fp)
        datasets[fp.stem] = df
        logger.info("Extracted %-15s → %s rows × %s cols", fp.name, f"{len(df):,}", df.shape[1])

    return datasets


# ────────────────────────────────────────────────────────────────────────────────
# Transform
# ────────────────────────────────────────────────────────────────────────────────

def _deduplicate(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Drop exact-duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        logger.warning("Removed %d duplicate rows from %s.", dropped, name)
    return df


def _fill_missing_prices(transactions: pd.DataFrame) -> pd.DataFrame:
    """Fill null selling prices with the per-product median."""
    if transactions["selling_price"].isna().any():
        median_prices = transactions.groupby("product_id")["selling_price"].transform("median")
        transactions["selling_price"] = transactions["selling_price"].fillna(median_prices)
        logger.info("Filled missing selling prices with per-product median.")
    return transactions


def _validate(transactions: pd.DataFrame) -> pd.DataFrame:
    """Enforce business rules: price > 0, quantity >= 0."""
    before = len(transactions)
    transactions = transactions[transactions["selling_price"] > 0]
    transactions = transactions[transactions["quantity"] >= 0]
    removed = before - len(transactions)
    if removed:
        logger.warning("Removed %d invalid rows (price ≤ 0 or qty < 0).", removed)
    return transactions.reset_index(drop=True)


def _add_computed_columns(txn: pd.DataFrame) -> pd.DataFrame:
    """Add revenue, profit, discount_pct (recomputed), gross_margin."""
    txn["revenue"] = (txn["selling_price"] * txn["quantity"]).round(2)
    txn["profit"] = ((txn["selling_price"] - txn["cost"]) * txn["quantity"]).round(2)
    txn["discount_pct"] = (
        ((txn["base_price"] - txn["selling_price"]) / txn["base_price"])
        .clip(lower=0)
        .round(4)
    )
    txn["gross_margin"] = np.where(
        txn["revenue"] > 0,
        ((txn["revenue"] - txn["cost"] * txn["quantity"]) / txn["revenue"]).round(4),
        0.0,
    )
    return txn


def _add_time_features(txn: pd.DataFrame) -> pd.DataFrame:
    """Derive calendar features from the ``date`` column."""
    txn["date"] = pd.to_datetime(txn["date"])
    txn["month"] = txn["date"].dt.month
    txn["quarter"] = txn["date"].dt.quarter
    txn["year"] = txn["date"].dt.year
    txn["day_of_week"] = txn["date"].dt.dayofweek
    txn["is_weekend"] = txn["day_of_week"].isin([5, 6]).astype(int)
    txn["is_holiday"] = txn["date"].dt.strftime("%Y-%m-%d").isin(_HOLIDAYS).astype(int)
    return txn


def transform(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Full transform pipeline on all datasets."""
    logger.info("Starting transform …")

    for name in datasets:
        datasets[name] = _deduplicate(datasets[name], name)

    txn = datasets["transactions"]
    txn = _fill_missing_prices(txn)
    txn = _validate(txn)
    txn = _add_computed_columns(txn)
    txn = _add_time_features(txn)
    datasets["transactions"] = txn

    # Ensure date columns are datetime
    if "promotions" in datasets and "date" in datasets["promotions"].columns:
        datasets["promotions"]["date"] = pd.to_datetime(datasets["promotions"]["date"])

    logger.info("Transform complete. Transactions: %s rows.", f"{len(txn):,}")
    return datasets


# ────────────────────────────────────────────────────────────────────────────────
# Load → SQLite
# ────────────────────────────────────────────────────────────────────────────────

_INDEXES: dict[str, list[str]] = {
    "transactions": [
        "CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date)",
        "CREATE INDEX IF NOT EXISTS idx_txn_product ON transactions(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_txn_store ON transactions(store_id)",
        "CREATE INDEX IF NOT EXISTS idx_txn_prod_date ON transactions(product_id, date)",
    ],
    "products": [
        "CREATE INDEX IF NOT EXISTS idx_prod_category ON products(category)",
    ],
    "promotions": [
        "CREATE INDEX IF NOT EXISTS idx_promo_product ON promotions(product_id)",
    ],
    "inventory": [
        "CREATE INDEX IF NOT EXISTS idx_inv_product ON inventory(product_id)",
    ],
}


def load_to_sqlite(
    datasets: dict[str, pd.DataFrame],
    db_path: Path | None = None,
) -> None:
    """Write all DataFrames into an SQLite database, creating indexes."""
    db_path = db_path or cfg.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data into SQLite → %s", db_path)
    conn = sqlite3.connect(str(db_path))

    try:
        for name, df in datasets.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
            logger.info("  %-15s → %s rows written.", name, f"{len(df):,}")

            for ddl in _INDEXES.get(name, []):
                conn.execute(ddl)

        conn.commit()
        logger.info("SQLite load complete.")
    finally:
        conn.close()


def save_processed_csvs(
    datasets: dict[str, pd.DataFrame],
    processed_dir: Path | None = None,
) -> None:
    """Persist cleaned datasets as CSVs."""
    processed_dir = processed_dir or cfg.PROCESSED_DATA_DIR
    processed_dir.mkdir(parents=True, exist_ok=True)

    for name, df in datasets.items():
        fp = processed_dir / f"{name}.csv"
        df.to_csv(fp, index=False)
        logger.info("Saved processed %s → %s", name, fp)


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(
    raw_dir: Path | None = None,
    db_path: Path | None = None,
    processed_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Execute the full ETL pipeline: Extract → Transform → Load.

    Returns the cleaned datasets dictionary.
    """
    datasets = extract(raw_dir)
    datasets = transform(datasets)
    load_to_sqlite(datasets, db_path)
    save_processed_csvs(datasets, processed_dir)
    return datasets


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    run()
