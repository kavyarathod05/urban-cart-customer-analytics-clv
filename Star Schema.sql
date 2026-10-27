-- UrbanCart star schema (Olist)
-- Built by setup_local.py. This file is the readable reference.

-- dim_customers: one row per person (Olist customer_unique_id)
--   customer_id, signup_date, city, state
-- dim_products: product_id, category (English), price (median line price)
-- dim_date: one row per order_date
-- orders_fact: one row per (order_id, product_id)
--   amount = price + freight; no campaign_id / channel / cost / gender / age

CREATE TABLE dim_customers AS
SELECT DISTINCT customer_id, signup_date::date AS signup_date, city, state
FROM customers;

CREATE TABLE dim_products AS
SELECT DISTINCT product_id, category, price FROM products;

CREATE TABLE dim_date AS
SELECT DISTINCT
    order_date::date AS date_id,
    EXTRACT(YEAR FROM order_date::date)::int AS year,
    EXTRACT(MONTH FROM order_date::date)::int AS month,
    EXTRACT(DAY FROM order_date::date)::int AS day,
    EXTRACT(QUARTER FROM order_date::date)::int AS quarter,
    DATE_TRUNC('month', order_date::date)::date AS month_start
FROM orders;

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

-- Recency clock for this extract (not wall-clock today)
CREATE TABLE analysis_params AS
SELECT MAX(order_date) AS analysis_date,
       MIN(order_date) AS first_date,
       COUNT(DISTINCT order_id) AS total_orders
FROM orders_fact;
