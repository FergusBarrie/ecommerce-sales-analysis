"""
Clean the Online Retail II dataset and load it into a SQLite database.

Input : data/raw/online_retail_II.xlsx   (two sheets, one per year)
Output: data/clean/retail_clean.csv      (the transaction lines I kept)
        data/clean/retail.db             (SQLite database used by the SQL scripts)
        outputs/cleaning_log.txt         (how many rows each step removed)

Every row I drop is counted and written to the cleaning log, so the numbers in
the write-up can be traced back to a specific decision.
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "online_retail_II.xlsx"
CLEAN_DIR = ROOT / "data" / "clean"
OUT_DIR = ROOT / "outputs"

# Stock codes that are not products. I found these by listing every code that
# does not look like a normal product code (5 digits, sometimes with letters)
# and reading its description: postage, carriage, manual adjustments, bad debt,
# Amazon fees, charity commission, samples and a test product.
NON_PRODUCT_CODES = {
    "POST", "DOT", "C2", "M", "D", "S", "B", "BANK CHARGES",
    "ADJUST", "ADJUST2", "AMAZONFEE", "CRUK", "TEST001", "TEST002",
}

log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    for sheet in ["Year 2009-2010", "Year 2010-2011"]:
        part = pd.read_excel(RAW, sheet_name=sheet)
        log("Loaded sheet " + sheet + ": {:,} rows".format(len(part)))
        frames.append(part)
    df = pd.concat(frames, ignore_index=True)

    df.columns = ["invoice", "stock_code", "description", "quantity",
                  "invoice_date", "price", "customer_id", "country"]
    start_rows = len(df)
    log("\nCombined raw rows: {:,}".format(start_rows))
    log("Date range: {} to {}".format(df.invoice_date.min(), df.invoice_date.max()))

    # Tidy the text columns first, so the same product does not appear twice
    # because of stray spaces or different capitalisation.
    df["invoice"] = df["invoice"].astype(str).str.strip().str.upper()
    df["stock_code"] = df["stock_code"].astype(str).str.strip().str.upper()
    df["description"] = df["description"].astype(str).str.strip().str.upper()
    df.loc[df["description"].isin(["NAN", "NONE", ""]), "description"] = pd.NA
    df["country"] = df["country"].str.strip()

    # Step 1 - exact duplicate rows. The same invoice, product, quantity, price
    # and timestamp appearing twice is a data entry duplicate, not two sales.
    dupes = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    log("Step 1  removed {:,} exact duplicate rows".format(dupes))

    # Step 2 - cancellations. Invoices starting with 'C' are credit notes and
    # always carry a negative quantity. I keep them in a separate table because
    # the cancellation rate is interesting on its own, but they must not sit in
    # the sales table or they would quietly cancel out real revenue.
    is_cancel = df["invoice"].str.startswith("C")
    cancellations = df[is_cancel].copy()
    df = df[~is_cancel].reset_index(drop=True)
    log("Step 2  moved {:,} cancellation lines to a separate table".format(len(cancellations)))

    # Step 3 - 'A' invoices are a few bad-debt adjustments, not sales.
    is_adj = df["invoice"].str.startswith("A")
    log("Step 3  removed {:,} bad-debt adjustment rows (invoices starting with A)".format(int(is_adj.sum())))
    df = df[~is_adj].reset_index(drop=True)

    # Step 4 - rows that cannot be a sale: zero or negative quantity or price.
    # The zero-price rows are mostly samples and data entry errors.
    bad_qty = int((df["quantity"] <= 0).sum())
    bad_price = int((df["price"] <= 0).sum())
    df = df[(df["quantity"] > 0) & (df["price"] > 0)].reset_index(drop=True)
    log("Step 4  removed {:,} rows with quantity <= 0 and {:,} rows with price <= 0".format(bad_qty, bad_price))

    # Step 5 - service and admin lines (postage, fees, manual adjustments).
    # This is real money, but it is not a product, so leaving it in would
    # distort the best-selling product ranking.
    is_service = (df["stock_code"].isin(NON_PRODUCT_CODES)
                  | df["stock_code"].str.startswith("GIFT_"))
    service_rows = int(is_service.sum())
    service_value = float((df.loc[is_service, "quantity"] * df.loc[is_service, "price"]).sum())
    df = df[~is_service].reset_index(drop=True)
    log("Step 5  removed {:,} postage / fee / adjustment lines worth GBP {:,.0f}".format(
        service_rows, service_value))

    # Step 6 - a few rows still have no description but do have a valid stock
    # code, so I fill the description from the most common description used for
    # that stock code elsewhere in the data.
    missing_desc = int(df["description"].isna().sum())
    if missing_desc:
        lookup = (df.dropna(subset=["description"])
                    .groupby("stock_code")["description"]
                    .agg(lambda s: s.value_counts().index[0]))
        df["description"] = df["description"].fillna(df["stock_code"].map(lookup))
    still_missing = int(df["description"].isna().sum())
    df = df.dropna(subset=["description"]).reset_index(drop=True)
    log("Step 6  filled {:,} missing descriptions from the stock code, dropped {:,} that could not be filled".format(
        missing_desc - still_missing, still_missing))

    # Step 7 - match credit notes back to the sale they reverse.
    #
    # This is the step I nearly missed. Removing the credit notes in step 2 but
    # keeping the original sale means a cancelled order still counts as
    # revenue. The two largest "sales" in the whole dataset turned out to be
    # exactly this: 80,995 units of PAPER CRAFT, LITTLE BIRDIE (GBP 168,470)
    # and 74,215 ceramic storage jars (GBP 77,184), both credited back in full
    # within two days.
    #
    # The match is deliberately strict: same customer, same product, same
    # quantity, same price, and the sale must come on or before the credit. I
    # pair them one-to-one using cumcount(), so a customer who bought the same
    # item three times and returned it once only loses one sale line.
    df["revenue"] = (df["quantity"] * df["price"]).round(2)
    cancellations["revenue"] = (cancellations["quantity"] * cancellations["price"]).round(2)

    match_keys = ["customer_id", "stock_code", "quantity", "price"]
    sales_pool = df.reset_index(names="sale_pos").sort_values("invoice_date")
    sales_pool["pair_no"] = sales_pool.groupby(match_keys, dropna=False).cumcount()

    credits = cancellations[cancellations["customer_id"].notna()].copy()
    credits = credits.reset_index(names="credit_pos")
    credits["quantity"] = -credits["quantity"]           # make it positive to match
    credits = credits.sort_values("invoice_date")
    credits["pair_no"] = credits.groupby(match_keys, dropna=False).cumcount()

    paired = credits[match_keys + ["pair_no", "credit_pos", "invoice_date"]].merge(
        sales_pool[match_keys + ["pair_no", "sale_pos", "invoice_date"]],
        on=match_keys + ["pair_no"], how="inner", suffixes=("_credit", "_sale"),
    )
    # A credit can only reverse a sale that already happened.
    paired = paired[paired["invoice_date_sale"] <= paired["invoice_date_credit"]]
    reversed_positions = paired["sale_pos"].unique()
    reversed_value = float(df.loc[reversed_positions, "revenue"].sum())

    gross_revenue = float(df["revenue"].sum())
    df = df.drop(index=reversed_positions).reset_index(drop=True)
    total_credit_value = float(-cancellations["revenue"].sum())

    log("Step 7  matched {:,} of {:,} credit lines back to a sale and removed both sides".format(
        len(paired), len(cancellations)))
    log("        gross product sales were GBP {:,.2f}; removing matched reversals leaves GBP {:,.2f}".format(
        gross_revenue, gross_revenue - reversed_value))
    log("        total value credited over the period: GBP {:,.2f}; GBP {:,.2f} of that could not be".format(
        total_credit_value, total_credit_value - reversed_value))
    log("        tied to a specific sale line (partial returns, postage and fee credits, and credits")
    log("        with no customer ID), so the revenue figure is still very slightly overstated")

    df["invoice_month"] = df["invoice_date"].dt.strftime("%Y-%m")
    df["invoice_day"] = df["invoice_date"].dt.date.astype(str)
    df["hour"] = df["invoice_date"].dt.hour
    df["weekday"] = df["invoice_date"].dt.day_name()

    # Customer ID is missing on about a fifth of the rows. I do not drop these:
    # the money was still taken, so they belong in the revenue totals. They are
    # excluded later from anything measured per customer, and I say so in the
    # write-up rather than hiding it.
    no_cust = int(df["customer_id"].isna().sum())
    log("\nKept rows: {:,} ({:.1%} of the raw file)".format(len(df), len(df) / start_rows))
    log("Rows with no customer ID: {:,} ({:.1%}) - kept for revenue, excluded from per-customer analysis".format(
        no_cust, no_cust / len(df)))
    df["customer_id"] = df["customer_id"].astype("Int64")

    cancellations["invoice_month"] = cancellations["invoice_date"].dt.strftime("%Y-%m")
    cancellations["customer_id"] = cancellations["customer_id"].astype("Int64")
    # Flag which credit lines I was able to tie back to a sale, so the SQL can
    # tell the two kinds of credit apart.
    cancellations["matched_to_sale"] = 0
    cancellations.loc[cancellations.index.isin(paired["credit_pos"]), "matched_to_sale"] = 1

    log("\nTotal revenue in the clean sales table: GBP {:,.2f}".format(df.revenue.sum()))
    log("Invoices: {:,}   Products: {:,}   Customers: {:,}   Countries: {}".format(
        df.invoice.nunique(), df.stock_code.nunique(),
        df.customer_id.nunique(), df.country.nunique()))

    df.to_csv(CLEAN_DIR / "retail_clean.csv", index=False)

    db_path = CLEAN_DIR / "retail.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    df.to_sql("sales", con, index=False)
    cancellations.to_sql("cancellations", con, index=False)
    con.execute("CREATE INDEX idx_sales_month ON sales(invoice_month)")
    con.execute("CREATE INDEX idx_sales_customer ON sales(customer_id)")
    con.execute("CREATE INDEX idx_sales_stock ON sales(stock_code)")
    con.commit()
    con.close()
    log("\nWrote " + str(CLEAN_DIR / "retail_clean.csv"))
    log("Wrote " + str(db_path) + " (tables: sales, cancellations)")

    (OUT_DIR / "cleaning_log.txt").write_text("\n".join(log_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
