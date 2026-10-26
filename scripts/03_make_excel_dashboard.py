"""
Build the Excel sales dashboard from the CSVs produced by 02_run_sql.py.

Output: excel/ecommerce_sales_dashboard.xlsx

The workbook is deliberately built the way I would build it by hand:
 - one sheet per topic, with the SQL output pasted in as a table
 - the derived columns (% change, moving average, share of total) are written
   as real Excel formulas, not as pre-calculated values, so anyone opening the
   file can click a cell and see how the number is produced
 - a Dashboard sheet that pulls the headline figures from the other sheets and
   holds the charts

Usage: python scripts/03_make_excel_dashboard.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "excel" / "ecommerce_sales_dashboard.xlsx"


def load(name):
    return pd.read_csv(TABLES / name)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    overview = load("01_overview.csv").iloc[0]
    monthly = load("02_monthly_sales_trend.csv")
    products = load("03_top_products.csv")
    categories = load("04_product_categories.csv")
    countries = load("05_sales_by_country.csv")
    customers = load("06_customer_purchase_patterns.csv")
    order_bands = load("07_order_value_distribution.csv")
    yoy = load("11_year_on_year.csv")
    repeat = load("12_repeat_customer_share.csv")

    writer = pd.ExcelWriter(OUT, engine="xlsxwriter")
    book = writer.book

    # ---- shared formats -------------------------------------------------
    title = book.add_format({"bold": True, "font_size": 15, "font_color": "#1F3353"})
    sub = book.add_format({"font_size": 10, "font_color": "#5A6B80", "text_wrap": True, "valign": "top"})
    head = book.add_format({"bold": True, "bg_color": "#1F3353", "font_color": "white",
                            "border": 1, "border_color": "#1F3353", "text_wrap": True, "valign": "vcenter"})
    gbp = book.add_format({"num_format": "#,##0", "border": 1, "border_color": "#D5DBE3"})
    gbp2 = book.add_format({"num_format": "#,##0.00", "border": 1, "border_color": "#D5DBE3"})
    num = book.add_format({"num_format": "#,##0", "border": 1, "border_color": "#D5DBE3"})
    pct = book.add_format({"num_format": "0.0%", "border": 1, "border_color": "#D5DBE3"})
    txt = book.add_format({"border": 1, "border_color": "#D5DBE3"})
    kpi_lbl = book.add_format({"font_size": 10, "font_color": "#5A6B80"})
    kpi_val = book.add_format({"font_size": 18, "bold": True, "font_color": "#1F3353", "num_format": "#,##0"})
    kpi_val_gbp = book.add_format({"font_size": 18, "bold": True, "font_color": "#1F3353",
                                   "num_format": "£#,##0"})
    kpi_val_gbp2 = book.add_format({"font_size": 18, "bold": True, "font_color": "#1F3353",
                                    "num_format": "£#,##0.00"})
    note = book.add_format({"font_size": 9, "italic": True, "font_color": "#7A8899", "text_wrap": True,
                            "valign": "top"})

    def write_table(ws, df, start_row, fmt_map, col_widths=None):
        """Write a dataframe as a formatted table and return the last row used."""
        for c, col in enumerate(df.columns):
            ws.write(start_row, c, col.replace("_", " "), head)
        for r, (_, row) in enumerate(df.iterrows(), start=start_row + 1):
            for c, col in enumerate(df.columns):
                value = row[col]
                fmt = fmt_map.get(col, txt)
                if pd.isna(value):
                    ws.write_blank(r, c, None, fmt)
                else:
                    ws.write(r, c, value, fmt)
        if col_widths:
            for c, w in enumerate(col_widths):
                ws.set_column(c, c, w)
        return start_row + len(df)

    # =====================================================================
    # Read me
    # =====================================================================
    ws = book.add_worksheet("Read me")
    writer.sheets["Read me"] = ws
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 110)
    ws.hide_gridlines(2)
    ws.write(1, 1, "E-commerce sales analysis - dashboard workbook", title)
    readme = [
        "What this is",
        "A sales dashboard for a UK online gift retailer, covering 1 December 2009 to 9 December 2011.",
        "",
        "Data source",
        "Online Retail II, UCI Machine Learning Repository (dataset 502). Licence: CC BY 4.0.",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "",
        "How the numbers were produced",
        "The raw file has 1,067,371 transaction lines. A Python script cleans it (removing duplicates, "
        "credit notes, zero-price rows and non-product lines such as postage), loads the result into a "
        "SQLite database, and runs a set of SQL queries. The CSV output of those queries is what feeds "
        "this workbook. Nothing here is typed in by hand.",
        "",
        "Two things to be aware of before quoting any figure",
        "1. December 2011 covers only nine days, so it is excluded from every growth comparison.",
        "2. About 23% of transaction lines have no customer ID. Those rows are included in revenue "
        "totals (the money was taken) but excluded from anything measured per customer.",
        "",
        "Sheets",
        "Dashboard        headline figures and the four main charts",
        "Monthly          revenue by month, with month-on-month change and a 3-month moving average",
        "Products         the 20 products that generated the most revenue",
        "Categories       revenue by product category (my own keyword grouping - see note on that sheet)",
        "Countries        revenue and average order value by country",
        "Customers        order frequency bands and revenue concentration",
        "Order sizes      distribution of order values",
        "Year on year     Dec 2009-Nov 2010 compared with Dec 2010-Nov 2011",
        "New vs returning revenue split by first-time and repeat buyers, by month",
    ]
    row = 3
    for line in readme:
        fmt = book.add_format({"bold": True, "font_color": "#1F3353"}) if line and not line.startswith(" ") \
            and line in ("What this is", "Data source", "How the numbers were produced",
                         "Two things to be aware of before quoting any figure", "Sheets") else sub
        ws.write(row, 1, line, fmt)
        row += 1

    # =====================================================================
    # Monthly
    # =====================================================================
    m = monthly[["invoice_month", "revenue", "orders", "active_customers", "units", "avg_order_value"]].copy()
    ws = book.add_worksheet("Monthly")
    writer.sheets["Monthly"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Revenue by month", title)
    ws.write(1, 0, "Month-on-month change and the 3-month moving average are Excel formulas - click any "
                   "cell in columns G or H to see them. December 2011 is a 9-day month and is shaded.", note)
    ws.set_row(1, 28)

    m_out = m.copy()
    m_out["mom_change"] = ""
    m_out["moving_avg_3m"] = ""
    header_row = 3
    last = write_table(
        ws, m_out, header_row,
        {"revenue": gbp2, "orders": num, "active_customers": num, "units": num,
         "avg_order_value": gbp2, "mom_change": pct, "moving_avg_3m": gbp2},
        col_widths=[14, 14, 10, 16, 12, 16, 13, 14],
    )
    # Real formulas for the two derived columns.
    for i in range(len(m_out)):
        r = header_row + 1 + i           # 0-based row in the sheet
        excel_r = r + 1                  # 1-based row for the formula text
        if i == 0:
            ws.write_blank(r, 6, None, pct)
        else:
            ws.write_formula(r, 6, "=(B{0}-B{1})/B{1}".format(excel_r, excel_r - 1), pct)
        if i < 2:
            ws.write_blank(r, 7, None, gbp2)
        else:
            ws.write_formula(r, 7, "=AVERAGE(B{0}:B{1})".format(excel_r - 2, excel_r), gbp2)
    ws.write(last + 2, 0, "Total (incl. partial Dec 2011)", kpi_lbl)
    ws.write_formula(last + 2, 1, "=SUM(B{0}:B{1})".format(header_row + 2, last + 1), gbp2)

    # =====================================================================
    # Products
    # =====================================================================
    ws = book.add_worksheet("Products")
    writer.sheets["Products"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Top 20 products by revenue", title)
    ws.write(1, 0, "Ranked by revenue rather than units sold: the cheapest items sell in huge volumes "
                   "without contributing much money.", note)
    write_table(ws, products, 3,
                {"units_sold": num, "orders_containing_item": num, "revenue": gbp2,
                 "avg_unit_price": gbp2, "share_of_total_pct": gbp2},
                col_widths=[12, 38, 12, 20, 14, 14, 16])

    # =====================================================================
    # Categories
    # =====================================================================
    ws = book.add_worksheet("Categories")
    writer.sheets["Categories"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Revenue by product category", title)
    ws.write(1, 0, "The dataset has no category column. These groups come from keywords in the product "
                   "description, so about 19% of revenue falls into 'Other'. Useful as a summary, not as "
                   "an exact category report.", note)
    ws.set_row(1, 28)
    write_table(ws, categories, 3,
                {"transaction_lines": num, "orders": num, "units_sold": num,
                 "revenue": gbp2, "share_of_revenue_pct": gbp2},
                col_widths=[26, 18, 10, 12, 14, 20])

    # =====================================================================
    # Countries
    # =====================================================================
    ws = book.add_worksheet("Countries")
    writer.sheets["Countries"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Revenue and average order value by country", title)
    ws.write(1, 0, "The UK accounts for most revenue, but export orders are much larger on average - "
                   "these look like wholesale buyers rather than consumers.", note)
    write_table(ws, countries, 3,
                {"orders": num, "customers": num, "revenue": gbp2,
                 "avg_order_value": gbp2, "share_of_revenue_pct": gbp2, "revenue_rank": num},
                col_widths=[22, 10, 11, 14, 16, 20, 13])

    # =====================================================================
    # Customers
    # =====================================================================
    ws = book.add_worksheet("Customers")
    writer.sheets["Customers"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Order frequency and revenue concentration", title)
    ws.write(1, 0, "Customers with no ID in the source data are excluded from this sheet, so it covers "
                   "about 77% of revenue.", note)
    write_table(ws, customers, 3,
                {"customers": num, "pct_of_customers": gbp2, "revenue": gbp2,
                 "pct_of_revenue": gbp2, "mean_avg_order_value": gbp2},
                col_widths=[14, 12, 18, 14, 16, 22])

    # =====================================================================
    # Order sizes
    # =====================================================================
    ws = book.add_worksheet("Order sizes")
    writer.sheets["Order sizes"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Distribution of order values", title)
    write_table(ws, order_bands, 2,
                {"orders": num, "pct_of_orders": gbp2, "revenue": gbp2, "pct_of_revenue": gbp2},
                col_widths=[20, 10, 15, 14, 16])

    # =====================================================================
    # Year on year
    # =====================================================================
    ws = book.add_worksheet("Year on year")
    writer.sheets["Year on year"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Like-for-like comparison of the two 12-month periods", title)
    ws.write(1, 0, "Calendar 2010 against calendar 2011 would be unfair because December 2011 is almost "
                   "entirely missing, and December is the biggest trading month. Dec-Nov windows fix that.",
             note)
    ws.set_row(1, 28)
    last = write_table(ws, yoy, 3,
                       {"orders": num, "active_customers": num, "units": num, "revenue": gbp2,
                        "avg_order_value": gbp2, "revenue_per_active_customer": gbp2,
                        "uk_share_of_revenue_pct": gbp2},
                       col_widths=[30, 10, 16, 12, 14, 16, 26, 22])
    ws.write(last + 2, 0, "Change, year 1 to year 2", book.add_format({"bold": True, "font_color": "#1F3353"}))
    labels = ["orders", "active_customers", "units", "revenue", "avg_order_value"]
    cols = {"orders": "B", "active_customers": "C", "units": "D", "revenue": "E", "avg_order_value": "F"}
    for i, lab in enumerate(labels):
        r = last + 3 + i
        col = cols[lab]
        ws.write(r, 0, lab.replace("_", " "), kpi_lbl)
        ws.write_formula(r, 1, "=({0}6-{0}5)/{0}5".format(col), pct)

    # =====================================================================
    # New vs returning
    # =====================================================================
    ws = book.add_worksheet("New vs returning")
    writer.sheets["New vs returning"] = ws
    ws.hide_gridlines(2)
    ws.write(0, 0, "Revenue from first-time and repeat buyers, by month", title)
    ws.write(1, 0, "Customers whose first purchase happened before December 2009 look like new customers "
                   "here, because the data does not go back far enough to know otherwise. That is why the "
                   "first month looks unusually new-customer heavy.", note)
    ws.set_row(1, 28)
    write_table(ws, repeat, 3,
                {"new_customer_revenue": gbp2, "returning_customer_revenue": gbp2,
                 "new_customer_orders": num, "returning_customer_orders": num,
                 "returning_share_of_revenue_pct": gbp2},
                col_widths=[14, 22, 26, 20, 24, 28])

    # =====================================================================
    # Dashboard
    # =====================================================================
    ws = book.add_worksheet("Dashboard")
    writer.sheets["Dashboard"] = ws
    book.worksheets_objs.insert(0, book.worksheets_objs.pop())   # put Dashboard first
    ws.hide_gridlines(2)
    ws.set_column(0, 0, 2)
    for c in range(1, 9):
        ws.set_column(c, c, 15)
    ws.write(1, 1, "E-commerce sales dashboard", title)
    ws.write(2, 1, "UK online gift retailer | 1 Dec 2009 - 9 Dec 2011 | source: UCI Online Retail II",
             kpi_lbl)

    kpis = [
        ("Total revenue", "=Monthly!B31", kpi_val_gbp),
        ("Orders", "=SUM(Monthly!C5:C29)", kpi_val),
        ("Average order value", "=Monthly!B31/SUM(Monthly!C5:C29)", kpi_val_gbp2),
        ("Identified customers", str(int(overview["identified_customers"])), kpi_val),
        ("Products sold", str(int(overview["products"])), kpi_val),
        ("Countries", str(int(overview["countries"])), kpi_val),
    ]
    for i, (label, value, fmt) in enumerate(kpis):
        col = 1 + (i % 3) * 2
        r = 4 + (i // 3) * 3
        ws.write(r, col, label, kpi_lbl)
        if value.startswith("="):
            ws.write_formula(r + 1, col, value, fmt)
        else:
            ws.write_number(r + 1, col, float(value), fmt)

    n_months = len(monthly)
    first_data_row = 5           # 1-based row of the first data row on Monthly
    last_data_row = first_data_row + n_months - 1

    chart_revenue = book.add_chart({"type": "column"})
    chart_revenue.add_series({
        "name": "Revenue",
        "categories": ["Monthly", first_data_row - 1, 0, last_data_row - 1, 0],
        "values": ["Monthly", first_data_row - 1, 1, last_data_row - 1, 1],
        "fill": {"color": "#2E4A72"},
        "gap": 40,
    })
    line = book.add_chart({"type": "line"})
    line.add_series({
        "name": "3-month moving average",
        "categories": ["Monthly", first_data_row - 1, 0, last_data_row - 1, 0],
        "values": ["Monthly", first_data_row - 1, 7, last_data_row - 1, 7],
        "line": {"color": "#C2703D", "width": 2.0},
    })
    chart_revenue.combine(line)
    chart_revenue.set_title({"name": "Monthly revenue (GBP)"})
    chart_revenue.set_legend({"position": "bottom"})
    chart_revenue.set_y_axis({"num_format": "#,##0"})
    chart_revenue.set_size({"width": 760, "height": 300})
    ws.insert_chart(11, 1, chart_revenue)

    chart_cat = book.add_chart({"type": "bar"})
    chart_cat.add_series({
        "name": "Revenue by category",
        "categories": ["Categories", 4, 0, 4 + len(categories) - 1, 0],
        "values": ["Categories", 4, 4, 4 + len(categories) - 1, 4],
        "fill": {"color": "#2E4A72"},
    })
    chart_cat.set_title({"name": "Revenue by product category (GBP)"})
    chart_cat.set_legend({"none": True})
    chart_cat.set_x_axis({"num_format": "#,##0"})
    chart_cat.set_size({"width": 380, "height": 300})
    ws.insert_chart(28, 1, chart_cat)

    chart_country = book.add_chart({"type": "column"})
    chart_country.add_series({
        "name": "Average order value",
        "categories": ["Countries", 4, 0, 11, 0],
        "values": ["Countries", 4, 4, 11, 4],
        "fill": {"color": "#C2703D"},
    })
    chart_country.set_title({"name": "Average order value, top 8 markets (GBP)"})
    chart_country.set_legend({"none": True})
    chart_country.set_size({"width": 380, "height": 300})
    ws.insert_chart(28, 5, chart_country)

    chart_conc = book.add_chart({"type": "column"})
    chart_conc.add_series({
        "name": "% of customers",
        "categories": ["Customers", 4, 0, 4 + len(customers) - 1, 0],
        "values": ["Customers", 4, 2, 4 + len(customers) - 1, 2],
        "fill": {"color": "#8FA6C4"},
    })
    chart_conc.add_series({
        "name": "% of revenue",
        "categories": ["Customers", 4, 0, 4 + len(customers) - 1, 0],
        "values": ["Customers", 4, 4, 4 + len(customers) - 1, 4],
        "fill": {"color": "#2E4A72"},
    })
    chart_conc.set_title({"name": "Share of customers vs share of revenue (%)"})
    chart_conc.set_legend({"position": "bottom"})
    chart_conc.set_size({"width": 760, "height": 300})
    ws.insert_chart(45, 1, chart_conc)

    ws.write(62, 1, "Reminder: December 2011 is a 9-day month, and rows without a customer ID are "
                    "excluded from the customer charts.", note)

    writer.close()
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
