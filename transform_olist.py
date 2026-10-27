#!/usr/bin/env python3
"""Transform raw Olist CSVs (dataset/raw/) into the UrbanCart source tables (dataset/).

Source: Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0)
        https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Outputs (dataset/):
    customers.csv  customer_id, signup_date, city, state
    products.csv   product_id, category, price
    orders.csv     order_line_id, order_id, customer_id, product_id, order_date,
                   quantity, price, freight, amount, payment_type, order_status

Rules
-----
* customer_id  = Olist `customer_unique_id` (the real person). Olist's own
                 `customer_id` is a per-order key and would break RFM / CLV.
* signup_date  = customer's first order purchase date (Olist has no signup table).
* One orders row per (order_id, product_id); quantity = number of identical
  item lines in that order; amount = SUM(price + freight_value).
* Cancelled / unavailable orders are excluded from all analytics tables.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "dataset" / "raw"
OUT = ROOT / "dataset"

EXCLUDED_STATUS = {"canceled", "unavailable"}


def main() -> None:
    print("Reading raw Olist files...")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    translation = pd.read_csv(RAW / "product_category_name_translation.csv")

    # ---- orders: attach the real person id, filter statuses -----------------
    orders = orders.merge(
        customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]],
        on="customer_id",
        how="left",
    )
    orders = orders[~orders["order_status"].isin(EXCLUDED_STATUS)].copy()
    orders["order_date"] = orders["order_purchase_timestamp"].dt.date

    # dominant payment type per order (highest paid value)
    pay = (
        payments.sort_values("payment_value", ascending=False)
        .drop_duplicates("order_id")[["order_id", "payment_type"]]
    )

    # ---- order lines: one row per (order, product) ---------------------------
    lines = (
        items.groupby(["order_id", "product_id"], as_index=False)
        .agg(
            quantity=("order_item_id", "count"),
            price=("price", "mean"),
            freight=("freight_value", "sum"),
            gross=("price", "sum"),
        )
    )
    lines["amount"] = (lines["gross"] + lines["freight"]).round(2)
    lines["price"] = lines["price"].round(2)
    lines["freight"] = lines["freight"].round(2)
    lines = lines.drop(columns="gross")

    lines = lines.merge(
        orders[["order_id", "customer_unique_id", "order_date", "order_status"]],
        on="order_id",
        how="inner",
    ).merge(pay, on="order_id", how="left")
    lines["payment_type"] = lines["payment_type"].fillna("not_defined")
    lines = lines.rename(columns={"customer_unique_id": "customer_id"})
    lines = lines.sort_values(["order_date", "order_id", "product_id"]).reset_index(drop=True)
    lines.insert(0, "order_line_id", range(1, len(lines) + 1))
    lines = lines[
        [
            "order_line_id",
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "price",
            "freight",
            "amount",
            "payment_type",
            "order_status",
        ]
    ]

    # ---- customers: one row per real person, signup = first order ------------
    first_order = (
        orders.sort_values("order_purchase_timestamp")
        .drop_duplicates("customer_unique_id")[
            ["customer_unique_id", "order_date", "customer_city", "customer_state"]
        ]
        .rename(
            columns={
                "customer_unique_id": "customer_id",
                "order_date": "signup_date",
                "customer_city": "city",
                "customer_state": "state",
            }
        )
    )
    first_order["city"] = first_order["city"].str.title()
    # only keep customers who have at least one kept order line
    cust = first_order[first_order["customer_id"].isin(lines["customer_id"])].reset_index(drop=True)

    # ---- products: English category + representative price -------------------
    prod = products[["product_id", "product_category_name"]].merge(
        translation, on="product_category_name", how="left"
    )
    prod["category"] = (
        prod["product_category_name_english"]
        .fillna(prod["product_category_name"])
        .fillna("unknown")
        .str.replace("_", " ")
        .str.title()
    )
    med_price = lines.groupby("product_id")["price"].median().rename("price").reset_index()
    prod = prod[["product_id", "category"]].merge(med_price, on="product_id", how="inner")
    prod["price"] = prod["price"].round(2)
    prod = prod.sort_values("product_id").reset_index(drop=True)

    # ---- write ---------------------------------------------------------------
    OUT.mkdir(exist_ok=True)
    cust.to_csv(OUT / "customers.csv", index=False)
    prod.to_csv(OUT / "products.csv", index=False)
    lines.to_csv(OUT / "orders.csv", index=False)

    print(
        f"  customers={len(cust):,}  products={len(prod):,}  order_lines={len(lines):,}  "
        f"orders={lines['order_id'].nunique():,}  "
        f"range={lines['order_date'].min()} → {lines['order_date'].max()}"
    )
    repeat = (lines.groupby("customer_id")["order_id"].nunique() > 1).mean()
    print(f"  repeat-buyer share={repeat:.2%}  gross revenue={lines['amount'].sum():,.2f} BRL")


if __name__ == "__main__":
    main()
