# Power BI — UrbanCart (Olist)

Power BI is a **required** deliverable alongside the Streamlit app. Both use the
same Olist warehouse in PostgreSQL.

| Item | Path |
|---|---|
| Project (open this) | [`UrbanCart_Olist.pbip`](UrbanCart_Olist.pbip) |
| DAX measures | [`measures.dax`](measures.dax) |
| Page layout (5 dashboards) | [`pages_spec.md`](pages_spec.md) |
| Import CSVs | `data/` (generated) |
| Legacy file | `../Urbancart_Dashboard.pbix` — **old synthetic schema; do not use** |

## Prerequisites

1. Warehouse loaded: `python setup_local.py` (from project root)
2. Power BI extract: `python powerbi/export_dataset.py`
3. Semantic model TMDL: `python powerbi/generate_semantic_model.py`
4. **Power BI Desktop** (Windows, or Windows VM / Cloud PC if you are on Mac)

`./run_local.sh` runs steps 1–2 automatically after the warehouse build.

## Option A — Open the PBIP (recommended)

1. Copy / sync this `powerbi/` folder to a Windows machine if needed.
2. Double-click **`UrbanCart_Olist.pbip`** (or open it from Power BI Desktop).
3. If prompted about the **Data Folder** parameter, set it to the absolute path of
   `powerbi/data` on that machine (forward slashes are fine).
4. **Home → Refresh** to load CSVs.
5. Build the five report pages using [`pages_spec.md`](pages_spec.md).
6. Paste any extra measures from [`measures.dax`](measures.dax).
7. **File → Save as** → `UrbanCart_Olist.pbix` next to this folder when you need a single-file hand-in.

## Option B — Live PostgreSQL connection

1. Power BI Desktop → **Get data → PostgreSQL database**
2. Server: `localhost` · Database: `urbancart`
3. Import tables / views:

   - `orders_fact`, `dim_customers`, `dim_products`, `dim_date`
   - `rfm_segmentation`, `clv_table`, `customer_metrics`
   - `cohort_retention`, `category_pairs`, `product_pairs`, `analysis_params`
   - Views: `monthly_kpis`, `state_revenue`, `category_performance`, `churn_risk`, `clv_segmentation`, `customer_360_view`

4. Create relationships as in `pages_spec.md`.
5. Add measures from `measures.dax`.
6. Build the five pages.

On Mac without Desktop: use a Windows VM, Cloud PC, or a lab Windows machine.
The semantic model + CSVs travel with the repo; only Desktop is required to author visuals.

## Five pages (same as Streamlit)

1. **Executive** — GMV, AOV, CLV, churn, monthly revenue, state, CLV mix  
2. **RFM** — segments, R×F matrix, monetary  
3. **Churn** — risk bands, revenue at risk  
4. **Cohorts** — retention heatmap (replaces Marketing Attribution; Olist has no ad spend)  
5. **Product** — category treemap + association rules  

Every card / chart formula is documented in Streamlit (hover **i**) and in the main project README.

## Dataset credit

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · CC BY-NC-SA 4.0
