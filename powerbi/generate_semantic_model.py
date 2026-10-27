#!/usr/bin/env python3
"""Generate TMDL table definitions from exported CSVs for the UrbanCart PBIP.

Uses a Power BI parameter `Data Folder` pointing at powerbi/data so the model
opens in Power BI Desktop (Windows). Re-run after export_dataset.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TABLES_DIR = ROOT / "UrbanCart_Olist.SemanticModel" / "definition" / "tables"
EXPR = ROOT / "UrbanCart_Olist.SemanticModel" / "definition" / "expressions.tmdl"
RELS = ROOT / "UrbanCart_Olist.SemanticModel" / "definition" / "relationships.tmdl"

# Preferred type map for known columns
FORCE = {
    "amount": "double",
    "price": "double",
    "freight": "double",
    "revenue": "double",
    "monetary": "double",
    "clv": "double",
    "avg_order_value": "double",
    "purchase_frequency": "double",
    "lifespan_years": "double",
    "aov": "double",
    "support": "double",
    "confidence_a_to_b": "double",
    "confidence_b_to_a": "double",
    "lift": "double",
    "retention_rate": "double",
    "revenue_per_order": "double",
    "total_revenue": "double",
    "total_spent": "double",
    "quantity": "int64",
    "units": "int64",
    "orders": "int64",
    "customers": "int64",
    "total_orders": "int64",
    "recency": "int64",
    "frequency": "int64",
    "r_score": "int64",
    "f_score": "int64",
    "m_score": "int64",
    "days_inactive": "int64",
    "lifespan_days": "int64",
    "period_number": "int64",
    "cohort_size": "int64",
    "retained_customers": "int64",
    "pair_orders": "int64",
    "order_line_id": "int64",
    "year": "int64",
    "month": "int64",
    "day": "int64",
    "quarter": "int64",
    "total_orders": "int64",
}


def infer_type(col: str, s: pd.Series) -> str:
    if col in FORCE:
        return FORCE[col]
    if pd.api.types.is_bool_dtype(s):
        return "boolean"
    if pd.api.types.is_integer_dtype(s):
        return "int64"
    if pd.api.types.is_float_dtype(s):
        return "double"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "dateTime"
    # date-looking object columns
    name = col.lower()
    if any(k in name for k in ("date", "month", "purchase", "signup", "period")):
        return "dateTime"
    return "string"


def m_type(tmdl_type: str) -> str:
    return {
        "int64": "Int64.Type",
        "double": "Number.Type",
        "boolean": "Logical.Type",
        "dateTime": "DateTime.Type",
        "string": "Text.Type",
    }[tmdl_type]


def quote(name: str) -> str:
    if any(c in name for c in " .'-"):
        return f"'{name}'"
    return name


def write_table(csv_name: str) -> str:
    path = DATA / f"{csv_name}.csv"
    df = pd.read_csv(path, nrows=2000)
    # parse dates softly for inference
    for c in df.columns:
        if "date" in c.lower() or c in {"month", "cohort_month", "first_date", "analysis_date", "first_purchase", "last_purchase", "last_purchase_date", "signup_date", "date_id", "month_start"}:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    ncols = len(df.columns)
    types = {c: infer_type(c, df[c]) for c in df.columns}

    type_rows = ",\n\t\t\t\t".join(
        f'{{"{c}", {m_type(types[c])}}}' for c in df.columns
    )

    cols_block = []
    for c in df.columns:
        t = types[c]
        summarize = "none" if t == "string" or "id" in c.lower() or c.endswith("_id") else "sum" if t in {"int64", "double"} and c not in {"year", "month", "day", "quarter", "r_score", "f_score", "m_score", "period_number"} else "none"
        if c in {"customer_id", "product_id", "order_id", "order_line_id", "customer_segment", "churn_segment", "category", "state", "city", "payment_type", "order_status"}:
            summarize = "none"
        cols_block.append(
            f"\tcolumn {quote(c)}\n"
            f"\t\tdataType: {t}\n"
            f"\t\tsummarizeBy: {summarize}\n"
            f"\t\tsourceColumn: {c}\n"
        )

    # Power Query: read from Data Folder parameter
    source = f"""\t\t\tlet
\t\t\t\tSource = Csv.Document(
\t\t\t\t\tFile.Contents("{csv_name}.csv" meta [#"Data Folder" = #"Data Folder"]),
\t\t\t\t\t[Delimiter = ",", Columns = {ncols}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
\t\t\t\t),
\t\t\t\t#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
\t\t\t\t#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{
\t\t\t\t\t{type_rows}
\t\t\t\t}})
\t\t\tin
\t\t\t\t#"Changed Type\""""

    # File.Contents with meta Data Folder doesn't work that way.
    # Correct pattern: File.Contents(#"Data Folder" & "/file.csv")
    source = f"""\t\t\tlet
\t\t\t\tSource = Csv.Document(
\t\t\t\t\tFile.Contents(#"Data Folder" & "/{csv_name}.csv"),
\t\t\t\t\t[Delimiter = ",", Columns = {ncols}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
\t\t\t\t),
\t\t\t\t#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
\t\t\t\t#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{
\t\t\t\t\t{type_rows}
\t\t\t\t}})
\t\t\tin
\t\t\t\t#"Changed Type\""""

    body = (
        f"table {quote(csv_name)}\n"
        f"\tlineageTag: {csv_name}-table\n\n"
        + "\n".join(cols_block)
        + f"\n\tpartition {quote(csv_name)} = m\n"
        f"\t\tmode: import\n"
        f"\t\tsource =\n{source}\n"
    )
    return body


def inject_measures(table_tmdl: str) -> str:
    """Append core DAX measures onto the Measures stub table."""
    measures = """
	measure 'Gross GMV' = SUM(orders_fact[amount])
		formatString: #,0.00

	measure Orders = DISTINCTCOUNT(orders_fact[order_id])
		formatString: #,0

	measure Buyers = DISTINCTCOUNT(orders_fact[customer_id])
		formatString: #,0

	measure AOV = DIVIDE([Gross GMV], [Orders])
		formatString: #,0.00

	measure 'Avg CLV' = AVERAGE(clv_table[clv])
		formatString: #,0.00

	measure 'Churn Rate' = ```
		DIVIDE(
		    CALCULATE(DISTINCTCOUNT(pbi_churn_risk[customer_id]), pbi_churn_risk[churn_segment] = "High Risk"),
		    DISTINCTCOUNT(pbi_churn_risk[customer_id])
		)
		```
		formatString: 0.0%

	measure 'Repeat Rate' = ```
		DIVIDE(
		    CALCULATE(DISTINCTCOUNT(customer_metrics[customer_id]), customer_metrics[total_orders] >= 2),
		    DISTINCTCOUNT(customer_metrics[customer_id])
		)
		```
		formatString: 0.0%

	measure 'Revenue At Risk' = ```
		CALCULATE(SUM(pbi_churn_risk[total_spent]), pbi_churn_risk[churn_segment] = "High Risk")
		```
		formatString: #,0.00
"""
    # Insert measures after table header / lineageTag line
    lines = table_tmdl.splitlines(keepends=True)
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith("\tlineageTag:"):
            out.append(measures)
            inserted = True
    return "".join(out)


def main() -> None:
    assert DATA.exists(), "Run export_dataset.py first"
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    data_folder = str(DATA.resolve()).replace("\\", "/")
    EXPR.write_text(
        f'expression \'Data Folder\' = "{data_folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n',
        encoding="utf-8",
    )

    csv_tables = sorted(p.stem for p in DATA.glob("*.csv"))
    for name in csv_tables:
        body = write_table(name)
        if name == "Measures":
            body = inject_measures(body)
        (TABLES_DIR / f"{name}.tmdl").write_text(body, encoding="utf-8")
        print(f"  table {name}")

    RELS.write_text(
        """relationship rel_orders_customers
	fromColumn: orders_fact.customer_id
	toColumn: dim_customers.customer_id

relationship rel_orders_products
	fromColumn: orders_fact.product_id
	toColumn: dim_products.product_id

relationship rel_orders_date
	fromColumn: orders_fact.order_date
	toColumn: dim_date.date_id

relationship rel_rfm_customers
	fromColumn: rfm_segmentation.customer_id
	toColumn: dim_customers.customer_id

relationship rel_clv_customers
	fromColumn: clv_table.customer_id
	toColumn: dim_customers.customer_id

relationship rel_churn_customers
	fromColumn: pbi_churn_risk.customer_id
	toColumn: dim_customers.customer_id

relationship rel_metrics_customers
	fromColumn: customer_metrics.customer_id
	toColumn: dim_customers.customer_id
""",
        encoding="utf-8",
    )

    # Refresh model.tmdl refs
    refs = "\n".join(f"ref table {quote(n)}" for n in csv_tables)
    model = ROOT / "UrbanCart_Olist.SemanticModel" / "definition" / "model.tmdl"
    model.write_text(
        "model Model\n"
        "\tculture: en-US\n"
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tdiscourageImplicitMeasures: false\n\n"
        f"{refs}\n",
        encoding="utf-8",
    )
    print(f"Data Folder parameter → {data_folder}")
    print("Semantic model TMDL ready.")


if __name__ == "__main__":
    main()
