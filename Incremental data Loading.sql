---1.Indentify Incrematal column
---order_date

---2.create tracking table
CREATE TABLE load_tracker (
    table_name TEXT PRIMARY KEY,
    last_load_date DATE
);

---3.add intial value
SELECT MIN(order_date) FROM orders;

INSERT INTO load_tracker VALUES ('orders', '2022-01-01');

---4.load only new data
INSERT INTO orders_fact (
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    channel,
    price,
    amount,
    campaign_id
)
SELECT 
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    channel,
    price,
    amount,
    campaign_id
FROM orders
WHERE order_date > (
    SELECT last_load_date 
    FROM load_tracker 
    WHERE table_name = 'orders'
);

---Update tracker
UPDATE load_tracker
SET last_load_date = (SELECT MAX(order_date) FROM orders)
WHERE table_name = 'orders';


---Handle Duplicates
INSERT INTO orders_fact (
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    channel,
    price,
    amount,
    campaign_id
)
SELECT 
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    channel,
    price,
    amount,
    campaign_id
FROM orders
WHERE order_date > (
    SELECT last_load_date FROM load_tracker WHERE table_name = 'orders'
)
ON CONFLICT (order_id)
DO UPDATE SET
    quantity = EXCLUDED.quantity,
    amount = EXCLUDED.amount;

	

