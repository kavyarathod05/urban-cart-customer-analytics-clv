CREATE OR REPLACE VIEW customer_360_view AS

WITH purchase_history AS (
    SELECT 
        customer_id,
        COUNT(order_id) AS total_orders,
        SUM(amount) AS total_spent,
        AVG(amount) AS avg_order_value,
        MAX(order_date) AS last_purchase_date
    FROM orders
    GROUP BY customer_id
),

engagement_metrics AS (
    SELECT 
        customer_id,
        COUNT(session_id) AS total_sessions,
        AVG(pages_viewed) AS avg_pages_viewed,
        AVG(time_spent_seconds) AS avg_time_spent
    FROM web_logs
    GROUP BY customer_id
),

campaign_responses AS (
    SELECT 
        o.customer_id,
        COUNT(DISTINCT m.campaign_id) AS campaigns_responded,
        SUM(m.spend) AS campaign_spend
    FROM orders o
    JOIN marketing_campaigns m
	ON 
    CASE 
        WHEN o.channel = 'Web' THEN 'Google Ads'
        WHEN o.channel = 'Mobile App' THEN 'Instagram'
        WHEN o.channel = 'Store' THEN 'Email'
    END = m.channel
        
    GROUP BY o.customer_id
),

cohort_analysis AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
)

SELECT 
    c.customer_id,
    c.signup_date,
    
    p.total_orders,
    p.total_spent,
    p.avg_order_value,
    p.last_purchase_date,
    
    e.total_sessions,
    e.avg_pages_viewed,
    e.avg_time_spent,
    
    cr.campaigns_responded,
    cr.campaign_spend,
    
    ca.cohort_month

FROM customers c
LEFT JOIN purchase_history p ON c.customer_id = p.customer_id
LEFT JOIN engagement_metrics e ON c.customer_id = e.customer_id
LEFT JOIN campaign_responses cr ON c.customer_id = cr.customer_id
LEFT JOIN cohort_analysis ca ON c.customer_id = ca.customer_id;


SELECT * FROM customer_360_view