-- Customer 360 from purchases only (Olist has no web sessions or campaigns)

CREATE OR REPLACE VIEW customer_360_view AS
SELECT
    c.customer_id,
    c.signup_date,
    c.city,
    c.state,
    m.total_orders,
    m.total_revenue AS total_spent,
    m.avg_order_value,
    m.first_purchase,
    m.last_purchase AS last_purchase_date,
    m.lifespan_days,
    DATE_TRUNC('month', m.first_purchase)::date AS cohort_month,
    (p.analysis_date - m.last_purchase) AS days_inactive
FROM dim_customers c
JOIN customer_metrics m ON m.customer_id = c.customer_id
CROSS JOIN analysis_params p;

SELECT * FROM customer_360_view LIMIT 20;
