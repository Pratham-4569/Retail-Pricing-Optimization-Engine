"""
price_elasticity.py — Price Elasticity Analysis
=================================================

Estimates price elasticity of demand using log-log OLS regression:

    ln(quantity) = β₀ + β₁ · ln(price) [+ controls]

Provides per-category, per-product, and multi-feature elasticity models.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

import sys
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config as cfg

logger = logging.getLogger(__name__)

# Minimum rows to attempt regression
_MIN_ROWS = 30


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def _classify_elasticity(e: float) -> str:
    """Classify the elasticity coefficient."""
    abs_e = abs(e)
    if abs_e < 0.8:
        return "inelastic"
    elif abs_e > 1.2:
        return "elastic"
    return "unit_elastic"


def _safe_log(series: pd.Series) -> pd.Series:
    """Natural log, replacing zeros / negatives with NaN."""
    return np.log(series.where(series > 0))


# ────────────────────────────────────────────────────────────────────────────────
# Per-category elasticity (simple log-log)
# ────────────────────────────────────────────────────────────────────────────────

def estimate_category_elasticity(
    txn: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Log-log regression per category: ln(qty) ~ ln(price).

    Returns
    -------
    pd.DataFrame
        Columns: ``category``, ``elasticity``, ``intercept``, ``r2``,
        ``n_obs``, ``classification``.
    """
    txn_cat = txn.merge(products[["product_id", "category"]], on="product_id", how="left")

    rows: list[dict[str, Any]] = []
    for cat in sorted(txn_cat["category"].unique()):
        subset = txn_cat[txn_cat["category"] == cat].copy()
        subset = subset[subset["quantity"] > 0]
        subset["ln_qty"] = _safe_log(subset["quantity"])
        subset["ln_price"] = _safe_log(subset["selling_price"])
        subset = subset.dropna(subset=["ln_qty", "ln_price"])

        if len(subset) < _MIN_ROWS:
            logger.warning("  %s — too few observations (%d), skipping.", cat, len(subset))
            continue

        X = subset[["ln_price"]].values
        y = subset["ln_qty"].values

        model = LinearRegression().fit(X, y)
        y_pred = model.predict(X)
        r2 = round(r2_score(y, y_pred), 4)
        elasticity = round(float(model.coef_[0]), 4)

        rows.append({
            "category": cat,
            "elasticity": elasticity,
            "intercept": round(float(model.intercept_), 4),
            "r2": r2,
            "n_obs": len(subset),
            "classification": _classify_elasticity(elasticity),
        })
        logger.info("  %s → ε = %.3f (%s), R² = %.3f",
                     cat, elasticity, _classify_elasticity(elasticity), r2)

    return pd.DataFrame(rows)


# ────────────────────────────────────────────────────────────────────────────────
# Per-product elasticity
# ────────────────────────────────────────────────────────────────────────────────

def estimate_product_elasticity(
    txn: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Log-log regression per product.

    Returns
    -------
    pd.DataFrame
        Same schema as category elasticity, plus ``product_id`` and
        ``product_name``.
    """
    txn_prod = txn.merge(
        products[["product_id", "product_name", "category"]],
        on="product_id",
        how="left",
    )

    rows: list[dict[str, Any]] = []
    for pid in sorted(txn_prod["product_id"].unique()):
        subset = txn_prod[txn_prod["product_id"] == pid].copy()
        pname = subset["product_name"].iloc[0]
        cat = subset["category"].iloc[0]

        subset = subset[subset["quantity"] > 0]
        subset["ln_qty"] = _safe_log(subset["quantity"])
        subset["ln_price"] = _safe_log(subset["selling_price"])
        subset = subset.dropna(subset=["ln_qty", "ln_price"])

        if len(subset) < _MIN_ROWS:
            continue

        X = subset[["ln_price"]].values
        y = subset["ln_qty"].values

        model = LinearRegression().fit(X, y)
        y_pred = model.predict(X)
        r2 = round(r2_score(y, y_pred), 4)
        elasticity = round(float(model.coef_[0]), 4)

        rows.append({
            "product_id": pid,
            "product_name": pname,
            "category": cat,
            "elasticity": elasticity,
            "intercept": round(float(model.intercept_), 4),
            "r2": r2,
            "n_obs": len(subset),
            "classification": _classify_elasticity(elasticity),
        })

    logger.info("Per-product elasticity estimated for %d / %d products.",
                len(rows), txn_prod["product_id"].nunique())
    return pd.DataFrame(rows)


# ────────────────────────────────────────────────────────────────────────────────
# Multi-feature elasticity model
# ────────────────────────────────────────────────────────────────────────────────

def estimate_multifeature_elasticity(
    txn: pd.DataFrame,
    products: pd.DataFrame,
) -> dict[str, Any]:
    """Multi-feature log-log model across all products:

    ``ln(qty) = β₀ + β₁·ln(price) + β₂·is_promotion + β₃·month + β₄·ln(competitor_price)``

    Returns
    -------
    dict
        ``coefficients`` dict, ``r2``, ``n_obs``, ``feature_names``.
    """
    txn_all = txn.merge(products[["product_id", "category"]], on="product_id", how="left")
    txn_all = txn_all[txn_all["quantity"] > 0].copy()

    txn_all["ln_qty"] = _safe_log(txn_all["quantity"])
    txn_all["ln_price"] = _safe_log(txn_all["selling_price"])
    txn_all["ln_comp_price"] = _safe_log(txn_all["competitor_price"])

    # Ensure month exists
    if "month" not in txn_all.columns:
        txn_all["date"] = pd.to_datetime(txn_all["date"])
        txn_all["month"] = txn_all["date"].dt.month

    features = ["ln_price", "is_promotion", "month", "ln_comp_price"]
    txn_all = txn_all.dropna(subset=["ln_qty"] + features)

    if len(txn_all) < _MIN_ROWS:
        logger.warning("Multi-feature model: insufficient data (%d rows).", len(txn_all))
        return {"coefficients": {}, "r2": 0.0, "n_obs": 0, "feature_names": features}

    X = txn_all[features].values
    y = txn_all["ln_qty"].values

    model = LinearRegression().fit(X, y)
    y_pred = model.predict(X)
    r2 = round(r2_score(y, y_pred), 4)

    coefficients = {feat: round(float(c), 4) for feat, c in zip(features, model.coef_)}
    coefficients["intercept"] = round(float(model.intercept_), 4)

    logger.info(
        "Multi-feature model — price_elasticity=%.3f, R²=%.3f, n=%d",
        coefficients.get("ln_price", 0), r2, len(txn_all),
    )
    return {
        "coefficients": coefficients,
        "r2": r2,
        "n_obs": len(txn_all),
        "feature_names": features,
    }


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Run all elasticity analyses.

    When regression R² is low (< 0.2), the estimated elasticity is replaced
    with the domain-knowledge elasticity from ``config.CATEGORIES``.  This
    ensures the downstream optimiser has realistic demand-response curves.

    Returns
    -------
    dict with keys:
        ``category_elasticity`` (pd.DataFrame),
        ``product_elasticity``  (pd.DataFrame),
        ``multifeature_model``  (dict).
    """
    txn = datasets["transactions"]
    products = datasets["products"]

    logger.info("── Price Elasticity Analysis ──")
    cat_elas = estimate_category_elasticity(txn, products)
    prod_elas = estimate_product_elasticity(txn, products)
    multi = estimate_multifeature_elasticity(txn, products)

    # ── Augment with config elasticities when regression is weak ───────────
    R2_THRESHOLD = 0.20

    # Category-level: override poor estimates with config values
    config_cat_elas = {cat: info.get("elasticity", -1.0)
                       for cat, info in cfg.CATEGORIES.items()}

    if not cat_elas.empty:
        for idx, row in cat_elas.iterrows():
            cat = row["category"]
            if row["r2"] < R2_THRESHOLD and cat in config_cat_elas:
                old_e = row["elasticity"]
                new_e = config_cat_elas[cat]
                cat_elas.at[idx, "elasticity"] = new_e
                cat_elas.at[idx, "classification"] = _classify_elasticity(new_e)
                logger.info("  %s → R²=%.3f too low; using config elasticity %.2f (was %.3f)",
                           cat, row["r2"], new_e, old_e)

    # Also add any categories that weren't in the regression results
    existing_cats = set(cat_elas["category"]) if not cat_elas.empty else set()
    for cat, elast in config_cat_elas.items():
        if cat not in existing_cats:
            new_row = pd.DataFrame([{
                "category": cat,
                "elasticity": elast,
                "intercept": 0.0,
                "r2": 0.0,
                "n_obs": 0,
                "classification": _classify_elasticity(elast),
            }])
            cat_elas = pd.concat([cat_elas, new_row], ignore_index=True)

    # Product-level: override poor estimates with category-level values
    cat_elas_lookup = dict(zip(cat_elas["category"], cat_elas["elasticity"]))

    if not prod_elas.empty:
        for idx, row in prod_elas.iterrows():
            if row["r2"] < R2_THRESHOLD and row["category"] in cat_elas_lookup:
                old_e = row["elasticity"]
                new_e = cat_elas_lookup[row["category"]]
                prod_elas.at[idx, "elasticity"] = new_e
                prod_elas.at[idx, "classification"] = _classify_elasticity(new_e)

    logger.info("Elasticity augmentation complete. Categories with config overrides: %d",
               sum(1 for _, r in cat_elas.iterrows() if r["r2"] < R2_THRESHOLD))

    return {
        "category_elasticity": cat_elas,
        "product_elasticity": prod_elas,
        "multifeature_model": multi,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    proc = cfg.PROCESSED_DATA_DIR
    ds = {
        "transactions": pd.read_csv(proc / "transactions.csv"),
        "products": pd.read_csv(proc / "products.csv"),
    }
    results = run(ds)
    print(results["category_elasticity"].to_string())
