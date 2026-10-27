-- Historic CLV (BRL)
-- CLV = AOV × purchase_frequency × lifespan_years
-- lifespan is floored at 1 day so a one-order buyer has CLV = that order.

CREATE TABLE customer_metrics AS
SELECT
    customer_id,
    COUNT(DISTINCT order_id)               AS total_orders,
    SUM(amount)                            AS total_revenue,
    SUM(amount) / COUNT(DISTINCT order_id) AS avg_order_value,
    MIN(order_date)                        AS first_purchase,
    MAX(order_date)                        AS last_purchase,
    (MAX(order_date) - MIN(order_date))    AS lifespan_days
FROM orders_fact
GROUP BY customer_id;

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
    ROUND(avg_order_value::numeric, 2) AS avg_order_value,
    ROUND((total_orders / lifespan_years)::numeric, 4) AS purchase_frequency,
    ROUND(lifespan_years::numeric, 4) AS lifespan_years,
    ROUND((avg_order_value * (total_orders / lifespan_years) * lifespan_years)::numeric, 2) AS clv
FROM base;

-- Bands for Olist BRL (not the old INR 3000 / 9000 cuts)
CREATE OR REPLACE VIEW clv_segmentation AS
SELECT
    customer_id,
    clv,
    CASE
        WHEN clv < 150 THEN 'Low Value'
        WHEN clv < 500 THEN 'Medium Value'
        ELSE 'High Value'
    END AS customer_segment
FROM clv_table;

SELECT customer_segment, COUNT(*), ROUND(AVG(clv)::numeric, 2)
FROM clv_segmentation GROUP BY 1;
