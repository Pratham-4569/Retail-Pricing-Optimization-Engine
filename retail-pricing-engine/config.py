"""
config.py - Central Configuration for Retail Pricing & Markdown Decision Engine
================================================================================

All project-wide constants, paths, and parameters are defined here.
Currency: Indian Rupees (₹)
"""

from pathlib import Path
from datetime import date

# ──────────────────────────── Project Paths ────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
OUTPUT_DIR = PROJECT_ROOT / "output"

DATABASE_PATH = DATABASE_DIR / "retail_analytics.db"

# ──────────────────────────── Reproducibility ──────────────────────────────────
RANDOM_SEED = 42

# ──────────────────────────── Date Range ───────────────────────────────────────
START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)

# ──────────────────────────── Scale Parameters ─────────────────────────────────
NUM_PRODUCTS = 50
NUM_STORES = 5

# ──────────────────────────── Currency ─────────────────────────────────────────
CURRENCY_SYMBOL = "₹"

# ──────────────────────────── Store Definitions ────────────────────────────────
STORES = [
    {"store_id": "S001", "city": "Mumbai",    "region": "West",  "tier": 1},
    {"store_id": "S002", "city": "Delhi",     "region": "North", "tier": 1},
    {"store_id": "S003", "city": "Bangalore", "region": "South", "tier": 1},
    {"store_id": "S004", "city": "Chennai",   "region": "South", "tier": 2},
    {"store_id": "S005", "city": "Kolkata",   "region": "East",  "tier": 2},
]

# ──────────────────────────── Category Definitions ─────────────────────────────
CATEGORIES = {
    "Grocery": {
        "price_range": (50, 1_500),
        "cost_factor": (0.60, 0.70),   # cost = price × factor
        "elasticity": -0.5,            # inelastic
        "base_demand": (80, 200),      # daily units range
        "products": [
            "Atta", "Basmati Rice", "Sunflower Oil", "Toor Dal",
            "Sugar", "Assam Tea", "Filter Coffee", "Biscuits",
        ],
    },
    "Electronics": {
        "price_range": (500, 50_000),
        "cost_factor": (0.55, 0.65),
        "elasticity": -2.0,            # very elastic
        "base_demand": (5, 30),
        "products": [
            "Wireless Earbuds", "Fast Charger", "Power Bank",
            "Smart Watch", "Tablet",
        ],
    },
    "Clothing": {
        "price_range": (500, 8_000),
        "cost_factor": (0.40, 0.55),
        "elasticity": -1.5,
        "base_demand": (15, 60),
        "products": [
            "Cotton T-Shirt", "Slim-Fit Jeans", "Kurta Set",
            "Silk Saree", "Winter Jacket",
        ],
    },
    "Beauty": {
        "price_range": (200, 5_000),
        "cost_factor": (0.35, 0.50),
        "elasticity": -1.2,
        "base_demand": (20, 70),
        "products": [
            "Herbal Shampoo", "Face Cream", "Matte Lipstick",
            "Eau de Perfume", "Coconut Hair Oil",
        ],
    },
    "Home & Kitchen": {
        "price_range": (300, 15_000),
        "cost_factor": (0.45, 0.60),
        "elasticity": -1.0,            # unit elastic
        "base_demand": (10, 40),
        "products": [
            "Non-Stick Cookware", "Cotton Bedsheet", "Blackout Curtains",
            "Mixer Grinder", "Steam Iron",
        ],
    },
    "Sports": {
        "price_range": (500, 10_000),
        "cost_factor": (0.45, 0.60),
        "elasticity": -1.3,
        "base_demand": (8, 35),
        "products": [
            "Kashmir Willow Cricket Bat", "Yoga Mat", "Running Shoes",
            "Football", "Gym Gloves",
        ],
    },
}

# ──────────────────────────── Seasonality Multipliers ──────────────────────────
SEASONALITY = {
    1: 1.00,   # January
    2: 0.95,   # February
    3: 1.00,   # March
    4: 0.85,   # April   — summer slump begins
    5: 0.85,   # May
    6: 0.85,   # June
    7: 0.95,   # July
    8: 1.05,   # August  — Raksha Bandhan / Independence Day
    9: 1.10,   # September — Navratri build-up
    10: 1.50,  # October  — Diwali season
    11: 1.50,  # November — Diwali / post-Diwali sales
    12: 1.30,  # December — year-end / Christmas
}

# ──────────────────────────── Day-of-Week Effects ──────────────────────────────
DAY_OF_WEEK_EFFECT = {
    0: 0.90,  # Monday
    1: 0.92,  # Tuesday
    2: 0.95,  # Wednesday
    3: 0.98,  # Thursday
    4: 1.05,  # Friday
    5: 1.15,  # Saturday
    6: 1.10,  # Sunday
}

# ──────────────────────────── Promotion Parameters ─────────────────────────────
PROMOTION_PROBABILITY = 0.20          # 20 % of transactions carry a discount
PROMOTION_DISCOUNT_RANGE = (0.05, 0.40)  # 5 % – 40 %

# ──────────────────────────── Competitor Price Band ────────────────────────────
COMPETITOR_PRICE_FACTOR = (0.85, 1.15)

# ──────────────────────────── Simulation Discounts ─────────────────────────────
SIMULATION_DISCOUNTS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

# ──────────────────────────── Optimization Bounds ──────────────────────────────
OPT_DISCOUNT_MIN = 0.0
OPT_DISCOUNT_MAX = 0.50
OPT_MIN_CLEARANCE = 0.60              # at least 60 % inventory clearance

# ──────────────────────────── Forecast Horizon ─────────────────────────────────
FORECAST_MONTHS = 3
SEASONAL_PERIOD = 12

# ──────────────────────────── Logging ──────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
