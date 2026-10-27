#!/usr/bin/env python3
"""UrbanCart analytics — five Olist-backed dashboards with formula hover."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ui.components import (  # noqa: E402
    CLV_COLORS,
    INK,
    MUTED,
    RFM_COLORS,
    RISK_COLORS,
    TEAL,
    brl,
    chart_card,
    footer,
    inject_theme,
    kpi_band,
    lede,
    masthead,
    table_card,
)

DB_URL = os.getenv(
    "URBANCART_DB_URL",
    f"postgresql+psycopg2://{os.getenv('USER', 'postgres')}@localhost:5432/urbancart",
)

RFM_ORDER = [
    "Champions",
    "Loyal Customers",
    "New Customers",
    "Average Customers",
    "At Risk",
    "Lost Customers",
]
RISK_ORDER = ["High Risk", "Medium Risk", "Low Risk"]
CLV_ORDER = ["High Value", "Medium Value", "Low Value"]


@st.cache_resource
def get_engine():
    return create_engine(DB_URL)


@st.cache_data(ttl=120)
def read_sql(query: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


def fig_layout(fig: go.Figure, *, legend: bool = True) -> go.Figure:
    fig.update_layout(showlegend=legend, hovermode="closest")
    fig.update_traces(hovertemplate="%{x}<br>%{y}<extra></extra>", selector=dict(type="bar"))
    return fig


# ---------------------------------------------------------------------------
# 1. Executive
# ---------------------------------------------------------------------------

def page_executive() -> None:
    masthead(
        "Ledger",
        "01  /  Executive overview",
        [
            "UrbanCart  ·  Olist public orders",
            "Brazil  ·  Sep 2016 – Sep 2018",
        ],
    )
    lede(
        "A snapshot of the book: what the marketplace earned, who bought, "
        "and how much of the base is already silent."
    )

    k = read_sql(
        """
        SELECT
            (SELECT SUM(amount) FROM orders_fact) AS revenue,
            (SELECT COUNT(DISTINCT order_id) FROM orders_fact) AS orders,
            (SELECT COUNT(*) FROM dim_customers) AS customers,
            (SELECT AVG(clv) FROM clv_table) AS avg_clv,
            (SELECT COUNT(*) FILTER (WHERE churn_segment = 'High Risk')::numeric
                 / NULLIF(COUNT(*), 0)
             FROM churn_risk) AS churn_rate
        """
    ).iloc[0]
    aov = float(k.revenue) / float(k.orders)

    kpi_band(
        [
            {
                "label": "Gross GMV",
                "value": brl(float(k.revenue)),
                "sub": "price + freight, kept orders",
                "how": "Sum of line amount on every kept order line. Amount is item price plus freight.",
                "formula": "GMV = Σ (price + freight_value)",
                "source": "orders_fact.amount",
            },
            {
                "label": "Orders",
                "value": f"{int(k.orders):,}",
                "sub": "distinct order_id",
                "how": "Count of unique orders after dropping canceled and unavailable statuses.",
                "formula": "Orders = COUNT(DISTINCT order_id)",
                "source": "orders_fact",
            },
            {
                "label": "Buyers",
                "value": f"{int(k.customers):,}",
                "sub": "unique people (customer_unique_id)",
                "how": "Olist issues a new customer_id per order. We use customer_unique_id so one person is one row.",
                "formula": "Buyers = COUNT(DISTINCT customer_id)",
                "source": "dim_customers",
            },
            {
                "label": "AOV",
                "value": brl(aov),
                "sub": "revenue / orders",
                "how": "Average order value across the whole book.",
                "formula": "AOV = GMV / Orders",
                "source": "orders_fact",
            },
            {
                "label": "Avg CLV",
                "value": brl(float(k.avg_clv)),
                "sub": "historic, per buyer",
                "how": "Mean of customer-level CLV. One-order buyers get a 1-day floor so CLV equals that order.",
                "formula": "CLV = AOV × frequency × lifespan_years",
                "source": "clv_table",
            },
            {
                "label": "Churn rate",
                "value": f"{float(k.churn_rate)*100:.1f}%",
                "sub": "share High Risk (>180d)",
                "how": "Share of buyers whose last order is more than 180 days before the dataset’s last order date.",
                "formula": "Churn rate = HighRisk / Buyers",
                "source": "churn_risk",
            },
        ]
    )

    monthly = read_sql("SELECT * FROM monthly_kpis ORDER BY month")
    monthly["month"] = pd.to_datetime(monthly["month"])

    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["revenue"],
                fill="tozeroy",
                line=dict(color=TEAL, width=2),
                fillcolor="rgba(31,111,120,0.12)",
                name="Revenue",
                hovertemplate="%{x|%b %Y}<br>R$ %{y:,.0f}<extra></extra>",
            )
        )
        fig_layout(fig, legend=False)
        fig.update_yaxes(tickprefix="R$ ", separatethousands=True)
        chart_card(
            "Monthly revenue",
            fig,
            how="Gross merchandise value by purchase month. Canceled and unavailable orders are excluded.",
            formula="Revenue_m = Σ amount  GROUP BY month(order_date)",
            source="monthly_kpis ← orders_fact",
        )
    with right:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=monthly["month"],
                y=monthly["orders"],
                name="Orders",
                marker_color=TEAL,
                opacity=0.85,
                hovertemplate="%{x|%b %Y}<br>%{y:,} orders<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["customers"],
                name="Buyers",
                yaxis="y2",
                line=dict(color="#B8573E", width=2),
                hovertemplate="%{x|%b %Y}<br>%{y:,} buyers<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis=dict(title="Orders"),
            yaxis2=dict(title="Buyers", overlaying="y", side="right", showgrid=False),
            showlegend=True,
        )
        chart_card(
            "Orders vs buyers",
            fig,
            how="Order volume against distinct people purchasing that month. A gap means the same buyers placed multiple orders.",
            formula="Orders_m = COUNT DISTINCT order_id\nBuyers_m = COUNT DISTINCT customer_id",
            source="monthly_kpis",
        )

    st.write("")
    left, right = st.columns(2)
    with left:
        states = read_sql(
            "SELECT state, revenue, orders, customers FROM state_revenue ORDER BY revenue DESC LIMIT 10"
        )
        fig = px.bar(states.sort_values("revenue"), x="revenue", y="state", orientation="h")
        fig.update_traces(
            marker_color=TEAL,
            hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>",
        )
        fig.update_xaxes(tickprefix="R$ ")
        fig_layout(fig, legend=False)
        chart_card(
            "Revenue by state — top 10",
            fig,
            how="Where GMV concentrates. State is the buyer’s shipping state on their first kept order.",
            formula="Revenue_s = Σ amount  GROUP BY customer_state",
            source="state_revenue ← orders_fact ⋈ dim_customers",
        )
    with right:
        clv = read_sql(
            """
            SELECT customer_segment, COUNT(*) AS customers, ROUND(AVG(clv)::numeric, 2) AS avg_clv
            FROM clv_segmentation GROUP BY 1
            """
        )
        clv["customer_segment"] = pd.Categorical(clv["customer_segment"], CLV_ORDER, ordered=True)
        clv = clv.sort_values("customer_segment")
        fig = go.Figure(
            go.Pie(
                labels=clv["customer_segment"],
                values=clv["customers"],
                hole=0.62,
                marker=dict(colors=[CLV_COLORS[s] for s in clv["customer_segment"]]),
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,} buyers<extra></extra>",
            )
        )
        fig.update_layout(showlegend=True)
        chart_card(
            "CLV mix",
            fig,
            how="Buyers banded on historic CLV in BRL. Low < 150, Medium 150–500, High > 500. Bands follow Olist’s order scale, not the old INR cuts.",
            formula="Low: CLV < 150\nMedium: 150 ≤ CLV < 500\nHigh: CLV ≥ 500",
            source="clv_segmentation ← clv_table",
        )


# ---------------------------------------------------------------------------
# 2. RFM
# ---------------------------------------------------------------------------

def page_rfm() -> None:
    masthead(
        "Who still buys",
        "02  /  RFM segmentation",
        ["Recency · Frequency · Monetary", "Scores 1–5, analysis date = last order"],
    )
    lede(
        "Quintiles on recency and spend. Frequency is rule-based: almost every "
        "Olist buyer purchases once, so quintiles on frequency would collapse."
    )

    summary = read_sql(
        """
        SELECT customer_segment,
               COUNT(*) AS customers,
               ROUND(AVG(recency)::numeric, 1) AS avg_recency,
               ROUND(AVG(frequency)::numeric, 2) AS avg_frequency,
               SUM(monetary) AS total_monetary
        FROM rfm_segmentation
        GROUP BY 1
        """
    )
    summary["customer_segment"] = pd.Categorical(summary["customer_segment"], RFM_ORDER, ordered=True)
    summary = summary.sort_values("customer_segment")

    kpi_band(
        [
            {
                "label": row.customer_segment,
                "value": f"{int(row.customers):,}",
                "sub": f"{brl(float(row.total_monetary))} GMV",
                "how": "Headcount in this RFM label. Recency is days since last purchase vs the dataset’s last order date.",
                "formula": "R = analysis_date − last_order\nF = COUNT DISTINCT orders\nM = Σ amount",
                "source": "rfm_segmentation",
            }
            for _, row in summary.iterrows()
        ]
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            summary,
            x="customers",
            y="customer_segment",
            orientation="h",
            color="customer_segment",
            color_discrete_map=RFM_COLORS,
        )
        fig.update_traces(hovertemplate="%{y}<br>%{x:,} buyers<extra></extra>")
        fig.update_layout(showlegend=False)
        chart_card(
            "Segment headcount",
            fig,
            how="How many people sit in each RFM label. Champions are recent, repeat, high-spend.",
            formula="Champions: R≥4, F=5, M≥4\nLoyal: R≥3, F≥3\nNew: R≥4, F=1\nAt risk: R≤2, F≥3\nLost: R≤2, F=1, M≤2",
            source="rfm_segmentation",
        )
    with right:
        fig = px.bar(
            summary,
            x="customer_segment",
            y="total_monetary",
            color="customer_segment",
            color_discrete_map=RFM_COLORS,
        )
        fig.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickprefix="R$ ")
        chart_card(
            "Revenue by segment",
            fig,
            how="Sum of each buyer’s historic spend, rolled to the RFM label. Shows where money actually sits.",
            formula="Revenue_seg = Σ monetary  GROUP BY customer_segment",
            source="rfm_segmentation.monetary",
        )

    heat = read_sql(
        """
        SELECT r_score, f_score, COUNT(*) AS customers
        FROM rfm_segmentation
        GROUP BY 1, 2
        """
    )
    pivot = heat.pivot(index="f_score", columns="r_score", values="customers").fillna(0)
    pivot = pivot.reindex(index=[1, 3, 5], columns=[1, 2, 3, 4, 5], fill_value=0)
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"R{c}" for c in pivot.columns],
            y=[f"F{i}" for i in pivot.index],
            colorscale=[[0, "#F7F3EC"], [0.5, "#5B9AA1"], [1, TEAL]],
            hovertemplate="%{x} × %{y}<br>%{z:,} buyers<extra></extra>",
        )
    )
    chart_card(
        "R × F heatmap",
        fig,
        how="Cell count of buyers for each recency quintile and frequency rule-score. F is 1 (one order), 3 (two), or 5 (three or more).",
        formula="r_score = NTILE(5) ORDER BY recency DESC\nf_score = 1 if F=1; 3 if F=2; 5 if F≥3",
        source="rfm_segmentation",
        height=300,
    )

    money = read_sql("SELECT customer_segment, monetary FROM rfm_segmentation")
    money["customer_segment"] = pd.Categorical(money["customer_segment"], RFM_ORDER, ordered=True)
    fig = px.box(
        money,
        x="customer_segment",
        y="monetary",
        color="customer_segment",
        color_discrete_map=RFM_COLORS,
        points=False,
    )
    fig.update_layout(showlegend=False)
    fig.update_yaxes(tickprefix="R$ ", type="log")
    chart_card(
        "Monetary spread by segment",
        fig,
        how="Distribution of lifetime spend inside each label. Log scale because a few Champions dwarf the rest.",
        formula="monetary_c = Σ amount_c",
        source="rfm_segmentation.monetary",
        height=360,
    )

    table_card(
        "Segment table",
        how="One row per RFM label with headcount, typical recency, typical frequency, and total spend.",
        formula="avg_recency = AVG(analysis_date − last_order)\navg_frequency = AVG(order count)",
        source="rfm_segmentation",
    )
    show = summary.rename(
        columns={
            "customer_segment": "Segment",
            "customers": "Buyers",
            "avg_recency": "Avg recency (days)",
            "avg_frequency": "Avg frequency",
            "total_monetary": "GMV (BRL)",
        }
    )
    st.dataframe(show, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# 3. Churn
# ---------------------------------------------------------------------------

def page_churn() -> None:
    masthead(
        "Who went quiet",
        "03  /  Churn risk",
        ["Clock = last order in the extract", "High > 180 days  ·  Medium > 90"],
    )
    lede(
        "Inactivity from the dataset’s last purchase date — not today’s calendar, "
        "or every 2018 buyer would look lost."
    )

    mix = read_sql(
        """
        SELECT churn_segment,
               COUNT(*) AS customers,
               SUM(total_spent) AS revenue
        FROM churn_risk GROUP BY 1
        """
    )
    mix["churn_segment"] = pd.Categorical(mix["churn_segment"], RISK_ORDER, ordered=True)
    mix = mix.sort_values("churn_segment")
    total = int(mix["customers"].sum())

    kpi_band(
        [
            {
                "label": row.churn_segment,
                "value": f"{int(row.customers):,}",
                "sub": f"{int(row.customers)/total*100:.1f}% of base · {brl(float(row.revenue))}",
                "how": "Buyers whose days since last order fall in this inactivity band.",
                "formula": "days_inactive = analysis_date − last_order\nHigh > 180  ·  Medium > 90  ·  else Low",
                "source": "churn_risk",
            }
            for _, row in mix.iterrows()
        ]
    )

    left, right = st.columns(2)
    with left:
        fig = go.Figure(
            go.Pie(
                labels=mix["churn_segment"],
                values=mix["customers"],
                hole=0.62,
                marker=dict(colors=[RISK_COLORS[s] for s in mix["churn_segment"]]),
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,} buyers<extra></extra>",
            )
        )
        chart_card(
            "Risk mix",
            fig,
            how="Share of the base in each inactivity band. High risk is the working definition of churn here — there is no cancel-flag in Olist.",
            formula="ChurnRate = COUNT(High Risk) / COUNT(*)",
            source="churn_risk",
        )
    with right:
        fig = px.bar(
            mix,
            x="churn_segment",
            y="revenue",
            color="churn_segment",
            color_discrete_map=RISK_COLORS,
        )
        fig.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickprefix="R$ ")
        chart_card(
            "Revenue sitting in each band",
            fig,
            how="Lifetime GMV of buyers currently in that risk band. High-risk revenue is money that may not come back.",
            formula="Revenue_risk = Σ total_spent  GROUP BY churn_segment",
            source="churn_risk.total_spent",
        )

    hist = read_sql("SELECT days_inactive FROM churn_risk")
    fig = px.histogram(hist, x="days_inactive", nbins=40)
    fig.update_traces(marker_color=TEAL, hovertemplate="%{x} days<br>%{y:,} buyers<extra></extra>")
    fig.update_layout(showlegend=False, bargap=0.05)
    fig.update_xaxes(title="Days inactive")
    chart_card(
        "Days inactive",
        fig,
        how="How long since each buyer’s last order, measured from 2018-09-03 (last order in the extract).",
        formula="days_inactive_c = MAX(order_date)_dataset − MAX(order_date)_c",
        source="churn_risk ← customer_360_view, analysis_params",
        height=300,
    )

    tenure = read_sql(
        """
        SELECT EXTRACT(YEAR FROM first_purchase)::int AS cohort_year,
               churn_segment,
               COUNT(*) AS customers
        FROM churn_risk cr
        JOIN customer_metrics m USING (customer_id)
        GROUP BY 1, 2
        ORDER BY 1
        """
    )
    fig = px.bar(
        tenure,
        x="cohort_year",
        y="customers",
        color="churn_segment",
        color_discrete_map=RISK_COLORS,
        category_orders={"churn_segment": RISK_ORDER},
        barmode="stack",
    )
    fig.update_traces(hovertemplate="%{x}<br>%{y:,} buyers<extra></extra>")
    chart_card(
        "Risk by acquisition year",
        fig,
        how="When the buyer first purchased, vs current inactivity. Older cohorts have had more time to go quiet.",
        formula="cohort_year = YEAR(MIN(order_date))\nthen COUNT by (cohort_year, churn_segment)",
        source="churn_risk ⋈ customer_metrics",
    )

    table_card(
        "Highest-value high-risk buyers",
        how="High-risk buyers ranked by lifetime spend, with RFM frequency and recency for targeting.",
        formula="High Risk AND monetary DESC",
        source="churn_risk ⋈ rfm_segmentation",
    )
    top = read_sql(
        """
        SELECT cr.customer_id,
               cr.days_inactive,
               r.frequency,
               ROUND(r.monetary::numeric, 2) AS monetary,
               r.customer_segment AS rfm_segment
        FROM churn_risk cr
        JOIN rfm_segmentation r USING (customer_id)
        WHERE cr.churn_segment = 'High Risk'
        ORDER BY r.monetary DESC
        LIMIT 40
        """
    )
    st.dataframe(top, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# 4. Cohort retention
# ---------------------------------------------------------------------------

def page_cohort() -> None:
    masthead(
        "Who came back",
        "04  /  Cohort retention",
        ["Cohort = month of first order", "Period 0 is the acquisition month"],
    )
    lede(
        "Olist has no ad-spend table. Retention by first-purchase month is the "
        "honest substitute: it shows whether new buyers ever return."
    )

    repeat = read_sql(
        """
        SELECT
            COUNT(*) FILTER (WHERE total_orders >= 2)::numeric / COUNT(*) AS repeat_rate,
            COUNT(*) FILTER (WHERE total_orders >= 2) AS repeaters,
            COUNT(*) AS buyers
        FROM customer_metrics
        """
    ).iloc[0]
    sizes = read_sql(
        """
        SELECT DISTINCT ON (cohort_month) cohort_month, cohort_size
        FROM cohort_retention
        ORDER BY cohort_month, period_number
        """
    )

    kpi_band(
        [
            {
                "label": "Repeat rate",
                "value": f"{float(repeat.repeat_rate)*100:.1f}%",
                "sub": f"{int(repeat.repeaters):,} of {int(repeat.buyers):,} buyers",
                "how": "Share of people with at least two distinct orders. Olist’s true repeat rate is low; most shoppers buy once.",
                "formula": "RepeatRate = COUNT(orders ≥ 2) / COUNT(buyers)",
                "source": "customer_metrics",
            },
            {
                "label": "Cohorts",
                "value": f"{len(sizes)}",
                "sub": "first-order months",
                "how": "Number of acquisition months with at least one kept order.",
                "formula": "cohort_month = DATE_TRUNC('month', MIN(order_date))",
                "source": "cohort_retention",
            },
            {
                "label": "Largest cohort",
                "value": f"{int(sizes['cohort_size'].max()):,}",
                "sub": pd.to_datetime(sizes.loc[sizes["cohort_size"].idxmax(), "cohort_month"]).strftime("%b %Y"),
                "how": "Headcount of the biggest acquisition month.",
                "formula": "cohort_size = COUNT(*) GROUP BY cohort_month",
                "source": "cohort_retention",
            },
        ]
    )

    cr = read_sql("SELECT * FROM cohort_retention WHERE period_number <= 12")
    cr["cohort_month"] = pd.to_datetime(cr["cohort_month"])
    heat = cr.pivot(index="cohort_month", columns="period_number", values="retention_rate")
    heat = heat.sort_index()
    fig = go.Figure(
        go.Heatmap(
            z=heat.values * 100,
            x=[f"M{int(c)}" for c in heat.columns],
            y=[d.strftime("%Y-%m") for d in heat.index],
            colorscale=[[0, "#F7F3EC"], [0.35, "#D9A066"], [1, TEAL]],
            zmin=0,
            zmax=8,
            hovertemplate="Cohort %{y}<br>%{x}<br>%{z:.2f}% retained<extra></extra>",
            colorbar=dict(title="%"),
        )
    )
    chart_card(
        "Retention heatmap",
        fig,
        how="Rows are acquisition months. Columns are months since first order. Cell is the percent of that cohort who placed an order in that later month. Colour scale is capped at 8% so the faint repeat signal is visible.",
        formula="retention(c, p) = buyers in cohort c active in period p\n                         / buyers in cohort c",
        source="cohort_retention",
        height=480,
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(sizes, x="cohort_month", y="cohort_size")
        fig.update_traces(marker_color=TEAL, hovertemplate="%{x|%b %Y}<br>%{y:,} buyers<extra></extra>")
        fig.update_layout(showlegend=False)
        chart_card(
            "Cohort size",
            fig,
            how="How many new buyers arrived each month (first kept order).",
            formula="cohort_size = COUNT(*) GROUP BY DATE_TRUNC('month', first_order)",
            source="cohort_retention",
        )
    with right:
        aged = read_sql(
            """
            WITH cust_cohort AS (
                SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::date AS cohort_month
                FROM orders_fact GROUP BY customer_id
            )
            SELECT
                ((EXTRACT(YEAR  FROM f.order_date) - EXTRACT(YEAR  FROM c.cohort_month)) * 12
               + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM c.cohort_month)))::int AS period_number,
                SUM(f.amount) AS revenue
            FROM orders_fact f
            JOIN cust_cohort c USING (customer_id)
            WHERE ((EXTRACT(YEAR  FROM f.order_date) - EXTRACT(YEAR  FROM c.cohort_month)) * 12
                 + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM c.cohort_month))) BETWEEN 0 AND 12
            GROUP BY 1
            ORDER BY 1
            """
        )
        fig = px.line(aged, x="period_number", y="revenue", markers=True)
        fig.update_traces(line_color=TEAL, hovertemplate="M%{x}<br>R$ %{y:,.0f}<extra></extra>")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickprefix="R$ ")
        fig.update_xaxes(title="Months since first order")
        chart_card(
            "Revenue by cohort age",
            fig,
            how="All cohorts stacked: GMV booked in the nth month after a buyer’s first order. Period 0 is acquisition spend; later periods are repeat spend.",
            formula="Revenue_p = Σ amount WHERE months_since_first_order = p",
            source="orders_fact + first-order month",
        )


# ---------------------------------------------------------------------------
# 5. Product & affinity
# ---------------------------------------------------------------------------

def page_product() -> None:
    masthead(
        "What sold together",
        "05  /  Product & affinity",
        ["English category names", "Baskets = order_id"],
    )
    lede(
        "Category mix, the products that carry the book, and association rules "
        "on items that share an order."
    )

    cats = read_sql("SELECT * FROM category_performance ORDER BY revenue DESC")
    kpi_band(
        [
            {
                "label": "Categories",
                "value": f"{len(cats)}",
                "sub": "with at least one sale",
                "how": "Distinct English product categories present on kept order lines.",
                "formula": "COUNT(DISTINCT category)",
                "source": "category_performance",
            },
            {
                "label": "Top category",
                "value": str(cats.iloc[0]["category"]),
                "sub": brl(float(cats.iloc[0]["revenue"])),
                "how": "Category with the highest GMV (price + freight).",
                "formula": "argmax_category Σ amount",
                "source": "category_performance",
            },
            {
                "label": "Category pairs",
                "value": str(int(read_sql("SELECT COUNT(*) AS n FROM category_pairs").iloc[0]["n"])),
                "sub": "rules with ≥ 5 co-orders",
                "how": "How many category pairs appear together in at least five baskets.",
                "formula": "pair_orders ≥ 5",
                "source": "category_pairs",
            },
        ]
    )

    left, right = st.columns(2)
    with left:
        fig = px.treemap(
            cats,
            path=["category"],
            values="revenue",
            color="revenue",
            color_continuous_scale=[[0, "#E6EEEF"], [1, TEAL]],
        )
        fig.update_traces(hovertemplate="%{label}<br>R$ %{value:,.0f}<extra></extra>")
        fig.update_layout(coloraxis_showscale=False, margin=dict(t=8, l=0, r=0, b=0))
        chart_card(
            "Revenue by category",
            fig,
            how="Share of GMV by English product category. Area is proportional to revenue.",
            formula="Revenue_cat = Σ amount  GROUP BY category",
            source="category_performance",
            height=380,
        )
    with right:
        top_p = read_sql(
            """
            SELECT p.product_id, p.category, SUM(f.amount) AS revenue, SUM(f.quantity) AS units
            FROM orders_fact f JOIN dim_products p USING (product_id)
            GROUP BY 1, 2
            ORDER BY revenue DESC
            LIMIT 15
            """
        )
        top_p["label"] = top_p["product_id"].str[:8] + "…"
        fig = px.bar(top_p.sort_values("revenue"), x="revenue", y="label", orientation="h", color="category")
        fig.update_traces(hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>")
        fig.update_xaxes(tickprefix="R$ ")
        chart_card(
            "Top 15 products",
            fig,
            how="Highest-GMV product ids. Olist does not publish product titles — the id is the grain.",
            formula="Revenue_p = Σ amount  GROUP BY product_id",
            source="orders_fact ⋈ dim_products",
            height=380,
        )

    fig = px.scatter(
        cats,
        x="units",
        y="revenue",
        size="orders",
        color="category",
        hover_name="category",
        size_max=42,
    )
    fig.update_traces(hovertemplate="%{hovertext}<br>%{x:,} units<br>R$ %{y:,.0f}<extra></extra>")
    fig.update_yaxes(tickprefix="R$ ")
    fig.update_layout(showlegend=False)
    chart_card(
        "Units vs revenue",
        fig,
        how="Each point is a category. Size is distinct orders. High units with low revenue are cheap volume; the inverse is premium mix.",
        formula="x = Σ quantity    y = Σ amount    size = COUNT DISTINCT order_id",
        source="category_performance",
        height=360,
    )

    share = read_sql(
        """
        WITH monthly AS (
            SELECT DATE_TRUNC('month', f.order_date)::date AS month,
                   p.category,
                   SUM(f.amount) AS revenue
            FROM orders_fact f JOIN dim_products p USING (product_id)
            GROUP BY 1, 2
        ),
        top AS (
            SELECT category FROM category_performance ORDER BY revenue DESC LIMIT 6
        )
        SELECT m.month, COALESCE(t.category, 'Other') AS category, SUM(m.revenue) AS revenue
        FROM monthly m
        LEFT JOIN top t ON t.category = m.category
        GROUP BY 1, 2
        ORDER BY 1
        """
    )
    share["month"] = pd.to_datetime(share["month"])
    fig = px.area(share, x="month", y="revenue", color="category", groupnorm="percent")
    fig.update_traces(hovertemplate="%{x|%b %Y}<br>%{y:.1f}%<extra></extra>")
    fig.update_yaxes(ticksuffix="%")
    chart_card(
        "Category share over time",
        fig,
        how="Top six categories by total GMV, plus Other. Stack is 100% of that month’s revenue.",
        formula="share_cat,m = Revenue_cat,m / Σ_cat Revenue_m",
        source="orders_fact ⋈ dim_products",
        height=360,
    )

    table_card(
        "Category association rules",
        how="Market basket at category grain. Basket = order. Lift > 1 means the pair is bought together more than chance; most Olist baskets are single-category, so lift often sits below 1.",
        formula="Support(A,B) = orders with A and B / all orders\nConfidence(A→B) = orders with A and B / orders with A\nLift(A,B) = Support(A,B) / (Support(A)×Support(B))",
        source="category_pairs",
    )
    pairs = read_sql(
        """
        SELECT category_a, category_b, pair_orders, support, confidence_a_to_b, lift
        FROM category_pairs
        ORDER BY lift DESC, pair_orders DESC
        LIMIT 20
        """
    )
    st.dataframe(pairs, width="stretch", hide_index=True)

    table_card(
        "Product pairs (min. 3 co-orders)",
        how="Same rules at product id. Olist baskets are sparse at this grain, so the list is short and high-signal.",
        formula="Support / Confidence / Lift on (product_a, product_b) where pair_orders ≥ 3",
        source="product_pairs",
    )
    pp = read_sql(
        """
        SELECT product_a, category_a, product_b, category_b, pair_orders, lift, confidence_a_to_b
        FROM product_pairs
        ORDER BY lift DESC, pair_orders DESC
        LIMIT 20
        """
    )
    st.dataframe(pp, width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="UrbanCart · Olist",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_theme()

    try:
        params = read_sql("SELECT * FROM analysis_params").iloc[0]
    except Exception as exc:
        st.error(
            "Database is not ready. From this folder run:\n\n"
            "`python transform_olist.py`  then  `python setup_local.py`\n\n"
            f"{exc}"
        )
        st.stop()

    tabs = st.tabs(
        [
            "01  Executive",
            "02  RFM",
            "03  Churn",
            "04  Cohorts",
            "05  Product",
        ]
    )
    with tabs[0]:
        page_executive()
    with tabs[1]:
        page_rfm()
    with tabs[2]:
        page_churn()
    with tabs[3]:
        page_cohort()
    with tabs[4]:
        page_product()

    footer(
        "UrbanCart  ·  analysis date "
        + pd.to_datetime(params["analysis_date"]).strftime("%d %b %Y")
        + "  ·  Power BI: powerbi/UrbanCart_Olist.pbip",
        "Source: Olist Brazilian E-Commerce  ·  CC BY-NC-SA 4.0",
    )


if __name__ == "__main__":
    main()
