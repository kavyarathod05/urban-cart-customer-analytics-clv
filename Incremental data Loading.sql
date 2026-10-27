-- Incremental load on order_date. Grain is order_line_id (not order_id).

CREATE TABLE IF NOT EXISTS load_tracker (
    table_name TEXT PRIMARY KEY,
    last_load_date DATE
);

INSERT INTO load_tracker VALUES ('orders', '2016-01-01')
ON CONFLICT (table_name) DO NOTHING;

INSERT INTO orders_fact (
    order_line_id, order_id, customer_id, product_id,
    order_date, quantity, price, freight, amount, payment_type, order_status
)
SELECT
    order_line_id, order_id, customer_id, product_id,
    order_date, quantity, price, freight, amount, payment_type, order_status
FROM orders
WHERE order_date > (
    SELECT last_load_date FROM load_tracker WHERE table_name = 'orders'
)
ON CONFLICT (order_line_id)
DO UPDATE SET
    quantity = EXCLUDED.quantity,
    amount   = EXCLUDED.amount,
    freight  = EXCLUDED.freight;

UPDATE load_tracker
SET last_load_date = (SELECT MAX(order_date) FROM orders)
WHERE table_name = 'orders';
