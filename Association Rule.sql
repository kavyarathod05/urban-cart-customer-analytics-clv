-- Market basket. Basket = order_id.
-- Support(A,B)    = pair_orders / total_orders
-- Confidence(A→B) = pair_orders / orders_with_A
-- Lift(A,B)       = Support(A,B) / (Support(A) × Support(B))

SELECT category_a, category_b, pair_orders, support, confidence_a_to_b, lift
FROM category_pairs
ORDER BY lift DESC, pair_orders DESC
LIMIT 20;

SELECT product_a, category_a, product_b, category_b, pair_orders, lift
FROM product_pairs
ORDER BY lift DESC, pair_orders DESC
LIMIT 20;
