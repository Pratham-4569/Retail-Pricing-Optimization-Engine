"""
export_dashboard_data.py — JSON Exporter for Web Dashboard
============================================================

Serialises all analytics results to JSON files in the ``output/``
directory, handling numpy / pandas types gracefully.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
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
# Custom JSON encoder
# ────────────────────────────────────────────────────────────────────────────────

class _NumpyPandasEncoder(json.JSONEncoder):
    """Handle numpy scalars, pandas Timestamps, and other non-JSON types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, pd.Period):
            return str(obj)
        if pd.isna(obj):
            return None
        return super().default(obj)


def _save_json(data: Any, filepath: Path) -> None:
    """Write data to a JSON file with the custom encoder."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=_NumpyPandasEncoder, indent=2, ensure_ascii=False)
    logger.info("Exported → %s", filepath)


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to a list of dicts, sanitising types."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ────────────────────────────────────────────────────────────────────────────────
# Individual exporters
# ────────────────────────────────────────────────────────────────────────────────

def export_overview_kpis(kpi_results: dict[str, Any], out_dir: Path) -> None:
    """output/overview_kpis.json — summary KPIs."""
    payload = kpi_results.get("overview", {})
    payload["discount_effectiveness"] = kpi_results.get("discount_effectiveness", {})
    _save_json(payload, out_dir / "overview_kpis.json")


def export_product_analytics(kpi_results: dict[str, Any], out_dir: Path) -> None:
    """output/product_analytics.json — product performance data."""
    df = kpi_results.get("product_kpis", pd.DataFrame())
    payload = {
        "products": _df_to_records(df),
        "top_sellers": _df_to_records(kpi_results.get("top_sellers", pd.DataFrame())),
        "bottom_sellers": _df_to_records(kpi_results.get("bottom_sellers", pd.DataFrame())),
    }
    _save_json(payload, out_dir / "product_analytics.json")


def export_category_analytics(kpi_results: dict[str, Any], out_dir: Path) -> None:
    """output/category_analytics.json — category breakdowns."""
    df = kpi_results.get("category_kpis", pd.DataFrame())
    _save_json(_df_to_records(df), out_dir / "category_analytics.json")


def export_monthly_trends(kpi_results: dict[str, Any], out_dir: Path) -> None:
    """output/monthly_trends.json — time series."""
    df = kpi_results.get("monthly_trends", pd.DataFrame())
    _save_json(_df_to_records(df), out_dir / "monthly_trends.json")


def export_forecast_data(forecast_results: list[dict[str, Any]], out_dir: Path) -> None:
    """output/forecast_data.json — historical + forecast demand."""
    _save_json(forecast_results, out_dir / "forecast_data.json")


def export_elasticity_data(elasticity_results: dict[str, Any], out_dir: Path) -> None:
    """output/elasticity_data.json — elasticity per category / product."""
    payload = {
        "category_elasticity": _df_to_records(
            elasticity_results.get("category_elasticity", pd.DataFrame())
        ),
        "product_elasticity": _df_to_records(
            elasticity_results.get("product_elasticity", pd.DataFrame())
        ),
        "multifeature_model": elasticity_results.get("multifeature_model", {}),
    }
    _save_json(payload, out_dir / "elasticity_data.json")


def export_simulation_results(sim_df: pd.DataFrame, out_dir: Path) -> None:
    """output/simulation_results.json — all markdown scenarios."""
    _save_json(_df_to_records(sim_df), out_dir / "simulation_results.json")


def export_recommendations(opt_results: dict[str, pd.DataFrame], out_dir: Path) -> None:
    """output/recommendations.json — final optimization recommendations."""
    recs_df = opt_results.get("recommendations", pd.DataFrame())
    payload = {
        "recommendations": _df_to_records(recs_df),
        "summary": {
            "total_products": len(recs_df),
            "avg_optimal_discount_pct": round(recs_df["optimal_discount_pct"].mean(), 2)
            if not recs_df.empty else 0.0,
            "total_expected_profit": round(recs_df["expected_profit"].sum(), 2)
            if not recs_df.empty else 0.0,
            "total_expected_revenue": round(recs_df["expected_revenue"].sum(), 2)
            if not recs_df.empty else 0.0,
        },
    }
    _save_json(payload, out_dir / "recommendations.json")


def export_whatif_params(products: pd.DataFrame, out_dir: Path) -> None:
    """output/whatif_params.json — parameters for front-end what-if analysis."""
    payload = {
        "discount_range": {
            "min": cfg.OPT_DISCOUNT_MIN * 100,
            "max": cfg.OPT_DISCOUNT_MAX * 100,
            "step": 5,
        },
        "products": _df_to_records(
            products[["product_id", "product_name", "category", "base_price", "cost"]]
        ),
        "categories": sorted(products["category"].unique().tolist()),
        "simulation_discounts": [d * 100 for d in cfg.SIMULATION_DISCOUNTS],
    }
    _save_json(payload, out_dir / "whatif_params.json")


# ────────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────────

def run(
    kpi_results: dict[str, Any],
    forecast_results: list[dict[str, Any]],
    elasticity_results: dict[str, Any],
    simulation_df: pd.DataFrame,
    opt_results: dict[str, pd.DataFrame],
    products: pd.DataFrame,
    out_dir: Path | None = None,
) -> None:
    """Export everything to JSON files under *out_dir*."""
    out_dir = out_dir or cfg.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Exporting dashboard JSON files to %s …", out_dir)

    export_overview_kpis(kpi_results, out_dir)
    export_product_analytics(kpi_results, out_dir)
    export_category_analytics(kpi_results, out_dir)
    export_monthly_trends(kpi_results, out_dir)
    export_forecast_data(forecast_results, out_dir)
    export_elasticity_data(elasticity_results, out_dir)
    export_simulation_results(simulation_df, out_dir)
    export_recommendations(opt_results, out_dir)
    export_whatif_params(products, out_dir)

    logger.info("All dashboard data exported (%d files).", 9)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=cfg.LOG_FORMAT, datefmt=cfg.LOG_DATE_FORMAT)
    logger.info("Run via main.py for full export.")
