# Retail Pricing & Markdown Decision Engine

<p align="center">
  <strong>RetailIQ</strong> — An intelligent markdown recommendation system that maximizes profit while clearing excess inventory
</p>

---

## 🎯 Overview

A complete **business decision support platform** that analyzes sales, pricing, inventory, and promotional data to recommend optimal markdown strategies. Built as an end-to-end analytics pipeline with a stunning interactive dashboard.

### Business Questions Answered

| Question | Module |
|----------|--------|
| Which products should be discounted? | Optimization Engine |
| What discount % should be applied? | Optimization Engine |
| How will discount impact demand? | Price Elasticity + Simulation |
| What revenue/profit impact will occur? | Markdown Simulation |
| How much inventory can be cleared? | Markdown Simulation |

---

## 🏗️ Architecture

```
Synthetic Data Generator (Python)
         │
         ▼
    Raw CSV Files
         │
         ▼
   ETL Pipeline (Pandas)
         │
         ▼
  SQLite Database (Data Warehouse)
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
  Business KPIs              Demand Forecasting
  (SQL + Python)              (Statsmodels)
         │                                  │
         │          Price Elasticity ◄───────┘
         │          (Scikit-Learn)
         │                │
         │                ▼
         │       Markdown Simulator
         │                │
         │                ▼
         │       Optimization Engine
         │          (SciPy)
         │                │
         ▼                ▼
     JSON Export ◄────────┘
         │
         ▼
  Web Dashboard (HTML/CSS/JS + Chart.js)
         │
         ▼
  Business Recommendations
```

---

## 📁 Project Structure

```
retail-pricing-engine/
├── main.py                     # Master pipeline orchestrator
├── config.py                   # Central configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── data/
│   ├── raw/                    # Generated CSV files
│   ├── processed/              # Cleaned CSV files
│   └── database/               # SQLite database
│
├── src/
│   ├── data_generation/
│   │   └── generate_data.py    # Synthetic data generator
│   ├── etl/
│   │   └── etl_pipeline.py     # Extract-Transform-Load pipeline
│   ├── analytics/
│   │   └── kpi_calculator.py   # Business KPI calculations
│   ├── forecasting/
│   │   └── demand_forecast.py  # Demand forecasting (Holt-Winters)
│   ├── elasticity/
│   │   └── price_elasticity.py # Price elasticity analysis
│   ├── simulation/
│   │   └── markdown_simulator.py # Discount scenario simulation
│   ├── optimization/
│   │   └── optimizer.py        # Profit optimization engine
│   └── utils/
│       └── export_dashboard_data.py # JSON export for dashboard
│
├── dashboard/
│   ├── index.html              # Executive dashboard
│   ├── style.css               # Premium dark-mode styles
│   └── app.js                  # Charts & interactivity
│
├── sql/
│   ├── database_schema.sql     # Table definitions
│   └── analytics_queries.sql   # KPI queries
│
├── docs/
│   ├── PRD.md                  # Product Requirements Document
│   ├── data_dictionary.md      # Data dictionary
│   ├── database_schema.md      # Schema documentation
│   └── business_report.md      # Final business report
│
├── output/                     # JSON files for dashboard
│   ├── overview_kpis.json
│   ├── product_analytics.json
│   ├── category_analytics.json
│   ├── monthly_trends.json
│   ├── forecast_data.json
│   ├── elasticity_data.json
│   ├── simulation_results.json
│   └── recommendations.json
│
└── tests/                      # Unit tests
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Navigate to project directory
cd retail-pricing-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the complete pipeline
python main.py
```

### View the Dashboard

After running the pipeline, open the dashboard:
```bash
# Open in your default browser
start dashboard/index.html
```

> **Note**: The dashboard also works standalone with built-in sample data — no need to run the Python pipeline first.

---

## 🔧 Modules

### Phase 1: Data Generation
Generates 100K+ realistic retail transactions across 50 products, 5 stores, and 2 years with:
- Indian product names and pricing (₹)
- Seasonal patterns (Diwali, summer, year-end)
- Day-of-week effects
- Promotional discounts
- Competitor pricing

### Phase 2: ETL Pipeline
- **Extract**: Load raw CSVs with type validation
- **Transform**: Clean nulls/duplicates, add computed columns
- **Load**: Insert into SQLite with proper schema and indexes

### Phase 3: Business Analytics
Calculates key performance indicators:
- Revenue, Profit, Gross Margin
- Sell-Through Rate, Inventory Turnover
- Discount Effectiveness
- Category & product breakdowns

### Phase 4: Demand Forecasting
- Holt-Winters Exponential Smoothing
- Monthly forecasts per category
- Confidence intervals
- Handles seasonality automatically

### Phase 5: Price Elasticity
- Log-log regression model
- Per-category elasticity coefficients
- Elastic vs inelastic classification
- Multi-feature analysis

### Phase 6: Markdown Simulation
- 9 discount scenarios per product (0% to 50%)
- Expected demand, revenue, profit per scenario
- Inventory clearance estimation
- Scenario comparison matrix

### Phase 7: Optimization Engine
- SciPy SLSQP constrained optimization
- Maximizes total profit across all products
- Constraints: discount bounds, minimum clearance
- Per-product optimal discount recommendation

### Phase 8: Executive Dashboard
- Premium dark-mode glassmorphism design
- 6 interactive sections
- Chart.js visualizations
- What-if scenario analysis
- Indian Rupee formatting

---

## 📊 Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python** | ETL, Analytics, ML, Optimization |
| **Pandas** | Data manipulation and analysis |
| **NumPy** | Numerical computing |
| **Statsmodels** | Time series forecasting |
| **Scikit-Learn** | Regression models |
| **SciPy** | Mathematical optimization |
| **SQLite** | Data warehouse |
| **HTML/CSS/JS** | Executive dashboard |
| **Chart.js** | Data visualization |

---

## 📋 Deliverables

| # | Deliverable | Location |
|---|------------|----------|
| 1 | Problem Statement & PRD | `docs/PRD.md` |
| 2 | Data Dictionary | `docs/data_dictionary.md` |
| 3 | Database Schema | `docs/database_schema.md`, `sql/database_schema.sql` |
| 4 | ETL Pipeline | `src/etl/etl_pipeline.py` |
| 5 | SQL Analytics Queries | `sql/analytics_queries.sql` |
| 6 | Demand Forecasting Module | `src/forecasting/demand_forecast.py` |
| 7 | Price Elasticity Module | `src/elasticity/price_elasticity.py` |
| 8 | Markdown Optimization Module | `src/optimization/optimizer.py` |
| 9 | Interactive Dashboard | `dashboard/index.html` |
| 10 | Business Report | `docs/business_report.md` |

---

## 📝 Resume Description

> **Retail Pricing & Markdown Decision Engine**
>
> Developed an end-to-end retail decision intelligence platform that analyzed sales, inventory, pricing, and promotional data to recommend profit-maximizing markdown strategies. Designed SQL-based analytics pipelines, demand forecasting models (Holt-Winters), price elasticity analysis (log-log regression), and constrained optimization workflows (SciPy SLSQP) to support executive pricing decisions through an interactive web dashboard.
>
> **Technologies**: Python, Pandas, NumPy, Statsmodels, Scikit-Learn, SciPy, SQLite, HTML/CSS/JavaScript, Chart.js

---

## 📜 License

This project is built for educational and portfolio purposes.
