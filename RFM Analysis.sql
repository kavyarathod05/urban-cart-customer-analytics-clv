CREATE TABLE rfm_segmentationss AS
WITH rfm_base AS (
    SELECT 
        customer_id,
        (CURRENT_DATE - COALESCE(last_purchase_date, CURRENT_DATE)) AS recency,
        COALESCE(total_orders, 0) AS frequency,
        COALESCE(total_spent, 0) AS monetary
    FROM customer_360_view
),

rfm_scores AS (
    SELECT 
        customer_id,
        recency,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)

SELECT 
    customer_id,
    
    -- ✅ Add original RFM values
    recency,
    frequency,
    monetary,
    
    -- ✅ Scores
    r_score,
    f_score,
    m_score,

    -- ✅ Segment
    CASE 
        WHEN r_score = 5 AND f_score = 5 AND m_score = 5 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 4 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost Customers'
        ELSE 'Average Customers'
    END AS customer_segment

FROM rfm_scores;

select * from rfm_Segmentationss