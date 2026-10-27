#!/usr/bin/env python3
"""Local UrbanCart setup — PostgreSQL only, data from the real Olist public dataset.

Pipeline:  dataset/*.csv  ->  raw tables  ->  star schema  ->  analytics tables / views

Run `python transform_olist.py` first if dataset/*.csv are missing (it builds them
from dataset/raw/ Olist files).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"

DB_URL = os.getenv(
    "URBANCART_DB_URL",
    f"postgresql+psycopg2://{os.getenv('USER', 'postgres')}@localhost:5432/urbancart",
)


def engine():
    return create_engine(DB_URL)


def load_raw_tables(eng) -> None:
    print("Loading Olist-derived CSV datasets...")
    customers = pd.read_csv(DATASET / "customers.csv", parse_dates=["signup_date"])
    products = pd.read_csv(DATASET / "products.csv")
    orders = pd.read_csv(DATASET / "orders.csv", parse_dates=["order_date"])

    customers["signup_date"] = customers["signup_date"].dt.date
    orders["order_date"] = orders["order_date"].dt.date

    # Drop raw tables (and anything depending on them, incl. legacy objects from
    # the pre-Olist schema) so pandas can recreate them cleanly.
    with eng.begin() as conn:
        for tbl in (
            "customers", "products", "orders",
            "marketing_campaigns", "web_logs",          # legacy sources
            "customer_metrices", "rfm_segmentationss",  # legacy typos
            "dim_campaigns", "load_tracker",
        ):
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
        for view in ("marketing_roi", "customer_lifespans", "purchase_frequency"):
            conn.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE"))

    customers.to_sql("customers", eng, if_exists="replace", index=False, chunksize=10_000)
    products.to_sql("products", eng, if_exists="replace", index=False, chunksize=10_000)
    orders.to_sql("orders", eng, if_exists="replace", index=False, chunksize=10_000)

    print(
        f"  customers={len(customers):,}  products={len(products):,}  "
        f"order_lines={len(orders):,}  orders={orders['order_id'].nunique():,}"
    )


WAREHOUSE_SQL = """
DROP TABLE IF EXISTS orders_fact CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS analysis_params CASCADE;
DROP TABLE IF EXISTS customer_metrics CASCADE;
DROP TABLE IF EXISTS clv_table CASCADE;
DROP TABLE IF EXISTS rfm_segmentation CASCADE;
DROP TABLE IF EXISTS cohort_retention CASCADE;
DROP TABLE IF EXISTS product_pairs CASCADE;
DROP TABLE IF EXISTS category_pairs CASCADE;
DROP VIEW IF EXISTS customer_360_view CASCADE;
DROP VIEW IF EXISTS clv_segmentation CASCADE;
DROP VIEW IF EXISTS churn_risk CASCADE;
DROP VIEW IF EXISTS monthly_kpis CASCADE;
DROP VIEW IF EXISTS category_performance CASCADE;
DROP VIEW IF EXISTS state_revenue CASCADE;

-- ---------------------------------------------------------------- dimensions
CREATE TABLE dim_customers AS
SELECT DISTINCT customer_id, signup_date::date AS signup_date, city, state
FROM customers;
ALTER TABLE dim_customers ADD PRIMARY KEY (customer_id);

CREATE TABLE dim_products AS
SELECT DISTINCT product_id, category, price FROM products;
ALTER TABLE dim_products ADD PRIMARY KEY (product_id);

CREATE TABLE dim_date AS
SELECT DISTINCT
    order_date::date AS date_id,
    EXTRACT(YEAR FROM order_date::date)::int AS year,
    EXTRACT(MONTH FROM order_date::date)::int AS month,
    EXTRACT(DAY FROM order_date::date)::int AS day,
    EXTRACT(QUARTER FROM order_date::date)::int AS quarter,
    DATE_TRUNC('month', order_date::date)::date AS month_start
FROM orders;
ALTER TABLE dim_date ADD PRIMARY KEY (date_id);

-- ---------------------------------------------------------------- fact
CREATE TABLE orders_fact AS
SELECT
    order_line_id,
    order_id,
    customer_id,
    product_id,
    order_date::date AS order_date,
    quantity,
    price,
    freight,
    amount,
    payment_type,
    order_status
FROM orders;
ALTER TABLE orders_fact ADD PRIMARY KEY (order_line_id);
CREATE INDEX ix_fact_customer ON orders_fact (customer_id);
CREATE INDEX ix_fact_product  ON orders_fact (product_id);
CREATE INDEX ix_fact_order    ON orders_fact (order_id);
CREATE INDEX ix_fact_date     ON orders_fact (order_date);

-- Analysis date = last order in the dataset (Olist spans 2016-2018; wall-clock
-- "today" would mark every customer as churned).
CREATE TABLE analysis_params AS
SELECT MAX(order_date) AS analysis_date,
       MIN(order_date) AS first_date,
       COUNT(DISTINCT order_id) AS total_orders
FROM orders_fact;

-- ---------------------------------------------------------------- customer metrics
CREATE TABLE customer_metrics AS
SELECT
    customer_id,
    COUNT(DISTINCT order_id)                AS total_orders,
    SUM(amount)                             AS total_revenue,
    SUM(amount) / COUNT(DISTINCT order_id)  AS avg_order_value,
    MIN(order_date)                         AS first_purchase,
    MAX(order_date)                         AS last_purchase,
    (MAX(order_date) - MIN(order_date))     AS lifespan_days
FROM orders_fact
GROUP BY customer_id;
ALTER TABLE customer_metrics ADD PRIMARY KEY (customer_id);

-- ---------------------------------------------------------------- customer 360
CREATE OR REPLACE VIEW customer_360_view AS
SELECT
    c.customer_id,
    c.signup_date,
    c.city,
    c.state,
    m.total_orders,
    m.total_revenue                         AS total_spent,
    m.avg_order_value,
    m.first_purchase,
    m.last_purchase                         AS last_purchase_date,
    m.lifespan_days,
    DATE_TRUNC('month', m.first_purchase)::date AS cohort_month,
    (p.analysis_date - m.last_purchase)     AS days_inactive
FROM dim_customers c
JOIN customer_metrics m ON m.customer_id = c.customer_id
CROSS JOIN analysis_params p;

-- ---------------------------------------------------------------- CLV
-- CLV = AOV x purchase_frequency (orders / yr) x lifespan (years)
-- Customers with one order have lifespan 0 -> frequency = order count, CLV = 0
-- lifetime beyond the single order; we floor lifespan at 1 day so every buyer
-- has a non-zero historic CLV equal to at least one order's value.
CREATE TABLE clv_table AS
WITH base AS (
    SELECT
        customer_id,
        avg_order_value,
        total_orders,
        GREATEST(lifespan_days, 1) / 365.0 AS lifespan_years
    FROM customer_metrics
)
SELECT
    customer_id,
    ROUND(avg_order_value::numeric, 2)                              AS avg_order_value,
    ROUND((total_orders / lifespan_years)::numeric, 4)              AS purchase_frequency,
    ROUND(lifespan_years::numeric, 4)                               AS lifespan_years,
    ROUND((avg_order_value * (total_orders / lifespan_years) * lifespan_years)::numeric, 2) AS clv
FROM base;
ALTER TABLE clv_table ADD PRIMARY KEY (customer_id);

-- Bands tuned for BRL order values (Olist median order ~ 100 BRL).
CREATE OR REPLACE VIEW clv_segmentation AS
SELECT
    customer_id,
    clv,
    CASE
        WHEN clv < 150  THEN 'Low Value'
        WHEN clv < 500  THEN 'Medium Value'
        ELSE 'High Value'
    END AS customer_segment
FROM clv_table;

-- ---------------------------------------------------------------- RFM
-- Recency / Monetary scored by quintile (NTILE 5).
-- Frequency uses business rules because ~97% of Olist customers order once,
-- so quintiles on frequency would be degenerate:  1 order=1, 2=3, 3+=5.
CREATE TABLE rfm_segmentation AS
WITH rfm_base AS (
    SELECT
        m.customer_id,
        (p.analysis_date - m.last_purchase) AS recency,
        m.total_orders                      AS frequency,
        m.total_revenue                     AS monetary
    FROM customer_metrics m CROSS JOIN analysis_params p
),
scores AS (
    SELECT
        customer_id, recency, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency DESC)  AS r_score,
        CASE WHEN frequency >= 3 THEN 5
             WHEN frequency  = 2 THEN 3
             ELSE 1 END                        AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)  AS m_score
    FROM rfm_base
)
SELECT
    customer_id, recency, frequency, monetary, r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score = 5 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score = 1                  THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3                 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score = 1 AND m_score <= 2 THEN 'Lost Customers'
        ELSE 'Average Customers'
    END AS customer_segment
FROM scores;
ALTER TABLE rfm_segmentation ADD PRIMARY KEY (customer_id);

-- ---------------------------------------------------------------- churn
CREATE OR REPLACE VIEW churn_risk AS
SELECT
    customer_id,
    last_purchase_date,
    total_spent,
    total_orders,
    days_inactive,
    CASE
        WHEN days_inactive > 180 THEN 'High Risk'
        WHEN days_inactive > 90  THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_segment
FROM customer_360_view;

-- ---------------------------------------------------------------- cohorts
CREATE TABLE cohort_retention AS
WITH cust_cohort AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::date AS cohort_month
    FROM orders_fact GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        f.customer_id,
        c.cohort_month,
        ((EXTRACT(YEAR  FROM f.order_date) - EXTRACT(YEAR  FROM c.cohort_month)) * 12
       + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM c.cohort_month)))::int AS period_number
    FROM orders_fact f JOIN cust_cohort c USING (customer_id)
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size FROM cust_cohort GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.period_number,
    s.cohort_size,
    COUNT(DISTINCT a.customer_id)                                    AS retained_customers,
    ROUND(COUNT(DISTINCT a.customer_id)::numeric / s.cohort_size, 4) AS retention_rate
FROM activity a JOIN sizes s USING (cohort_month)
GROUP BY a.cohort_month, a.period_number, s.cohort_size
ORDER BY a.cohort_month, a.period_number;

-- ---------------------------------------------------------------- market basket
-- Basket = order.  Support / Confidence / Lift.
--   product_pairs  : product-level rules (min 3 co-orders) -> concrete cross-sell
--   category_pairs : category-level rules (min 5 co-orders) -> assortment view
CREATE TABLE product_pairs AS
WITH basket AS (
    SELECT DISTINCT order_id, product_id FROM orders_fact
),
prod_support AS (
    SELECT product_id, COUNT(DISTINCT order_id) AS orders_with FROM basket GROUP BY product_id
),
pairs AS (
    SELECT a.product_id AS product_a, b.product_id AS product_b, COUNT(*) AS pair_orders
    FROM basket a JOIN basket b ON a.order_id = b.order_id AND a.product_id < b.product_id
    GROUP BY a.product_id, b.product_id
)
SELECT
    pr.product_a,
    pa.category AS category_a,
    pr.product_b,
    pb.category AS category_b,
    pr.pair_orders,
    ROUND(pr.pair_orders::numeric / ap.total_orders, 6)                               AS support,
    ROUND(pr.pair_orders::numeric / sa.orders_with, 4)                                AS confidence_a_to_b,
    ROUND(pr.pair_orders::numeric / sb.orders_with, 4)                                AS confidence_b_to_a,
    ROUND((pr.pair_orders::numeric * ap.total_orders)
          / (sa.orders_with::numeric * sb.orders_with), 2)                            AS lift
FROM pairs pr
JOIN prod_support sa ON sa.product_id = pr.product_a
JOIN prod_support sb ON sb.product_id = pr.product_b
JOIN dim_products pa ON pa.product_id = pr.product_a
JOIN dim_products pb ON pb.product_id = pr.product_b
CROSS JOIN analysis_params ap
WHERE pr.pair_orders >= 3
ORDER BY lift DESC, pr.pair_orders DESC;

CREATE TABLE category_pairs AS
WITH basket AS (
    SELECT DISTINCT f.order_id, p.category
    FROM orders_fact f JOIN dim_products p USING (product_id)
),
cat_support AS (
    SELECT category, COUNT(DISTINCT order_id) AS orders_with FROM basket GROUP BY category
),
pairs AS (
    SELECT a.category AS category_a, b.category AS category_b, COUNT(*) AS pair_orders
    FROM basket a JOIN basket b ON a.order_id = b.order_id AND a.category < b.category
    GROUP BY a.category, b.category
)
SELECT
    pr.category_a,
    pr.category_b,
    pr.pair_orders,
    ROUND(pr.pair_orders::numeric / ap.total_orders, 6)                               AS support,
    ROUND(pr.pair_orders::numeric / sa.orders_with, 4)                                AS confidence_a_to_b,
    ROUND(pr.pair_orders::numeric / sb.orders_with, 4)                                AS confidence_b_to_a,
    ROUND((pr.pair_orders::numeric * ap.total_orders)
          / (sa.orders_with::numeric * sb.orders_with), 4)                            AS lift
FROM pairs pr
JOIN cat_support sa ON sa.category = pr.category_a
JOIN cat_support sb ON sb.category = pr.category_b
CROSS JOIN analysis_params ap
WHERE pr.pair_orders >= 5
ORDER BY lift DESC;

-- ---------------------------------------------------------------- reporting views
CREATE OR REPLACE VIEW monthly_kpis AS
SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    SUM(amount)                           AS revenue,
    COUNT(DISTINCT order_id)              AS orders,
    COUNT(DISTINCT customer_id)           AS customers,
    SUM(amount) / COUNT(DISTINCT order_id) AS aov
FROM orders_fact
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE VIEW category_performance AS
SELECT
    p.category,
    SUM(f.amount)               AS revenue,
    SUM(f.quantity)             AS units,
    COUNT(DISTINCT f.order_id)  AS orders,
    COUNT(DISTINCT f.customer_id) AS customers,
    SUM(f.amount) / COUNT(DISTINCT f.order_id) AS revenue_per_order
FROM orders_fact f JOIN dim_products p USING (product_id)
GROUP BY p.category;

CREATE OR REPLACE VIEW state_revenue AS
SELECT
    c.state,
    SUM(f.amount)                 AS revenue,
    COUNT(DISTINCT f.order_id)    AS orders,
    COUNT(DISTINCT f.customer_id) AS customers
FROM orders_fact f JOIN dim_customers c USING (customer_id)
GROUP BY c.state;
"""


def build_warehouse(eng) -> None:
    print("Building star schema + analytics...")
    with eng.begin() as conn:
        conn.execute(text(WAREHOUSE_SQL))


def smoke_test(eng) -> None:
    print("Smoke test...")
    queries = {
        "analysis_params": "SELECT * FROM analysis_params",
        "orders_fact": "SELECT COUNT(*) FROM orders_fact",
        "rfm_segments": "SELECT customer_segment, COUNT(*) FROM rfm_segmentation GROUP BY 1 ORDER BY 2 DESC",
        "clv_segments": "SELECT customer_segment, COUNT(*) FROM clv_segmentation GROUP BY 1 ORDER BY 2 DESC",
        "churn": "SELECT churn_segment, COUNT(*) FROM churn_risk GROUP BY 1 ORDER BY 2 DESC",
        "cohorts": "SELECT COUNT(*) FROM cohort_retention",
        "product_pairs": "SELECT COUNT(*) FROM product_pairs",
        "category_pairs": "SELECT category_a, category_b, lift FROM category_pairs LIMIT 3",
    }
    with eng.connect() as conn:
        for name, q in queries.items():
            rows = conn.execute(text(q)).fetchall()
            print(f"  {name}: {rows[:8]}")


def main() -> int:
    print(f"DB: {DB_URL}")
    if not (DATASET / "orders.csv").exists():
        print("dataset/orders.csv missing — run:  python transform_olist.py", file=sys.stderr)
        return 1
    eng = engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(
            "Cannot connect to PostgreSQL.\n"
            "Start it with:  brew services start postgresql@16\n"
            "Create DB with: createdb urbancart\n"
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    load_raw_tables(eng)
    build_warehouse(eng)
    smoke_test(eng)
    print("\nDone. Run dashboard:  streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
