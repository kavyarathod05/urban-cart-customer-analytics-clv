-- Churn from inactivity vs analysis_date (last order in the extract)
SELECT
    customer_id,
    last_purchase_date,
    days_inactive,
    CASE
        WHEN days_inactive > 180 THEN 'High Risk'
        WHEN days_inactive > 90  THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_segment
FROM customer_360_view;

-- Value bands (BRL)
SELECT
    CASE
        WHEN total_spent >= 500 THEN 'High Value'
        WHEN total_spent >= 150 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS segment,
    COUNT(*) AS customers,
    SUM(total_spent) AS revenue
FROM customer_360_view
GROUP BY 1
ORDER BY revenue DESC;

-- Repeat rate
SELECT
    COUNT(*) FILTER (WHERE total_orders >= 2)::numeric / COUNT(*) AS repeat_rate
FROM customer_metrics;

-- Cohort retention
SELECT * FROM cohort_retention ORDER BY cohort_month, period_number;

-- Revenue by payment type (Olist has no ad-spend channel)
SELECT
    payment_type,
    SUM(amount) AS revenue,
    COUNT(DISTINCT order_id) AS orders
FROM orders_fact
GROUP BY 1
ORDER BY revenue DESC;
