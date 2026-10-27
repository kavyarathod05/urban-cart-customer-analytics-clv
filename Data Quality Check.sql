---null check
SELECT *
FROM orders_fact
WHERE customer_id IS NULL
   OR product_id IS NULL
   OR order_date IS NULL;

---Duplicate Check
SELECT order_id, COUNT(*)
FROM orders_fact
GROUP BY order_id
HAVING COUNT(*) > 1;

--Referential Integrity Check
SELECT COUNT(*)
FROM orders_fact f
LEFT JOIN dim_customers d
ON f.customer_id = d.customer_id
WHERE d.customer_id IS NULL;

--Data type is check
SELECT *
FROM orders_fact
WHERE order_date IS NULL;

---Range check
SELECT *
FROM orders_fact
WHERE amount < 0 OR quantity < 0;

---Business Rule check
SELECT *
FROM orders_fact
WHERE amount != quantity * price;

--Add record count check
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM orders_fact;

