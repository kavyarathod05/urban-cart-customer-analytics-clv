# Power BI page build — five UrbanCart dashboards

Build these pages in Power BI Desktop after loading the Olist model
(Postgres **or** `powerbi/data` CSVs). Every visual maps to a formula already
used in Streamlit / SQL.

## Relationships (model)

| From | To | Key |
|---|---|---|
| `orders_fact` | `dim_customers` | `customer_id` |
| `orders_fact` | `dim_products` | `product_id` |
| `orders_fact` | `dim_date` | `order_date` → `date_id` |
| `rfm_segmentation` | `dim_customers` | `customer_id` |
| `clv_table` | `dim_customers` | `customer_id` |
| `pbi_churn_risk` | `dim_customers` | `customer_id` |
| `customer_metrics` | `dim_customers` | `customer_id` |

`cohort_retention`, `category_pairs`, `product_pairs`, `pbi_monthly_kpis`,
`pbi_state_revenue`, `pbi_category_performance` are self-contained fact tables
(no required relationship for their pages).

---

## Page 1 — Executive

| Visual | Fields / measures | Notes |
|---|---|---|
| Card | `[Gross GMV]` | Format currency BRL |
| Card | `[Orders]` | |
| Card | `[Buyers]` | |
| Card | `[AOV]` | |
| Card | `[Avg CLV]` | |
| Card | `[Churn Rate]` | % |
| Area chart | X: `pbi_monthly_kpis[month]` · Y: `revenue` | Monthly revenue |
| Line + clustered column | X: `month` · Col: `orders` · Line: `customers` | Orders vs buyers |
| Bar | Y: `pbi_state_revenue[state]` · X: `revenue` | Top 10 filter |
| Donut | Legend: `pbi_clv_segmentation[customer_segment]` · Values: Count | CLV mix |

## Page 2 — RFM

| Visual | Fields |
|---|---|
| Cards / multi-row | `rfm_segmentation[customer_segment]` + Count + `[RFM Monetary]` |
| Bar | Segment vs Count of customer_id |
| Bar | Segment vs Sum of monetary |
| Matrix / heatmap | Rows: `f_score` · Columns: `r_score` · Values: Count |
| Box / scatter | `monetary` by `customer_segment` |
| Table | segment, count, avg recency, avg frequency, sum monetary |

## Page 3 — Churn

| Visual | Fields |
|---|---|
| Cards | Count by `churn_segment`; `[Revenue At Risk]` |
| Donut | `churn_segment` |
| Bar | `churn_segment` × Sum `total_spent` |
| Histogram | `days_inactive` |
| Stacked column | Year of first purchase (from `customer_metrics[first_purchase]`) × `churn_segment` |
| Table | High Risk sorted by `total_spent` desc |

## Page 4 — Cohorts (replaces Marketing Attribution)

| Visual | Fields |
|---|---|
| Card | `[Repeat Rate]` |
| Matrix heatmap | Rows: `cohort_month` · Columns: `period_number` · Values: `retention_rate` (format %) |
| Column | `cohort_month` × `cohort_size` (use period_number = 0) |
| Line | Optional: revenue by months since first order (build from `orders_fact` if needed) |

## Page 5 — Product & affinity

| Visual | Fields |
|---|---|
| Treemap | `pbi_category_performance[category]` · Sum `revenue` |
| Bar | Top 15 products from `orders_fact` + `dim_products` |
| Scatter | X units · Y revenue · Size orders · `category` |
| Stacked area 100% | Monthly share by top categories |
| Table | `category_pairs` ordered by `lift` |
| Table | `product_pairs` ordered by `lift` |

---

## Theme

Match Streamlit: canvas `#F7F3EC`, ink `#1F2A2E`, accent teal `#1F6F78`, clay `#B8573E`.
Avoid default purple / Inter.
