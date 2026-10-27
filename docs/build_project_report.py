#!/usr/bin/env python3
"""Build UrbanCart project report PDF (team cover + work done + dashboard shots).

Uses existing screenshots in docs/screenshots/. Re-capture first if missing:
  python docs/build_study_pdf.py   # needs Streamlit on :8501
  python docs/build_project_report.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
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
OUT_PDF = ROOT / "docs" / "UrbanCart_Olist_Project_Report.pdf"

TEAL = colors.HexColor("#1F6F78")
INK = colors.HexColor("#1F2A2E")
MUTED = colors.HexColor("#4A5559")
RULE = colors.HexColor("#E2DBD0")
CANVAS = colors.HexColor("#F7F3EC")
CLAY = colors.HexColor("#B8573E")

TEAM = [
    ("Tushar Jawale", "2023IMG025"),
    ("Kavya Rathod", "2023IMG042"),
    ("Tarun Rai", "2023IMG049"),
    ("Tushar Tiwari", "2023IMG050"),
]

DASHBOARDS = [
    {
        "file": "01_executive.png",
        "title": "01 — Executive Overview (Ledger)",
        "what": (
            "Built as the board-level health check for the Olist-backed book. "
            "KPIs: Gross GMV, Orders, Buyers, AOV, Avg CLV, and Churn Rate. "
            "Charts: monthly revenue area, orders-vs-buyers dual series, top-10 "
            "revenue by Brazilian state, and CLV band mix (Low / Medium / High)."
        ),
        "findings": (
            "About R$ 15.74M GMV across ~98k orders and ~95k buyers; AOV ≈ R$ 160. "
            "Most historic CLV mass sits in the Low band; São Paulo (SP) dominates "
            "state revenue. Orders and buyers track closely month-to-month — "
            "repeat purchase is thin in this marketplace extract."
        ),
    },
    {
        "file": "02_rfm.png",
        "title": "02 — RFM Segmentation (Who still buys)",
        "what": (
            "Implemented classic RFM with Olist-aware scoring: Recency and Monetary "
            "via NTILE(5); Frequency as rule scores 1 / 3 / 5 because most buyers "
            "order once (quintiles would collapse). Segments: Champions, Loyal, "
            "New, Average, At Risk, Lost. Visuals: headcount bars, revenue by "
            "segment, R×F heatmap, monetary box plots, and a summary table."
        ),
        "findings": (
            "Headcount and GMV concentrate in New and Average customers. The R×F "
            "heatmap is heavy on F1 (single purchase) across all recency bins — "
            "the structural reason Frequency could not use NTILE."
        ),
    },
    {
        "file": "03_churn.png",
        "title": "03 — Churn Risk (Who went quiet)",
        "what": (
            "Defined inactivity churn against the dataset clock "
            "(analysis_date = MAX(order_date) = 2018-09-03), not today’s calendar: "
            "High > 180 days, Medium > 90, else Low. Built risk mix donut, revenue "
            "sitting in each band, days-inactive histogram, risk by acquisition "
            "year, and a high-value high-risk buyer list for re-engagement study."
        ),
        "findings": (
            "High Risk is ~60% of the base and carries the largest GMV share. "
            "Earlier acquisition years skew High Risk by construction of a fixed "
            "end date — an honest reading of a closed historical marketplace window."
        ),
    },
    {
        "file": "04_cohorts.png",
        "title": "04 — Cohorts & Retention (Who came back)",
        "what": (
            "Replaced the original Marketing Attribution board (no ad-spend table "
            "in Olist) with first-order month cohorts. Built retention heatmap "
            "(period 0 = acquisition month), cohort-size bars, and revenue by "
            "months since first order. KPIs: repeat rate, cohort count, largest cohort."
        ),
        "findings": (
            "Repeat rate ≈ 3%. Retention after M0 is very low; almost all revenue "
            "lands in period 0. Largest cohort around Nov 2017 (~7.2k buyers)."
        ),
    },
    {
        "file": "05_product.png",
        "title": "05 — Product & Affinity (What sold together)",
        "what": (
            "Category treemap, top SKUs by revenue, units-vs-revenue bubble chart, "
            "category share over time, plus association rules at category and "
            "product grain (Support / Confidence / Lift on shared order_id baskets)."
        ),
        "findings": (
            "Health Beauty leads category revenue. Many baskets are single-category, "
            "so lift often sits near or below 1 — still useful for assortment "
            "hypotheses. Product-pair rules are sparse but high-signal where they appear."
        ),
    },
]


def styles():
    ss = getSampleStyleSheet()
    ss.add(
        ParagraphStyle(
            name="CoverKicker",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=TEAL,
            alignment=TA_CENTER,
            spaceAfter=8,
            tracking=1,
        )
    )
    ss.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=10,
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
            name="Section",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=TEAL,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            name="SubHead",
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
            leading=13.5,
            textColor=MUTED,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            name="BodyLeft",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Formula",
            fontName="Courier",
            fontSize=8.2,
            leading=11,
            textColor=INK,
            backColor=colors.HexColor("#EFEAE2"),
            borderPadding=4,
            spaceBefore=2,
            spaceAfter=6,
            leftIndent=3,
            rightIndent=3,
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
            spaceBefore=3,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            name="TeamName",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=INK,
            alignment=TA_CENTER,
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
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        18 * mm,
        7 * mm,
        "UrbanCart · Olist Customer Analytics & CLV · Project Report",
    )
    canvas.drawRightString(A4[0] - 18 * mm, 7 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, A4[0], 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        A4[0] / 2,
        7 * mm,
        "Source: Olist Brazilian E-Commerce · CC BY-NC-SA 4.0 · analysis date 03 Sep 2018",
    )
    canvas.restoreState()


def fit_image(path: Path, max_w: float, max_h: float) -> Image:
    img = Image(str(path))
    iw, ih = img.imageWidth, img.imageHeight
    scale = min(max_w / iw, max_h / ih)
    img.drawWidth = iw * scale
    img.drawHeight = ih * scale
    return img


def bullet(items: list[str], style) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=8, value="•") for t in items],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        bulletFontName="Helvetica",
        bulletFontSize=9,
        bulletColor=TEAL,
    )


def build() -> Path:
    missing = [d["file"] for d in DASHBOARDS if not (SHOTS / d["file"]).exists()]
    if missing:
        raise SystemExit(
            f"Missing screenshots: {missing}. Run docs/build_study_pdf.py with Streamlit up first."
        )

    ss = styles()
    story: list = []

    # —— Cover ——
    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph("PROJECT REPORT", ss["CoverKicker"]))
    story.append(
        Paragraph(
            "UrbanCart — Customer Analytics<br/>&amp; Customer Lifetime Value",
            ss["CoverTitle"],
        )
    )
    story.append(
        Paragraph(
            "Purchase analytics warehouse on the Olist Brazilian E-Commerce dataset<br/>"
            "RFM · Historic CLV · Churn · Cohort Retention · Market Basket",
            ss["CoverSub"],
        )
    )
    story.append(Spacer(1, 10 * mm))

    team_rows = [
        [
            Paragraph("<b>Name</b>", ss["Tiny"]),
            Paragraph("<b>Roll Number</b>", ss["Tiny"]),
        ]
    ]
    for name, roll in TEAM:
        team_rows.append(
            [
                Paragraph(name, ss["TeamName"]),
                Paragraph(roll, ss["TeamName"]),
            ]
        )
    team_tbl = Table(team_rows, colWidths=[95 * mm, 55 * mm])
    team_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CANVAS]),
                ("BOX", (0, 0), (-1, -1), 0.6, TEAL),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(Paragraph("Prepared by", ss["CoverSub"]))
    story.append(Spacer(1, 3 * mm))
    story.append(team_tbl)
    story.append(Spacer(1, 12 * mm))
    story.append(
        Paragraph(
            "Stack: PostgreSQL star schema · Streamlit + Plotly dashboards · "
            "Power BI (PBIP) semantic model<br/>"
            "Repository: github.com/kavyarathod05/urban-cart-customer-analytics-clv",
            ss["CoverSub"],
        )
    )
    story.append(PageBreak())

    # —— 1. Objective ——
    story.append(Paragraph("1. Objective", ss["Section"]))
    story.append(
        Paragraph(
            "Build an end-to-end customer analytics system for an e-commerce book: "
            "clean transactional data, a dimensional warehouse, RFM and historic CLV, "
            "inactivity-based churn, cohort retention, association rules, and five "
            "interactive dashboards — with Power BI as a mandatory second presentation "
            "layer. The original brief assumed omni-channel marketing data (campaigns, "
            "web logs, demographics, product cost). Those fields do not exist in a "
            "reliable public match, so the team selected the best real public dataset "
            "and redesigned scope around what the data can honestly support.",
            ss["BodyJust"],
        )
    )

    # —— 2. What we did ——
    story.append(Paragraph("2. What We Did", ss["Section"]))
    story.append(Paragraph("2.1 Dataset decision", ss["SubHead"]))
    story.append(
        Paragraph(
            "After comparing synthetic multi-table demos with real public sources, "
            "we standardised on the <b>Brazilian E-Commerce Public Dataset by Olist</b> "
            "(Kaggle, CC BY-NC-SA 4.0; orders Sep 2016 – Sep 2018). It supplies "
            "customers, orders, items, products, payments, and category translations — "
            "enough for RFM, CLV, churn, cohorts, and baskets. We explicitly "
            "<b>removed</b> campaign ROI, web-session funnels, gender/age, and "
            "cost/margin objects that Olist does not contain, rather than inventing them.",
            ss["BodyJust"],
        )
    )

    story.append(Paragraph("2.2 ETL and warehouse", ss["SubHead"]))
    story.append(
        Paragraph(
            "Pipeline we implemented:",
            ss["BodyLeft"],
        )
    )
    story.append(
        bullet(
            [
                "<b>transform_olist.py</b> — join Olist CSVs into clean "
                "<font face='Courier'>customers / products / orders</font> extracts; "
                "map people to <font face='Courier'>customer_unique_id</font>; drop "
                "canceled/unavailable orders; amount = price + freight.",
                "<b>setup_local.py</b> — load PostgreSQL star schema "
                "(<font face='Courier'>dim_customers</font>, "
                "<font face='Courier'>dim_products</font>, "
                "<font face='Courier'>dim_date</font>, "
                "<font face='Courier'>orders_fact</font>) plus analytics views/tables "
                "for RFM, CLV, churn, cohorts, and association rules.",
                "<b>analysis_params.analysis_date</b> = "
                "<font face='Courier'>MAX(order_date)</font> (2018-09-03) so "
                "recency and churn are measured against the book’s last day, "
                "not the machine’s calendar.",
            ],
            ss["BodyLeft"],
        )
    )

    story.append(Paragraph("2.3 Analytics models", ss["SubHead"]))
    story.append(
        Paragraph(
            "<b>RFM.</b> R = analysis_date − last_order; F = COUNT DISTINCT order_id; "
            "M = Σ amount. R and M scored with NTILE(5); F scored 1/3/5 by rule.",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "CLV = AOV × purchase_frequency × lifespan_years<br/>"
            "Bands (BRL): Low &lt; 150 · Medium &lt; 500 · High ≥ 500",
            ss["Formula"],
        )
    )
    story.append(
        Paragraph(
            "<b>Churn.</b> High if inactive &gt; 180 days, Medium &gt; 90, else Low. "
            "Rate = High / buyers.",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "<b>Cohorts.</b> Cohort = month of first order; "
            "retention(c,p) = active in period p / cohort size. This board replaces "
            "marketing attribution (no ad spend in Olist).",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "Support(A,B) = pair_orders / total_orders<br/>"
            "Confidence(A→B) = pair_orders / orders_with_A<br/>"
            "Lift(A,B) = Support(A,B) / (Support(A) × Support(B))",
            ss["Formula"],
        )
    )

    story.append(Paragraph("2.4 Dashboards and Power BI", ss["SubHead"]))
    story.append(
        bullet(
            [
                "<b>Streamlit + Plotly</b> (<font face='Courier'>app.py</font>) — five "
                "tabs with formula hover tips on every KPI and chart; custom theme "
                "(non-generic UI); Kaggle dataset link in the masthead.",
                "<b>Power BI</b> mandatory deliverable — "
                "<font face='Courier'>powerbi/export_dataset.py</font>, "
                "TMDL semantic model, "
                "<font face='Courier'>UrbanCart_Olist.pbip</font>, measures and "
                "page specification for Desktop (Windows).",
                "<b>Study guide PDF</b> — full-tab screenshots plus per-graph formulas "
                "for revision (<font face='Courier'>UrbanCart_Olist_Dashboard_Study_Guide.pdf</font>).",
            ],
            ss["BodyLeft"],
        )
    )
    story.append(PageBreak())

    # —— 3. Deliverables summary table ——
    story.append(Paragraph("3. Deliverables Summary", ss["Section"]))
    rows = [
        [
            Paragraph("<b>Deliverable</b>", ss["Tiny"]),
            Paragraph("<b>What it contains</b>", ss["Tiny"]),
        ],
        [
            Paragraph("PostgreSQL warehouse", ss["BodyLeft"]),
            Paragraph("Star schema + RFM / CLV / churn / cohort / association objects", ss["BodyLeft"]),
        ],
        [
            Paragraph("Streamlit app (5 tabs)", ss["BodyLeft"]),
            Paragraph("Executive, RFM, Churn, Cohorts, Product — live interactive views", ss["BodyLeft"]),
        ],
        [
            Paragraph("Power BI PBIP", ss["BodyLeft"]),
            Paragraph("Import CSVs, semantic model, DAX measures, page layout spec", ss["BodyLeft"]),
        ],
        [
            Paragraph("SQL scripts", ss["BodyLeft"]),
            Paragraph("RFM, CLV, star schema, DQ, incremental load, association, etc.", ss["BodyLeft"]),
        ],
        [
            Paragraph("Documentation", ss["BodyLeft"]),
            Paragraph("README, Power BI README, study guide PDF, this project report", ss["BodyLeft"]),
        ],
    ]
    t = Table(rows, colWidths=[48 * mm, 120 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CANVAS]),
                ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            "The following pages attach the exact dashboard screenshots from the "
            "live Streamlit app and describe what each board does and what the "
            "visuals show.",
            ss["BodyJust"],
        )
    )
    story.append(PageBreak())

    # —— 4. Dashboards with screenshots ——
    story.append(Paragraph("4. Dashboards — Screenshots &amp; Work Done", ss["Section"]))
    story.append(
        Paragraph(
            "Each figure is a full-tab capture of the Streamlit UI (analysis date "
            "03 Sep 2018). Formulas appear as hover tips in the live app; key "
            "interpretations are summarised under each shot.",
            ss["BodyJust"],
        )
    )

    max_w = A4[0] - 36 * mm
    max_h = 145 * mm

    for i, d in enumerate(DASHBOARDS, start=1):
        block = []
        block.append(Paragraph(f"4.{i} {d['title']}", ss["SubHead"]))
        block.append(Paragraph(f"<b>What we built.</b> {d['what']}", ss["BodyJust"]))
        block.append(Paragraph(f"<b>What the board shows.</b> {d['findings']}", ss["BodyJust"]))
        img_path = SHOTS / d["file"]
        block.append(fit_image(img_path, max_w, max_h))
        block.append(
            Paragraph(
                f"Figure 4.{i} — {d['title']} (Streamlit · Olist)",
                ss["Caption"],
            )
        )
        story.append(KeepTogether(block))
        if i < len(DASHBOARDS):
            story.append(PageBreak())

    story.append(PageBreak())

    # —— 5. Key outcomes ——
    story.append(Paragraph("5. Key Outcomes", ss["Section"]))
    story.append(
        bullet(
            [
                "Replaced synthetic / incomplete omni-channel assumptions with a "
                "real, citable public marketplace dataset and a scope that matches it.",
                "Delivered a reproducible ETL → Postgres → analytics → Streamlit + "
                "Power BI path, with analysis_date pinned to the data.",
                "Five coherent dashboards covering ledger health, RFM, churn, "
                "retention, and product affinity — each with transparent formulas.",
                "Documented findings that matter for study and defence: low repeat "
                "rate (~3%), High Risk majority by the fixed end date, SP-led "
                "geography, and sparse but interpretable association rules.",
            ],
            ss["BodyLeft"],
        )
    )

    story.append(Paragraph("6. How to Re-run", ss["Section"]))
    story.append(
        Paragraph(
            "Install PostgreSQL and Python 3.12, create database "
            "<font face='Courier'>urbancart</font>, place Olist CSVs under "
            "<font face='Courier'>dataset/raw/</font>, then:",
            ss["BodyJust"],
        )
    )
    story.append(
        Paragraph(
            "python transform_olist.py<br/>"
            "python setup_local.py<br/>"
            "streamlit run app.py<br/>"
            "python powerbi/export_dataset.py<br/>"
            "python powerbi/generate_semantic_model.py",
            ss["Formula"],
        )
    )
    story.append(
        Paragraph(
            "Open <font face='Courier'>powerbi/UrbanCart_Olist.pbip</font> in Power BI "
            "Desktop (Windows) and Refresh. Rebuild this report after re-capturing "
            "shots: <font face='Courier'>python docs/build_project_report.py</font>.",
            ss["BodyJust"],
        )
    )

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Team", ss["Section"]))
    for name, roll in TEAM:
        story.append(Paragraph(f"{name} ({roll})", ss["BodyLeft"]))

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="UrbanCart Olist — Project Report",
        author="Tushar Jawale · Kavya Rathod · Tarun Rai · Tushar Tiwari",
    )
    doc.build(story, onFirstPage=cover_footer, onLaterPages=footer_fn)
    return OUT_PDF


if __name__ == "__main__":
    path = build()
    print(f"PDF → {path} ({path.stat().st_size // 1024} KB)")
