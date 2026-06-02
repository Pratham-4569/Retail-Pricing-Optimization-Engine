"""
demand_forecast.py — Demand Forecasting Module
================================================

Uses Holt-Winters Exponential Smoothing (additive trend & seasonality)
to forecast demand per category for the next *N* months.

Falls back to a simple moving average when the time series is too short
or the model fails to converge.
"""

from __future__ import annotations

import logging
import warnings
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

# Suppress statsmodels convergence warnings — we handle failures gracefully
warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning, module="statsmodels")


# ────────────────────────────────────────────────────────────────────────────────
# Aggregation
# ────────────────────────────────────────────────────────────────────────────────

def aggregate_monthly_demand(
    txn: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate daily transactions to monthly demand by category.

    Returns
    -------
    pd.DataFrame
        Columns: ``category``, ``month`` (Period), ``quantity``.
    """
    txn = txn.copy()
    txn["date"] = pd.to_datetime(txn["date"])

    txn_cat = txn.merge(products[["product_id", "category"]], on="product_id", how="left")
    txn_cat["month"] = txn_cat["date"].dt.to_period("M")

    monthly = (
        txn_cat.groupby(["category", "month"])["quantity"]
        .sum()
        .reset_index()
    )
    monthly = monthly.sort_values(["category", "month"]).reset_index(drop=True)
    logger.info("Aggregated monthly demand: %d rows across %d categories.",
                len(monthly), monthly["category"].nunique())
    return monthly


# ────────────────────────────────────────────────────────────────────────────────
# Forecasting
# ────────────────────────────────────────────────────────────────────────────────

def _simple_moving_average(
    series: pd.Series, horizon: int, window: int = 3
) -> pd.Series:
    """Fallback forecast using a simple moving average of the last *window* points."""
    avg = series.tail(window).mean()
    return pd.Series([round(avg)] * horizon, name="forecast")


def forecast_category(
    monthly: pd.DataFrame,
    category: str,
    horizon: int = cfg.FORECAST_MONTHS,
    seasonal_period: int = cfg.SEASONAL_PERIOD,
) -> dict[str, Any]:
    """Forecast demand for a single category.

    Parameters
    ----------
    monthly : pd.DataFrame
        Output of :func:`aggregate_monthly_demand`.
    category : str
        Category to forecast.
    horizon : int
        Number of future months.
    seasonal_period : int
        Seasonality period (12 for monthly data).

    Returns
    -------
    dict  with keys:
        ``category``, ``historical`` (list), ``forecast`` (list),
        ``confidence_lower`` (list), ``confidence_upper`` (list),
        ``dates_historical``, ``dates_forecast``, ``method``.
    """
    cat_data = monthly[monthly["category"] == category].copy()
    cat_data = cat_data.sort_values("month")
    ts = cat_data.set_index("month")["quantity"]

    # Convert PeriodIndex to DatetimeIndex with monthly frequency for statsmodels
    ts.index = ts.index.to_timestamp()
    ts = ts.asfreq("MS", fill_value=0)

    historical_values = ts.values.tolist()
    historical_dates = [d.strftime("%Y-%m") for d in ts.index]

    method = "holt_winters"
    forecast_values: list[float] = []
    conf_lower: list[float] = []
    conf_upper: list[float] = []

    # Need at least 2 full seasonal cycles for Holt-Winters
    if len(ts) >= 2 * seasonal_period:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            model = ExponentialSmoothing(
                ts,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_period,
            ).fit(optimized=True, use_brute=True)

            pred = model.forecast(horizon)
            forecast_values = [max(0, round(v)) for v in pred.values]

            # Approximate CI using residual std
            residual_std = float(np.std(model.resid.dropna()))
            z = 1.96  # 95 % CI
            conf_lower = [max(0, round(v - z * residual_std)) for v in pred.values]
            conf_upper = [round(v + z * residual_std) for v in pred.values]

            logger.info("  %s → Holt-Winters OK (AIC=%.1f)", category, model.aic)
        except Exception as exc:
            logger.warning("  %s → Holt-Winters failed (%s), falling back to SMA.", category, exc)
            method = "simple_moving_average"
    else:
        logger.info("  %s → insufficient data (%d months), using SMA.", category, len(ts))
        method = "simple_moving_average"

    if method == "simple_moving_average":
        sma = _simple_moving_average(ts, horizon)
        forecast_values = sma.tolist()
        residual_std = float(ts.std()) if len(ts) > 1 else 0.0
        conf_lower = [max(0, round(v - 1.96 * residual_std)) for v in forecast_values]
        conf_upper = [round(v + 1.96 * residual_std) for v in forecast_values]

    # Future date labels
    last_date = ts.index[-1]
    forecast_dates = [
        (last_date + pd.DateOffset(months=i + 1)).strftime("%Y-%m")
        for i in range(horizon)
    ]

    return {
        "category": category,
        "historical": historical_values,
        "forecast": forecast_values,
        "confidence_lower": conf_lower,
        "confidence_upper": conf_upper,
        "dates_historical": historical_dates,
        "dates_forecast": forecast_dates,
        "method": method,
    }


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(datasets: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Forecast demand for every category.

    Returns
    -------
    list[dict]
        One entry per category with historical + forecast arrays.
    """
    txn = datasets["transactions"]
    products = datasets["products"]

    monthly = aggregate_monthly_demand(txn, products)
    categories = sorted(monthly["category"].unique())

    logger.info("Forecasting demand for %d categories …", len(categories))
    results: list[dict[str, Any]] = []

    for cat in categories:
        result = forecast_category(monthly, cat)
        results.append(result)

    logger.info("Demand forecasting complete.")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    proc = cfg.PROCESSED_DATA_DIR
    ds = {
        "transactions": pd.read_csv(proc / "transactions.csv"),
        "products": pd.read_csv(proc / "products.csv"),
    }
    results = run(ds)
    for r in results:
        print(f"{r['category']:20s} → method={r['method']}, forecast={r['forecast']}")
