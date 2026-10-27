# Dataset

UrbanCart loads three tables built from the **Brazilian E-Commerce Public Dataset by Olist**.

- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- License: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- Window: Sep 2016 – Sep 2018

## Files

| File | Grain | Columns |
|---|---|---|
| `customers.csv` | person (`customer_unique_id`) | `customer_id`, `signup_date`, `city`, `state` |
| `products.csv` | product | `product_id`, `category`, `price` |
| `orders.csv` | order × product | `order_line_id`, `order_id`, `customer_id`, `product_id`, `order_date`, `quantity`, `price`, `freight`, `amount`, `payment_type`, `order_status` |

`signup_date` is the first kept order date. `amount` = line price + freight. Canceled and unavailable orders are dropped.

Raw Olist CSVs live in `raw/`. Rebuild the three files with:

```bash
python transform_olist.py
```

## Not in Olist — not in this project

Marketing campaigns, web sessions, gender, age, product cost, ad CAC / ROI.
