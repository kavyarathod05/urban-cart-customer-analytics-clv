"""Presentation helpers: theme, Plotly template, KPI band, chart card with formula hover."""

from __future__ import annotations

import html
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

INK = "#1F2A2E"
INK2 = "#4A5559"
MUTED = "#8A8F94"
RULE = "#E2DBD0"
CANVAS = "#F7F3EC"
TEAL = "#1F6F78"
CLAY = "#B8573E"
SAND = "#D9A066"

PALETTE = [TEAL, CLAY, SAND, "#5B8C8F", "#7A6A5B", "#A8B4B7", "#3E4F53"]
SEQ_TEAL = [[0, "#E6EEEF"], [0.5, "#5B9AA1"], [1, TEAL]]
RISK_COLORS = {"High Risk": CLAY, "Medium Risk": SAND, "Low Risk": TEAL}
CLV_COLORS = {"High Value": TEAL, "Medium Value": SAND, "Low Value": "#A8B4B7"}
RFM_COLORS = {
    "Champions": TEAL,
    "Loyal Customers": "#5B8C8F",
    "New Customers": SAND,
    "Average Customers": "#A8B4B7",
    "At Risk": CLAY,
    "Lost Customers": "#7A6A5B",
}


def inject_theme() -> None:
    css = (Path(__file__).parent / "theme.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", color=INK2, size=12),
        title=dict(text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE,
        margin=dict(l=8, r=8, t=18, b=8),
        xaxis=dict(showgrid=False, linecolor=RULE, tickcolor=RULE, zeroline=False),
        yaxis=dict(gridcolor=RULE, griddash="dot", linecolor="rgba(0,0,0,0)", zeroline=False),
        legend=dict(orientation="h", y=-0.18, x=0, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        hoverlabel=dict(bgcolor=INK, font=dict(color="#F2EEE7", family="IBM Plex Sans"), bordercolor=INK),
    )
    pio.templates["urbancart"] = tpl
    pio.templates.default = "urbancart"


def _tip(title: str, how: str, formula: str, source: str, *, place: str = "right") -> str:
    """place: 'right' opens tip to the right of the icon (use for left KPIs);
    'left' opens tip to the left (use for right-edge KPIs / chart headers)."""
    side = "uc-tip-right" if place == "right" else "uc-tip-left"
    return (
        f'<span class="uc-info" tabindex="0"><span class="uc-i" aria-hidden="true">i</span>'
        f'<span class="uc-tip {side}" role="tooltip">'
        f'<div class="uc-tip-h">How {html.escape(title)} is calculated</div>'
        f'<div class="uc-tip-body">{html.escape(how)}</div>'
        f"<code>{html.escape(formula)}</code>"
        f'<div class="uc-tip-src">Source · {html.escape(source)}</div>'
        "</span></span>"
    )


OLIST_DATASET_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"


def masthead(title: str, kicker: str, meta_lines: list[str]) -> None:
    meta = "<br>".join(meta_lines)
    st.markdown(
        f'<div class="uc-masthead"><div><div class="uc-kicker">{kicker}</div>'
        f"<h1>{title}</h1></div>"
        f'<div class="uc-meta">{meta}'
        f'<br><a class="uc-dataset-link" href="{OLIST_DATASET_URL}" target="_blank" rel="noopener noreferrer">'
        f"Olist dataset on Kaggle ↗</a></div></div>",
        unsafe_allow_html=True,
    )


def lede(text: str) -> None:
    st.markdown(f'<p class="uc-lede">{text}</p>', unsafe_allow_html=True)


def kpi_band(items: list[dict]) -> None:
    """items: {label, value, sub, how, formula, source}

    Left-half KPIs open the tip to the right so they stay on screen;
    right-half KPIs open to the left.
    """
    n = len(items)
    split = max(1, (n + 1) // 2)
    cells = []
    for i, it in enumerate(items):
        place = "right" if i < split else "left"
        tip = _tip(
            it["label"],
            it["how"],
            it["formula"],
            it.get("source", "orders_fact"),
            place=place,
        )
        cells.append(
            '<div class="uc-kpi">'
            f'<div class="uc-kpi-label"><span>{html.escape(it["label"])}</span>{tip}</div>'
            f'<div class="uc-kpi-value">{it["value"]}</div>'
            f'<div class="uc-kpi-sub">{html.escape(it.get("sub", ""))}</div>'
            "</div>"
        )
    st.markdown(f'<div class="uc-kpis">{"".join(cells)}</div>', unsafe_allow_html=True)


def chart_card(title: str, fig: go.Figure, *, how: str, formula: str, source: str, height: int = 340) -> None:
    # Info sits on the right of the header → open tip leftward.
    tip = _tip(title, how, formula, source, place="left")
    st.markdown(
        '<div class="uc-card-head"><div>'
        f'<div class="uc-card-title">{html.escape(title)}</div>'
        f'<div class="uc-card-formula">{html.escape(formula.splitlines()[0])}</div>'
        f"</div>{tip}</div>",
        unsafe_allow_html=True,
    )
    fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def table_card(title: str, *, how: str, formula: str, source: str) -> None:
    tip = _tip(title, how, formula, source, place="left")
    st.markdown(
        '<div class="uc-card-head"><div>'
        f'<div class="uc-card-title">{html.escape(title)}</div>'
        f'<div class="uc-card-formula">{html.escape(formula.splitlines()[0])}</div>'
        f"</div>{tip}</div>",
        unsafe_allow_html=True,
    )


def footer(left: str, right: str) -> None:
    st.markdown(f'<div class="uc-foot"><span>{left}</span><span>{right}</span></div>', unsafe_allow_html=True)


def brl(x: float) -> str:
    if x >= 1_000_000:
        return f"R$ {x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"R$ {x/1_000:.1f}k"
    return f"R$ {x:,.0f}"
