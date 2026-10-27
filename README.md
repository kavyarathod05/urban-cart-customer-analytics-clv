# UrbanCart — Customer Analytics & CLV

Omni-channel was the original brief. The live system is a **purchase analytics warehouse** on real Brazilian marketplace orders: RFM, historic CLV, inactivity churn, cohort retention, and market-basket rules.

Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0), Sep 2016 – Sep 2018.

## What is in the data

| Table | Grain | Notes |
|---|---|---|
| customers | person | `customer_unique_id` (not Olist’s per-order `customer_id`), city, state, signup = first order |
| products | SKU | English category, median line price |
| orders | order × product | quantity, price, freight, amount = price + freight, payment type |

Canceled / unavailable orders are excluded. There is **no** campaign spend, web log, gender, age, or product cost in Olist, so those objects are not in the warehouse or the dashboards.

## Pipeline

```
dataset/raw/ (Olist CSVs)
        ↓  transform_olist.py
dataset/{customers,products,orders}.csv
        ↓  setup_local.py
PostgreSQL star schema + analytics
        ├─→ streamlit run app.py          (live dashboards)
        └─→ powerbi/export_dataset.py     (Power BI Import CSVs + PBIP model)
```

**Power BI is mandatory.** Open [`powerbi/UrbanCart_Olist.pbip`](powerbi/UrbanCart_Olist.pbip) in Power BI Desktop after export. Full steps: [`powerbi/README.md`](powerbi/README.md). Page layout: [`powerbi/pages_spec.md`](powerbi/pages_spec.md). The old `Urbancart_Dashboard.pbix` targets the previous synthetic schema — use the new Olist PBIP instead.

Star: `dim_customers`, `dim_products`, `dim_date`, `orders_fact`.  
Clock: `analysis_params.analysis_date = MAX(order_date)` so recency is not computed against today’s calendar.

## Analytics

**RFM.** Recency and monetary scored with `NTILE(5)`. Frequency is 1 / 3 / 5 because most Olist buyers order once (quintiles would collapse).

```
R = analysis_date − last_order
F = COUNT DISTINCT order_id
M = Σ amount
```

**CLV (historic).**

```
AOV              = Σ amount / COUNT orders
lifespan_years   = MAX(lifespan_days, 1) / 365
purchase_freq    = orders / lifespan_years
CLV              = AOV × purchase_freq × lifespan_years
```

Bands (BRL): Low < 150, Medium < 500, High ≥ 500.

**Churn risk.** High if inactive > 180 days, Medium > 90, else Low. Rate = High / buyers.

**Cohorts.** `cohort_month = month of first order`. `retention(c,p) = active in period p / cohort size`. Replaces the old Marketing Attribution board (no ad spend in Olist).

**Association.** Basket = `order_id`.

```
Support(A,B)    = pair_orders / total_orders
Confidence(A→B) = pair_orders / orders_with_A
Lift(A,B)       = Support(A,B) / (Support(A) × Support(B))
```

## Dashboards

Hover the **i** under each number or chart for the formula.

1. **Executive** — GMV, orders, buyers, AOV, avg CLV, churn rate; monthly revenue; orders vs buyers; state mix; CLV donut  
2. **RFM** — segment headcount and GMV, R×F heatmap, monetary spread, summary table  
3. **Churn** — risk mix, GMV in each band, inactivity histogram, risk by acquisition year, high-value high-risk list  
4. **Cohorts** — repeat rate, retention heatmap, cohort size, revenue by months since first order  
5. **Product** — category treemap, top SKUs, units vs revenue, share over time, category and product rules  

## Run locally

```bash
brew install postgresql@16 python@3.12
brew services start postgresql@16
createdb urbancart

cd urban-cart-customer-analytics-clv
./run_local.sh
```

- Streamlit: http://localhost:8501  
- Power BI: open `powerbi/UrbanCart_Olist.pbip` in Desktop (Windows), then Refresh

If `dataset/*.csv` are missing:

```bash
# place Olist CSVs in dataset/raw/ then
python transform_olist.py
python setup_local.py
python powerbi/export_dataset.py
python powerbi/generate_semantic_model.py
streamlit run app.py
```

## Author

Kavya Rathod · [github.com/kavyarathod05](https://github.com/kavyarathod05)
