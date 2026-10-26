"""
Collect the query results into a single JSON file that the portfolio website
reads, and print the headline figures used in the written findings.

Output: outputs/website_data.json

Nothing is rounded or adjusted here beyond display rounding - the file is a
straight copy of the SQL output, so the charts on the website and the tables in
the Excel workbook always agree.

Usage: python scripts/04_export_for_website.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
DB = ROOT / "data" / "clean" / "retail.db"
OUT = ROOT / "outputs" / "website_data.json"


def load(name):
    return pd.read_csv(TABLES / name)


def json_safe(obj):
    """Replace NaN/NaT with None so the output is valid JSON.

    pandas writes missing numbers as NaN, which json.dumps happily emits as the
    bare token NaN - valid Python, invalid JSON, and the website build refuses
    to parse it. Walking the payload once at the end is the reliable fix.
    """
    import math
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if obj is pd.NaT:
        return None
    return obj


def main():
    overview = load("01_overview.csv").iloc[0]
    monthly = load("02_monthly_sales_trend.csv")
    products = load("03_top_products.csv")
    categories = load("04_product_categories.csv")
    countries = load("05_sales_by_country.csv")
    customers = load("06_customer_purchase_patterns.csv")
    order_bands = load("07_order_value_distribution.csv")
    credits = load("08_cancellation_rate.csv")
    yoy = load("11_year_on_year.csv")
    repeat = load("12_repeat_customer_share.csv")

    complete = monthly[monthly.month_status == "complete month"]
    y1 = yoy.iloc[0]
    y2 = yoy.iloc[1]

    # A few figures I quote in the write-up and want calculated, not typed.
    peak = complete.loc[complete.revenue.idxmax()]
    trough = complete.loc[complete.revenue.idxmin()]
    autumn_months = complete[complete.invoice_month.str[-2:].isin(["09", "10", "11"])]
    autumn_share = 100 * autumn_months.revenue.sum() / complete.revenue.sum()
    top10_share = products.head(10).share_of_total_pct.sum()
    repeat_recent = repeat[repeat.invoice_month >= "2010-06"]
    repeat_typical = repeat_recent.returning_share_of_revenue_pct.median()

    con = sqlite3.connect(DB)
    uk_share = float(pd.read_sql(
        "SELECT 100.0 * SUM(CASE WHEN country = 'United Kingdom' THEN revenue ELSE 0 END)"
        " / SUM(revenue) AS s FROM sales", con).iloc[0]["s"])
    median_order = float(pd.read_sql(
        "WITH o AS (SELECT invoice, SUM(revenue) AS v FROM sales GROUP BY invoice)"
        " SELECT v FROM o ORDER BY v LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM o)", con).iloc[0]["v"])
    con.close()

    headline = {
        "period": "{} to {}".format(overview["first_day"], overview["last_day"]),
        "total_revenue": round(float(overview["total_revenue"]), 2),
        "orders": int(overview["orders"]),
        "transaction_lines": int(overview["transaction_lines"]),
        "identified_customers": int(overview["identified_customers"]),
        "products": int(overview["products"]),
        "countries": int(overview["countries"]),
        "avg_order_value": round(float(overview["avg_order_value"]), 2),
        "median_order_value": round(median_order, 2),
        "uk_share_of_revenue_pct": round(uk_share, 1),
        "autumn_share_of_revenue_pct": round(float(autumn_share), 1),
        "peak_month": peak.invoice_month,
        "peak_month_revenue": round(float(peak.revenue), 2),
        "trough_month": trough.invoice_month,
        "trough_month_revenue": round(float(trough.revenue), 2),
        "peak_to_trough_ratio": round(float(peak.revenue / trough.revenue), 2),
        "top10_products_share_pct": round(float(top10_share), 1),
        "typical_returning_revenue_share_pct": round(float(repeat_typical), 1),
        "yoy": {
            "year1_label": y1.period,
            "year2_label": y2.period,
            "revenue_change_pct": round(100 * (y2.revenue / y1.revenue - 1), 1),
            "orders_change_pct": round(100 * (y2.orders / y1.orders - 1), 1),
            "units_change_pct": round(100 * (y2.units / y1.units - 1), 1),
            "aov_change_pct": round(100 * (y2.avg_order_value / y1.avg_order_value - 1), 1),
            "year1_revenue": round(float(y1.revenue), 2),
            "year2_revenue": round(float(y2.revenue), 2),
            "year1_orders": int(y1.orders),
            "year2_orders": int(y2.orders),
            "year1_aov": round(float(y1.avg_order_value), 2),
            "year2_aov": round(float(y2.avg_order_value), 2),
        },
    }

    payload = {
        "meta": {
            "project": "E-commerce sales analysis",
            "dataset": "Online Retail II (UCI Machine Learning Repository, dataset 502)",
            "dataset_url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            "licence": "CC BY 4.0",
            "currency": "GBP",
            "note": "Figures are calculated from the cleaned data by the SQL in sql/. "
                    "December 2011 covers 9 days only and is excluded from growth comparisons.",
        },
        "headline": headline,
        "monthly": monthly.where(pd.notna(monthly), None).to_dict(orient="records"),
        "top_products": products.head(12).to_dict(orient="records"),
        "categories": categories.to_dict(orient="records"),
        "countries": countries.head(12).to_dict(orient="records"),
        "customer_bands": customers.to_dict(orient="records"),
        "order_value_bands": order_bands.to_dict(orient="records"),
        "credits_by_month": credits.to_dict(orient="records"),
        "year_on_year": yoy.to_dict(orient="records"),
        "new_vs_returning": repeat.to_dict(orient="records"),
    }

    OUT.write_text(json.dumps(json_safe(payload), indent=2, allow_nan=False),
                   encoding="utf-8")
    print("Wrote", OUT)
    print()
    print("Headline figures for the write-up")
    print("-" * 60)
    for key, value in headline.items():
        if key == "yoy":
            continue
        print("{:40s} {}".format(key, value))
    print()
    for key, value in headline["yoy"].items():
        print("  yoy.{:36s} {}".format(key, value))


if __name__ == "__main__":
    main()
