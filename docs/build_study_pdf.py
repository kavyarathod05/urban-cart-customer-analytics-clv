#!/usr/bin/env python3
"""Capture Streamlit dashboard screenshots and build a study PDF.

Requires: Streamlit running on http://127.0.0.1:8501
  python docs/build_study_pdf.py
"""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
OUT_PDF = ROOT / "docs" / "UrbanCart_Olist_Dashboard_Study_Guide.pdf"
BASE = "http://127.0.0.1:8501"

TEAL = colors.HexColor("#1F6F78")
INK = colors.HexColor("#1F2A2E")
MUTED = colors.HexColor("#4A5559")
RULE = colors.HexColor("#E2DBD0")
CANVAS = colors.HexColor("#F7F3EC")
CLAY = colors.HexColor("#B8573E")

DASHBOARDS = [
    {
        "tab": "01 Executive",
        "file": "01_executive.png",
        "title": "01 — Executive Overview (Ledger)",
        "purpose": (
            "Board-level health check for the Olist-backed UrbanCart book: how much "
            "merchandise was sold, how many people bought, what a typical order is worth, "
            "how valuable buyers look on a lifetime basis, and how much of the base has "
            "gone quiet. Every number uses kept orders only (canceled / unavailable dropped)."
        ),
        "kpis": [
            {
                "name": "Gross GMV",
                "formula": "GMV = Σ (price + freight_value) = Σ orders_fact.amount",
                "detail": (
                    "Gross merchandise value across every kept order line. Amount is the "
                    "line’s mean unit price contribution plus freight allocated to that "
                    "line. This is the top-line money metric for the extract."
                ),
            },
            {
                "name": "Orders",
                "formula": "Orders = COUNT(DISTINCT order_id)",
                "detail": (
                    "Number of unique baskets. Multi-item orders still count as one order. "
                    "Analysis date for the book is MAX(order_date) = 2018-09-03."
                ),
            },
            {
                "name": "Buyers",
                "formula": "Buyers = COUNT(DISTINCT customer_id)",
                "detail": (
                    "People, not Olist’s per-order customer_id. We map to "
                    "customer_unique_id so RFM/CLV are not inflated."
                ),
            },
            {
                "name": "AOV",
                "formula": "AOV = GMV / Orders",
                "detail": "Average order value for the whole book — revenue per basket.",
            },
            {
                "name": "Avg CLV",
                "formula": "CLV = AOV_c × purchase_frequency_c × lifespan_years_c; then AVG(CLV)",
                "detail": (
                    "Mean of historic customer CLV. Lifespan is floored at 1 day so a "
                    "one-order buyer has CLV equal to that order (not zero)."
                ),
            },
            {
                "name": "Churn rate",
                "formula": "ChurnRate = COUNT(High Risk) / COUNT(Buyers)",
                "detail": (
                    "Share of buyers whose last order is more than 180 days before the "
                    "dataset’s last order date (not today’s calendar)."
                ),
            },
        ],
        "charts": [
            {
                "name": "Monthly revenue (area)",
                "formula": "Revenue_m = Σ amount  GROUP BY DATE_TRUNC('month', order_date)",
                "detail": (
                    "Time series of GMV by purchase month. Shows seasonality and growth "
                    "through 2016–2018. Canceled/unavailable orders are already excluded "
                    "upstream in transform_olist.py."
                ),
            },
            {
                "name": "Orders vs buyers (dual axis)",
                "formula": "Orders_m = COUNT DISTINCT order_id; Buyers_m = COUNT DISTINCT customer_id",
                "detail": (
                    "Bars = order volume; line = distinct people that month. When orders "
                    "rise faster than buyers, the same people are buying more often."
                ),
            },
            {
                "name": "Revenue by state — top 10 (bar)",
                "formula": "Revenue_s = Σ amount  GROUP BY customer_state",
                "detail": (
                    "Geographic concentration of GMV. State comes from the buyer’s shipping "
                    "state on their first kept order (dim_customers)."
                ),
            },
            {
                "name": "CLV mix (donut)",
                "formula": "Low: CLV < 150; Medium: 150 ≤ CLV < 500; High: CLV ≥ 500 (BRL)",
                "detail": (
                    "Share of buyers in each historic CLV band. Bands are tuned for Olist’s "
                    "BRL order scale (not the old synthetic INR 3k/9k cuts)."
                ),
            },
        ],
    },
    {
        "tab": "02 RFM",
        "file": "02_rfm.png",
        "title": "02 — RFM Segmentation (Who still buys)",
        "purpose": (
            "Behavioral segmentation on Recency, Frequency, and Monetary value. Recency "
            "and Monetary use NTILE(5). Frequency is rule-based (1 / 3 / 5) because ~97% "
            "of Olist buyers order only once — quintiles on frequency would collapse."
        ),
        "kpis": [
            {
                "name": "Segment headcount KPIs",
                "formula": "R = analysis_date − last_order; F = COUNT DISTINCT orders; M = Σ amount",
                "detail": (
                    "One KPI cell per RFM label with buyer count and GMV in that segment. "
                    "Labels: Champions, Loyal, New, Average, At Risk, Lost."
                ),
            },
        ],
        "charts": [
            {
                "name": "Segment headcount (horizontal bar)",
                "formula": (
                    "Champions: R≥4, F=5, M≥4; Loyal: R≥3, F≥3; New: R≥4, F=1; "
                    "At risk: R≤2, F≥3; Lost: R≤2, F=1, M≤2; else Average"
                ),
                "detail": (
                    "How many people sit in each RFM label. Champions are recent, repeat, "
                    "high-spend. New Customers are recent one-time buyers."
                ),
            },
            {
                "name": "Revenue by segment (bar)",
                "formula": "Revenue_seg = Σ monetary  GROUP BY customer_segment",
                "detail": (
                    "Where lifetime spend actually sits. A small Champions segment can "
                    "still hold meaningful GMV."
                ),
            },
            {
                "name": "R × F heatmap",
                "formula": "r_score = NTILE(5) ORDER BY recency DESC; f_score = 1|3|5 by order count",
                "detail": (
                    "Cell = buyer count for each (r_score, f_score). High R + high F is "
                    "the sweet spot; high R + F=1 are recent one-timers."
                ),
            },
            {
                "name": "Monetary spread by segment (box, log)",
                "formula": "monetary_c = Σ amount_c",
                "detail": (
                    "Distribution of lifetime spend inside each label. Log scale because "
                    "a few Champions dwarf Average / New customers."
                ),
            },
            {
                "name": "Segment table",
                "formula": "avg_recency = AVG(R); avg_frequency = AVG(F); GMV = Σ M",
                "detail": (
                    "Summary table: buyers, average days since last order, average order "
                    "count, and total monetary per segment — for targeting briefs."
                ),
            },
        ],
    },
    {
        "tab": "03 Churn",
        "file": "03_churn.png",
        "title": "03 — Churn Risk (Who went quiet)",
        "purpose": (
            "Inactivity-based churn proxy. Olist has no cancel/unsubscribe flag, so "
            "risk is defined from days since last purchase vs the extract’s last order "
            "date (2018-09-03)."
        ),
        "kpis": [
            {
                "name": "High / Medium / Low Risk counts",
                "formula": "days_inactive = analysis_date − last_order; High>180; Medium>90; else Low",
                "detail": (
                    "Each KPI shows headcount, share of base, and lifetime GMV sitting in "
                    "that band."
                ),
            },
        ],
        "charts": [
            {
                "name": "Risk mix (donut)",
                "formula": "ChurnRate = COUNT(High Risk) / COUNT(*)",
                "detail": (
                    "Share of the base in each inactivity band. High Risk is the working "
                    "definition of churn for this project."
                ),
            },
            {
                "name": "Revenue sitting in each band (bar)",
                "formula": "Revenue_risk = Σ total_spent  GROUP BY churn_segment",
                "detail": (
                    "Money at stake. High-risk revenue is lifetime GMV of people who have "
                    "not ordered in >180 days — prioritise win-back here."
                ),
            },
            {
                "name": "Days inactive (histogram)",
                "formula": "days_inactive_c = MAX(order_date)_dataset − MAX(order_date)_c",
                "detail": (
                    "Distribution of inactivity length. Long right tail = early buyers who "
                    "never returned."
                ),
            },
            {
                "name": "Risk by acquisition year (stacked)",
                "formula": "cohort_year = YEAR(MIN(order_date)); COUNT by (year, churn_segment)",
                "detail": (
                    "Older acquisition years have had more calendar time to go quiet, so "
                    "High Risk share rises for earlier cohorts."
                ),
            },
            {
                "name": "Highest-value high-risk buyers (table)",
                "formula": "WHERE churn_segment = 'High Risk' ORDER BY monetary DESC",
                "detail": (
                    "Target list: silent buyers ranked by lifetime spend, with RFM "
                    "frequency and segment for outreach prioritisation."
                ),
            },
        ],
    },
    {
        "tab": "04 Cohorts",
        "file": "04_cohorts.png",
        "title": "04 — Cohort Retention (Who came back)",
        "purpose": (
            "Replaces Marketing Attribution — Olist has no ad-spend table. Retention by "
            "first-purchase month is the honest view of whether new buyers ever return. "
            "Olist’s true repeat rate is low; most shoppers buy once."
        ),
        "kpis": [
            {
                "name": "Repeat rate",
                "formula": "RepeatRate = COUNT(orders ≥ 2) / COUNT(buyers)",
                "detail": "Share of people with at least two distinct orders in the extract.",
            },
            {
                "name": "Cohorts",
                "formula": "cohort_month = DATE_TRUNC('month', MIN(order_date))",
                "detail": "Number of first-order months with at least one kept buyer.",
            },
            {
                "name": "Largest cohort",
                "formula": "cohort_size = COUNT(*) GROUP BY cohort_month",
                "detail": "Headcount of the biggest acquisition month.",
            },
        ],
        "charts": [
            {
                "name": "Retention heatmap",
                "formula": "retention(c,p) = active buyers in cohort c at period p / cohort_size_c",
                "detail": (
                    "Rows = acquisition month; columns = months since first order (M0–M12). "
                    "Cell = % of that cohort who ordered again in that later month. Colour "
                    "scale capped near 8% so the faint repeat signal is visible. M0 is "
                    "always ~100% (acquisition)."
                ),
            },
            {
                "name": "Cohort size (bar)",
                "formula": "cohort_size = COUNT(*) GROUP BY first-order month",
                "detail": "How many new buyers arrived each month.",
            },
            {
                "name": "Revenue by cohort age (line)",
                "formula": "Revenue_p = Σ amount WHERE months_since_first_order = p",
                "detail": (
                    "All cohorts stacked: GMV booked in the nth month after first order. "
                    "Period 0 is acquisition spend; later periods are repeat spend — "
                    "usually much smaller on Olist."
                ),
            },
        ],
    },
    {
        "tab": "05 Product",
        "file": "05_product.png",
        "title": "05 — Product & Affinity (What sold together)",
        "purpose": (
            "Category mix, top SKUs, and market-basket association rules. Basket grain is "
            "order_id. English category names come from Olist’s translation table."
        ),
        "kpis": [
            {
                "name": "Categories / Top category / Category pairs",
                "formula": "COUNT DISTINCT category; argmax Σ amount; pair_orders ≥ 5",
                "detail": "Catalog breadth, highest-GMV category, and how many category pairs co-occur in ≥5 baskets.",
            },
        ],
        "charts": [
            {
                "name": "Revenue by category (treemap)",
                "formula": "Revenue_cat = Σ amount  GROUP BY category",
                "detail": "Area ∝ GMV. Quickly shows which English categories carry the book.",
            },
            {
                "name": "Top 15 products (bar)",
                "formula": "Revenue_p = Σ amount  GROUP BY product_id",
                "detail": (
                    "Highest-GMV product ids. Olist does not publish product titles — the "
                    "id is the analysis grain."
                ),
            },
            {
                "name": "Units vs revenue (scatter)",
                "formula": "x = Σ quantity; y = Σ amount; size = COUNT DISTINCT order_id",
                "detail": (
                    "Each point is a category. High units + low revenue = cheap volume; "
                    "high revenue + fewer units = premium mix."
                ),
            },
            {
                "name": "Category share over time (100% area)",
                "formula": "share_cat,m = Revenue_cat,m / Σ_cat Revenue_m",
                "detail": (
                    "Top six categories by total GMV plus Other. Stack sums to 100% of "
                    "that month’s revenue — mix shift over time."
                ),
            },
            {
                "name": "Category association rules (table)",
                "formula": (
                    "Support(A,B)=pair/all; Confidence(A→B)=pair/orders_with_A; "
                    "Lift=Support/(SupportA×SupportB)"
                ),
                "detail": (
                    "Market basket at category grain. Lift > 1 means the pair appears "
                    "together more than chance. Most Olist baskets are single-category, "
                    "so lift often sits near or below 1 — still useful for assortment."
                ),
            },
            {
                "name": "Product pairs (table)",
                "formula": "Same Support / Confidence / Lift on product_id where pair_orders ≥ 3",
                "detail": (
                    "Sparse at SKU grain; short high-signal list for concrete cross-sell."
                ),
            },
        ],
    },
]


def capture() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="networkidle", timeout=120_000)
        # Wait for Streamlit to finish running scripts
        page.wait_for_selector("[data-testid='stTabs']", timeout=120_000)
        time.sleep(3)

        for d in DASHBOARDS:
            tab_name = d["tab"]
            # Streamlit BaseWeb tabs
            tab = page.locator(f"[data-testid='stTab'][role='tab']:has-text('{tab_name}')").first
            tab.click()
            # Active tab panel is not inert; inactive ones are inert and fail visibility waits
            page.wait_for_selector(
                "[data-testid='stTabPanel']:not([inert])",
                timeout=90_000,
            )
            page.wait_for_timeout(3500)
            page.evaluate("window.scrollTo(0, 0)")
            # Measure full app height and screenshot the main block for this tab
            height = page.evaluate(
                """() => {
                    const main = document.querySelector('[data-testid="stMain"]')
                        || document.querySelector('[data-testid="stAppViewContainer"]')
                        || document.body;
                    return Math.max(main.scrollHeight, document.body.scrollHeight, 1400);
                }"""
            )
            page.set_viewport_size({"width": 1440, "height": min(int(height) + 100, 14000)})
            page.wait_for_timeout(2000)
            out = SHOTS / d["file"]
            page.locator("[data-testid='stMain']").first.screenshot(path=str(out), type="png")
            print(f"  captured {out.name} ({out.stat().st_size // 1024} KB)")
            page.set_viewport_size({"width": 1440, "height": 900})

        browser.close()


def styles():
    ss = getSampleStyleSheet()
    ss.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    ss.add(
        ParagraphStyle(
            name="CoverSub",
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            name="HDash",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=TEAL,
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            name="HChart",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="BodyJust",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Formula",
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            textColor=INK,
            backColor=colors.HexColor("#EFEAE2"),
            borderPadding=4,
            spaceBefore=3,
            spaceAfter=6,
            leftIndent=4,
            rightIndent=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Tiny",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MUTED,
        )
    )
    return ss


def footer_fn(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 7 * mm, "UrbanCart · Olist Dashboard Study Guide")
    canvas.drawRightString(A4[0] - 18 * mm, 7 * mm, f"Page {doc.page}")
    canvas.restoreState()


def add_shot(story, path: Path, caption: str, styles_map) -> None:
    if not path.exists():
        story.append(Paragraph(f"[Missing screenshot: {path.name}]", styles_map["BodyJust"]))
        return
    # Fit image to page width with max height
    max_w = A4[0] - 36 * mm
    max_h = A4[1] - 55 * mm
    img = Image(str(path))
    iw, ih = img.imageWidth, img.imageHeight
    scale = min(max_w / iw, max_h / ih, 1.0)
    img.drawWidth = iw * scale
    img.drawHeight = ih * scale
    story.append(img)
    story.append(Paragraph(caption, styles_map["Caption"]))


def build_pdf() -> None:
    ss = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="UrbanCart Olist Dashboard Study Guide",
        author="UrbanCart Analytics",
    )
    story = []

    # Cover
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("UrbanCart Analytics", ss["CoverTitle"]))
    story.append(Paragraph("Olist Dashboard Study Guide", ss["CoverTitle"]))
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "Exact screenshots of all five Streamlit dashboards<br/>"
            "with in-depth formulas and interpretation for every KPI and chart",
            ss["CoverSub"],
        )
    )
    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "Source: Brazilian E-Commerce Public Dataset by Olist (CC BY-NC-SA 4.0)<br/>"
            "Window: Sep 2016 – Sep 2018 · Currency: BRL<br/>"
            "Warehouse clock: analysis_date = MAX(order_date) = 2018-09-03<br/>"
            "Person key: customer_unique_id (not Olist per-order customer_id)",
            ss["CoverSub"],
        )
    )
    story.append(Spacer(1, 14 * mm))
    toc_rows = [[Paragraph("<b>Contents</b>", ss["HChart"]), ""]]
    for i, d in enumerate(DASHBOARDS, 1):
        toc_rows.append([Paragraph(d["title"], ss["BodyJust"]), Paragraph(f"Section {i}", ss["Tiny"])])
    toc = Table(toc_rows, colWidths=[120 * mm, 40 * mm])
    toc.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(toc)
    story.append(PageBreak())

    # How to read
    story.append(Paragraph("How to study this guide", ss["HDash"]))
    story.append(
        Paragraph(
            "Each section opens with a full-page screenshot of the live Streamlit tab, "
            "then documents every KPI and chart: what it shows, the exact formula used in "
            "SQL/Python, and how to interpret it for business data mining. Recency and "
            "churn always use the dataset’s last order date — never today’s calendar — "
            "otherwise every 2018 buyer would look churned.",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "Core CLV identity used across Executive and CLV bands:",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "AOV_c = Σ amount_c / COUNT(orders)_c<br/>"
            "lifespan_years_c = MAX(lifespan_days_c, 1) / 365<br/>"
            "purchase_frequency_c = orders_c / lifespan_years_c<br/>"
            "CLV_c = AOV_c × purchase_frequency_c × lifespan_years_c",
            ss["Formula"],
        )
    )
    story.append(PageBreak())

    for d in DASHBOARDS:
        story.append(Paragraph(d["title"], ss["HDash"]))
        story.append(Paragraph(d["purpose"], ss["BodyJust"]))
        story.append(Spacer(1, 3 * mm))
        add_shot(
            story,
            SHOTS / d["file"],
            f"Screenshot · Streamlit tab “{d['tab']}” · UrbanCart Olist",
            ss,
        )
        story.append(PageBreak())

        story.append(Paragraph(f"{d['title']} — detailed reference", ss["HDash"]))
        story.append(Paragraph("<b>KPIs</b>", ss["HChart"]))
        for k in d["kpis"]:
            block = [
                Paragraph(k["name"], ss["HChart"]),
                Paragraph(k["formula"].replace("\n", "<br/>"), ss["Formula"]),
                Paragraph(k["detail"], ss["BodyJust"]),
            ]
            story.append(KeepTogether(block))

        story.append(Paragraph("<b>Charts &amp; tables</b>", ss["HChart"]))
        for c in d["charts"]:
            block = [
                Paragraph(c["name"], ss["HChart"]),
                Paragraph(c["formula"].replace("\n", "<br/>"), ss["Formula"]),
                Paragraph(c["detail"], ss["BodyJust"]),
            ]
            story.append(KeepTogether(block))

        story.append(PageBreak())

    # Closing cheat sheet
    story.append(Paragraph("Quick formula cheat sheet", ss["HDash"]))
    cheats = [
        ["Topic", "Formula"],
        ["GMV", "Σ (price + freight) on kept lines"],
        ["AOV", "GMV / DISTINCT orders"],
        ["CLV", "AOV × (orders/lifespan_years) × lifespan_years"],
        ["RFM R", "analysis_date − last_order (days)"],
        ["RFM F", "1 if 1 order; 3 if 2; 5 if ≥3"],
        ["RFM M", "Σ amount"],
        ["Churn High", "days_inactive > 180"],
        ["Retention", "active_in_period_p / cohort_size"],
        ["Support(A,B)", "orders with A∧B / all orders"],
        ["Confidence(A→B)", "orders with A∧B / orders with A"],
        ["Lift(A,B)", "Support(A,B) / (Support(A)×Support(B))"],
    ]
    # Wrap cells
    wrapped = []
    for r, row in enumerate(cheats):
        wrapped.append(
            [
                Paragraph(f"<b>{row[0]}</b>" if r == 0 else row[0], ss["Tiny"]),
                Paragraph(f"<b>{row[1]}</b>" if r == 0 else row[1], ss["Tiny"]),
            ]
        )
    t = Table(wrapped, colWidths=[35 * mm, 130 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("BACKGROUND", (0, 1), (-1, -1), CANVAS),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "Repo: github.com/kavyarathod05/urban-cart-customer-analytics-clv · "
            "Live app: streamlit run app.py · Power BI: powerbi/UrbanCart_Olist.pbip",
            ss["CoverSub"],
        )
    )

    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    print(f"PDF → {OUT_PDF}")


def main() -> int:
    print("Capturing dashboards from", BASE)
    capture()
    print("Building PDF…")
    build_pdf()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
