"""
main.py — Master Pipeline Orchestrator
========================================

Retail Pricing & Markdown Decision Engine
------------------------------------------

Runs the full analytics pipeline end-to-end:

    1. Generate synthetic retail data
    2. ETL — clean, validate, load into SQLite
    3. Compute business KPIs
    4. Forecast demand per category
    5. Estimate price elasticity
    6. Simulate markdown scenarios
    7. Optimize discounts for profit maximisation
    8. Export all results to JSON for the dashboard

Usage::

    python main.py

All monetary values are in Indian Rupees (₹).
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# ── Ensure project root is on sys.path ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg

# ── Set up logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format=cfg.LOG_FORMAT,
    datefmt=cfg.LOG_DATE_FORMAT,
)
logger = logging.getLogger("main")


# ────────────────────────────────────────────────────────────────────────────────
# Timing helper
# ────────────────────────────────────────────────────────────────────────────────

class _PhaseTimer:
    """Context manager that logs elapsed time for a named phase."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float = 0.0

    def __enter__(self) -> "_PhaseTimer":
        logger.info("━" * 60)
        logger.info("▶  PHASE: %s", self.name)
        logger.info("━" * 60)
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc) -> None:
        elapsed = time.perf_counter() - self._start
        logger.info("✔  %s completed in %.2f s", self.name, elapsed)
        logger.info("")


# ────────────────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Execute the full Retail Pricing & Markdown Decision Engine pipeline."""
    pipeline_start = time.perf_counter()

    logger.info("=" * 60)
    logger.info("  RETAIL PRICING & MARKDOWN DECISION ENGINE")
    logger.info("  Currency: %s  |  Products: %d  |  Stores: %d",
                cfg.CURRENCY_SYMBOL, cfg.NUM_PRODUCTS, cfg.NUM_STORES)
    logger.info("  Date range: %s → %s", cfg.START_DATE, cfg.END_DATE)
    logger.info("=" * 60)
    logger.info("")

    # ── 1. Data Generation ─────────────────────────────────────────────────
    with _PhaseTimer("Data Generation"):
        from src.data_generation import generate_data
        raw_datasets = generate_data.run()

    # ── 2. ETL Pipeline ────────────────────────────────────────────────────
    with _PhaseTimer("ETL Pipeline"):
        from src.etl import etl_pipeline
        datasets = etl_pipeline.run()

    # ── 3. Business KPIs ───────────────────────────────────────────────────
    with _PhaseTimer("KPI Calculation"):
        from src.analytics import kpi_calculator
        kpi_results = kpi_calculator.run(datasets)

    # ── 4. Demand Forecasting ──────────────────────────────────────────────
    with _PhaseTimer("Demand Forecasting"):
        from src.forecasting import demand_forecast
        forecast_results = demand_forecast.run(datasets)

    # ── 5. Price Elasticity ────────────────────────────────────────────────
    with _PhaseTimer("Price Elasticity Analysis"):
        from src.elasticity import price_elasticity
        elasticity_results = price_elasticity.run(datasets)

    # ── 6. Markdown Simulation ─────────────────────────────────────────────
    with _PhaseTimer("Markdown Simulation"):
        from src.simulation import markdown_simulator
        simulation_df = markdown_simulator.run(datasets, elasticity_results)

    # ── 7. Optimization ────────────────────────────────────────────────────
    with _PhaseTimer("Discount Optimization"):
        from src.optimization import optimizer
        opt_results = optimizer.run(datasets, elasticity_results)

    # ── 8. Export to JSON ──────────────────────────────────────────────────
    with _PhaseTimer("Dashboard Export"):
        from src.utils import export_dashboard_data
        export_dashboard_data.run(
            kpi_results=kpi_results,
            forecast_results=forecast_results,
            elasticity_results=elasticity_results,
            simulation_df=simulation_df,
            opt_results=opt_results,
            products=datasets["products"],
        )

    # ── Final Summary ──────────────────────────────────────────────────────
    total_elapsed = time.perf_counter() - pipeline_start
    overview = kpi_results.get("overview", {})
    recs = opt_results.get("recommendations", None)

    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info("  Total time          : %.2f seconds", total_elapsed)
    logger.info("  Total revenue       : %s%s", cfg.CURRENCY_SYMBOL,
                f"{overview.get('total_revenue', 0):,.2f}")
    logger.info("  Total profit        : %s%s", cfg.CURRENCY_SYMBOL,
                f"{overview.get('total_profit', 0):,.2f}")
    logger.info("  Total orders        : %s", f"{overview.get('total_orders', 0):,}")
    logger.info("  Gross margin        : %.2f%%", overview.get("overall_gross_margin", 0))

    if recs is not None and not recs.empty:
        logger.info("  Avg optimal discount: %.2f%%", recs["optimal_discount_pct"].mean())
        logger.info("  Projected profit    : %s%s", cfg.CURRENCY_SYMBOL,
                    f"{recs['expected_profit'].sum():,.2f}")

    logger.info("")
    logger.info("  Output files → %s", cfg.OUTPUT_DIR)
    logger.info("  Database     → %s", cfg.DATABASE_PATH)
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user.")
        sys.exit(1)
    except Exception:
        logger.exception("Pipeline failed with an unexpected error.")
        sys.exit(2)
