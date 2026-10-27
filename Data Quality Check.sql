-- Nulls
SELECT COUNT(*) AS null_keys
FROM orders_fact
WHERE customer_id IS NULL OR product_id IS NULL OR order_date IS NULL;

-- Duplicate line ids
SELECT order_line_id, COUNT(*)
FROM orders_fact
GROUP BY 1
HAVING COUNT(*) > 1;

-- Orphan customers
SELECT COUNT(*) AS orphan_customers
FROM orders_fact f
LEFT JOIN dim_customers d ON f.customer_id = d.customer_id
WHERE d.customer_id IS NULL;

-- Negative amounts
SELECT COUNT(*) AS negative_lines
FROM orders_fact
WHERE amount < 0 OR quantity < 0;

-- Amount identity: amount = SUM(price) + freight at line grain
-- (price is the mean unit price; quantity may be > 1)
SELECT COUNT(*) AS amount_mismatch
FROM orders_fact
WHERE ABS(amount - (price * quantity + freight)) > 0.05;

SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM orders_fact;
SELECT COUNT(DISTINCT order_id) FROM orders_fact;
SELECT * FROM analysis_params;
