---- STEP 1: Generate product pairs
CREATE TABLE product_pairs AS
SELECT
    a.product_id AS product_a,
    b.product_id AS product_b,
    COUNT(*) AS pair_count
FROM orders_fact a
JOIN orders_fact b
    ON a.customer_id = b.customer_id
    AND a.product_id < b.product_id
GROUP BY a.product_id, b.product_id;


---- STEP 2: Product frequency
CREATE OR REPLACE VIEW product_frequency AS
SELECT
    product_id,
    COUNT(*) AS product_count
FROM orders_fact
GROUP BY product_id;


---- STEP 3: Final Association Rules (Support + Confidence + Lift)
CREATE TABLE association_rules AS
SELECT
    pp.product_a,
    pp.product_b,
    pp.pair_count,

    --- SUPPORT (fixed: decimal + division by zero)
    COALESCE(
        pp.pair_count * 1.0 /
        NULLIF((SELECT COUNT(DISTINCT order_id) FROM orders_fact), 0),
    0) AS support,

    -- CONFIDENCE (fixed)
    COALESCE(
        pp.pair_count * 1.0 / NULLIF(pfa.product_count, 0),
    0) AS confidence,

    -- LIFT (fixed)
    COALESCE(
        (pp.pair_count * 1.0 / NULLIF(pfa.product_count, 0)) /
        (NULLIF(pfb.product_count, 0) * 1.0 /
         NULLIF((SELECT COUNT(DISTINCT order_id) FROM orders_fact), 0)),
    0) AS lift

FROM product_pairs pp
JOIN product_frequency pfa
    ON pp.product_a = pfa.product_id
JOIN product_frequency pfb
    ON pp.product_b = pfb.product_id;


---- STEP 4: Get strong rules
SELECT *
FROM association_rules
WHERE confidence > 0.01
AND lift > 1
AND pair_count >= 2   -- optional but recommended
ORDER BY lift DESC
LIMIT 20;