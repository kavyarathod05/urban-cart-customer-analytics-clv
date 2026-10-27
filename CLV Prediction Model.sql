---check orders_fact data
select *
from orders_fact
limit 10;

---Calculate BAsic CUSTOMER metrices
CREATE TABLE CUSTOMER_METRICES AS
SELECT
CUSTOMER_ID,
COUNT(ORDER_ID)AS TOTAL_ORDERS,
SUM(AMOUNT) AS TOTAL_REVENUE,
AVG(AMOUNT) AS AVG_ORDER_VALUE,
MIN(ORDER_DATE) AS FIRST_PURCHASE,
MAX(ORDER_DATE) AS LAST_PURCHASE
FROM ORDERS_FACT
GROUP BY CUSTOMER_ID;

---CALCULATE CUSTOMER LIFESPAN
---calculate customer lifespan
---customer lifespan = difference between first and last purchase
CREATE OR REPLACE VIEW customer_lifespans AS
SELECT
    customer_id,
    total_orders,
    total_revenue,
    avg_order_value,
    first_purchase,
    last_purchase,

    (last_purchase - first_purchase) AS lifespan_days

FROM customer_metrices;

---CONVERT DAYS TO YEAR
SELECT
customer_id,
lifespan_days,
lifespan_days / 365 AS lifespan_years
FROM CUSTOMER_LIFESPANS;



------CALCULATE PURCHASE FREQUENCY
---purchase_frequency=orders per year
CREATE OR REPLACE VIEW purchase_frequency AS
SELECT
    customer_id,
    total_orders,
    lifespan_days,

    CASE 
        WHEN lifespan_days = 0 THEN total_orders
        ELSE total_orders / (lifespan_days / 365.0)
    END AS purchase_frequency

FROM customer_lifespans;

-----CALCULATE CLV
CREATE TABLE clv_table AS
SELECT
    cl.customer_id,

    COALESCE(cl.avg_order_value, 0) AS avg_order_value,
    COALESCE(pf.purchase_frequency, 0) AS purchase_frequency,

    COALESCE(cl.lifespan_days / 365.0, 0) AS lifespan_years,

    COALESCE(cl.avg_order_value, 0) *
    COALESCE(pf.purchase_frequency, 0) *
    COALESCE(cl.lifespan_days / 365.0, 0) AS clv

FROM customer_lifespans cl
LEFT JOIN purchase_frequency pf
ON cl.customer_id = pf.customer_id;



SELECT COUNT(*)
FROM customer_lifespans cl
LEFT JOIN purchase_frequency pf
ON cl.customer_id = pf.customer_id
WHERE pf.customer_id IS NULL;

SELECT *
FROM clv_table
WHERE clv IS NULL;

------CUSTOMER SEGMENTATION
CREATE OR REPLACE VIEW clv_segmentation AS
SELECT
    customer_id,
    clv,

    CASE
        WHEN clv < 3000 THEN 'Low Value'
        WHEN clv BETWEEN 3000 AND 9000 THEN 'Medium Value'
        ELSE 'High Value'
    END AS customer_segment

FROM clv_table;


select * from clv_segmentation
