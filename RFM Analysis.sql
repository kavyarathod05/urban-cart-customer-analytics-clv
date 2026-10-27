-- RFM on Olist
-- Recency / Monetary: NTILE 5
-- Frequency: rule-based because ~97% of buyers order once
-- analysis_date = MAX(order_date), not CURRENT_DATE

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
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        CASE WHEN frequency >= 3 THEN 5
             WHEN frequency  = 2 THEN 3
             ELSE 1 END AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
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

SELECT customer_segment, COUNT(*) FROM rfm_segmentation GROUP BY 1 ORDER BY 2 DESC;
