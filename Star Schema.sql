CREATE TABLE dim_customers (
    customer_id INT PRIMARY KEY,
    signup_date DATE,
    gender TEXT,
	city TEXT,
	age INT
);

CREATE TABLE dim_products (
    product_id INT PRIMARY KEY,
    category TEXT,
    price NUMERIC,
    cost NUMERIC
);



CREATE TABLE dim_campaigns (
    campaign_id INT PRIMARY KEY,
    channel TEXT,
    spend NUMERIC,
    period DATE
);

CREATE TABLE dim_date (
    date_id DATE PRIMARY KEY,
    year INT,
    month INT,
    day INT,
    quarter INT
);

CREATE TABLE ORDERS_FACT (
    ORDER_ID INT PRIMARY KEY,
    CUSTOMER_ID INT,
    PRODUCT_ID INT,
    CAMPAIGN_ID INT,
    ORDER_DATE DATE,
    QUANTITY INT,
	CHANNEL VARCHAR,
    PRICE INT,
    AMOUNT INT
);


INSERT INTO dim_customers
SELECT DISTINCT customer_id, signup_date, gender, city, age
FROM customers;

INSERT INTO dim_products
SELECT DISTINCT product_id, category, price, cost
FROM products;

INSERT INTO dim_campaigns
SELECT DISTINCT campaign_id, channel, spend, period
FROM marketing_campaigns;

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
    order_date::DATE,
    quantity,
    channel,
    price,
    amount,
    campaign_id
FROM orders;

INSERT INTO dim_date (date_id, year, month, day, quarter)
SELECT DISTINCT
    order_date,
    EXTRACT(YEAR FROM order_date),
    EXTRACT(MONTH FROM order_date),
    EXTRACT(DAY FROM order_date),
    EXTRACT(QUARTER FROM order_date)
FROM orders;


select * from dim_customers;
select * from dim_products;
select * from dim_campaigns;
select * from orders_fact;
select * from dim_date;

---verify star schema 
SELECT 
    f.order_id,
    c.customer_id,
    p.product_id,
    d.year,
    f.amount
FROM orders_fact f
JOIN dim_customers c ON f.customer_id = c.customer_id
JOIN dim_products p ON f.product_id = p.product_id
JOIN dim_date d ON f.order_date = d.date_id
LIMIT 10;
