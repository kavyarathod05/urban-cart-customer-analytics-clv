----Customer Churn Probability
SELECT
    customer_id,
    last_purchase_date,
    
    (CURRENT_DATE - last_purchase_date) AS days_inactive,
    
    CASE
        WHEN (CURRENT_DATE - last_purchase_date) > 180
            THEN 'High Churn Risk'
        WHEN (CURRENT_DATE - last_purchase_date) > 90
            THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_segment

FROM customer_360_view;


----Most Profitable Customer Segment
SELECT
    CASE
        WHEN total_spent > 50000 THEN 'High Value'
        WHEN total_spent > 20000 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS segment,
    COUNT(*) AS customers,
    SUM(total_spent) AS revenue
FROM customer_360_view
GROUP BY segment
ORDER BY revenue DESC;


----Cross selling Oppotunities
SELECT
    a.product_id AS product_1,
    b.product_id AS product_2,
    COUNT(*) AS frequency
FROM orders a
JOIN orders b
    ON a.customer_id = b.customer_id
    AND a.product_id <> b.product_id
GROUP BY product_1, product_2
ORDER BY frequency DESC;

----Marketing ROI By Channel
---ROI=REVENUE/SPEND
SELECT
    m.channel,
    SUM(o.amount) AS revenue,
    SUM(m.spend) AS spend,
    SUM(o.amount) / NULLIF(SUM(m.spend), 0) AS ROI
FROM marketing_campaigns m
JOIN orders o
    ON CASE
        WHEN o.channel = 'Web' THEN 'Google Ads'
        WHEN o.channel = 'Mobile App' THEN 'Instagram'
        WHEN o.channel = 'Store' THEN 'Email'
    END = m.channel
GROUP BY m.channel
ORDER BY ROI DESC;
    