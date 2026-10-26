# E-commerce Sales Analysis

Analysis of two years of transactions from a UK online gift retailer, using SQL for the
analysis and Excel for the dashboard.

**Business question:** Where does this retailer's revenue actually come from, and how did
it change between December 2009 and December 2011?

| | |
|---|---|
| **Tools** | SQLite (SQL), Python (pandas, for cleaning only), Excel |
| **Dataset** | [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii), UCI Machine Learning Repository (dataset 502), CC BY 4.0 |
| **Period** | 1 December 2009 to 9 December 2011 |
| **Size** | 1,067,371 raw transaction lines; 997,367 after cleaning |

---

## Headline numbers

All of these are calculated by the SQL in [`sql/`](sql/) — none of them are typed in by hand.

| Metric | Value |
|---|---|
| Revenue | £19,097,385 |
| Orders | 39,336 |
| Average order value | £485.49 |
| Median order value | £299.34 |
| Identified customers | 5,839 |
| Products sold | 4,718 |
| Countries | 43 |
| UK share of revenue | 85.5% |

## What I found

1. **Revenue grew 2.2% year on year, but only because orders got bigger.** Comparing
   Dec 2009–Nov 2010 with Dec 2010–Nov 2011, revenue went from £9.23m to £9.43m (+2.2%)
   while orders fell 3.8% and units fell 6.3%. Average order value rose 6.2%, from
   £469.95 to £498.96. The business served fewer orders and sold fewer items, and still
   took slightly more money.

2. **Trading is heavily seasonal.** September to November alone produced 36.8% of total
   revenue. The best month (November 2011, £1.44m) was 2.9 times the worst
   (February 2011, £0.50m).

3. **A small group of repeat buyers carries the business.** Of the customers who can be
   identified, the 16.4% who placed 10 or more orders generated 67.7% of revenue. The
   27.6% who ordered only once generated 3.3%. In a typical month, around 91% of revenue
   came from customers who had bought before.

4. **The export markets are really a handful of individual accounts.** The Netherlands is
   the third-largest market at £547k, but 95.8% of that came from one customer ID.
   Ireland is second at £606k, with 92% from two customers. Export orders are also far
   larger than UK ones — £2,544 average in the Netherlands against £453 in the UK — which
   suggests these are wholesale buyers rather than consumers.

5. **Revenue leans on a small number of large orders.** The 2.9% of orders worth more than
   £2,000 produced 27.6% of revenue. That is why the mean order value (£485) sits well
   above the median (£299).

## What I would suggest doing about it

1. **Treat the top accounts as a concentration risk, and give them named contacts.**
   Losing the single Dutch customer would remove around 2.7% of total revenue by itself.
   The same applies to the two Irish accounts. This is a commercial risk that the sales
   totals hide.

2. **Plan stock and cash around the autumn peak, not the annual average.** November
   trades at roughly 2.9 times February. Buying and warehouse staffing based on an
   average month would mean running short in the peak and holding too much in the spring.

3. **Try to get a second order out of one-time customers.** They are 27.6% of identified
   customers but only 3.3% of revenue. Even a small improvement in the share who come back
   is worth more than chasing the same repeat buyers harder — though I cannot say how much
   it would be worth, because the data contains no marketing costs.

## Limitations

- **No cost or margin data.** Everything here is revenue. A product with high revenue
  could still be unprofitable, so "best selling" never means "most profitable".
- **23% of transaction lines have no customer ID.** They are included in revenue totals
  (the money was taken) but excluded from every per-customer figure. Those rows are not
  one anonymous customer — they are simply unknown.
- **The dataset has no product category column.** The categories in
  [`sql/04_product_categories.sql`](sql/04_product_categories.sql) are my own grouping
  based on keywords in the product description. About 19% of revenue does not match any
  keyword and sits in "Other", so treat the category split as a rough summary.
- **December 2011 covers only nine days,** so it is excluded from all growth comparisons.
- **Credit notes are only partly matched.** I could tie 5,990 of 19,104 credit lines back
  to the exact sale they reversed and removed both sides. The remaining £916k of credits
  are mostly partial returns and credits with no customer ID, so revenue is still very
  slightly overstated.
- **The data is from 2009–2011.** It is good for practising the analysis; it says nothing
  about today's market.
- **There are only 30 Saturday orders in two years,** which almost certainly means the
  order feed is incomplete rather than that nobody shopped on Saturdays.

---

## How to reproduce this

You need Python 3.9+ and `pandas`, `openpyxl` and `xlsxwriter`. No database server is
needed — SQLite comes with Python.

```bash
pip install pandas openpyxl xlsxwriter

# 1. Download the dataset (45 MB) into data/raw/
python scripts/00_download_data.py

# 2. Clean it and build the SQLite database
python scripts/01_clean_data.py

# 3. Run every query in sql/ and save the results to outputs/tables/
python scripts/02_run_sql.py

# 4. Build the Excel dashboard
python scripts/03_make_excel_dashboard.py

# 5. Export the JSON the portfolio website reads
python scripts/04_export_for_website.py
```

Steps 1 and 2 take a couple of minutes because the source file is a 45 MB Excel workbook.
Everything after that is fast.

To explore the database yourself:

```bash
sqlite3 data/clean/retail.db
sqlite> .mode column
sqlite> .read sql/02_monthly_sales_trend.sql
```

## What is in this repository

```
data/raw/        the source Excel file (not committed - run 00_download_data.py)
data/clean/      retail_clean.csv and retail.db (not committed - regenerated by step 2)
scripts/         00 download, 01 clean, 02 run SQL, 03 Excel dashboard, 04 website export
sql/             12 .sql files, one per question, each with comments explaining it
outputs/tables/  one CSV per query - these are the numbers quoted above
outputs/         cleaning_log.txt (every row dropped, and why) and website_data.json
excel/           ecommerce_sales_dashboard.xlsx
FINDINGS.md      the full write-up
LEARNING_GUIDE.md  how every query and figure works, with exercises
```

The raw and cleaned data files are not committed because the source file is 45 MB.
`scripts/00_download_data.py` fetches it from UCI, and the rest of the pipeline rebuilds
everything else from it.

## Data cleaning summary

`scripts/01_clean_data.py` writes a full log to `outputs/cleaning_log.txt`. In short:

| Step | Rows affected | Why |
|---|---|---|
| Exact duplicates removed | 34,335 | Identical invoice, product, quantity, price and timestamp |
| Credit notes separated | 19,104 | Invoices starting with `C`; kept in their own table |
| Bad-debt adjustments removed | 6 | Invoices starting with `A` |
| Quantity ≤ 0 or price ≤ 0 removed | 9,407 | Cannot be a sale |
| Postage, fees and manual adjustments removed | 4,555 | Real money, but not products |
| Cancelled sales removed | 5,990 | Matched back to the credit note that reversed them |

The last step matters most. Separating the credit notes but keeping the original sale left
cancelled orders counted as revenue — including the two largest "sales" in the dataset
(£168,470 and £77,184), both of which were credited back in full within two days. Matching
them back reduced revenue from £19.64m to £19.10m.

## Honest note on this project

I built this project to learn, and the write-up only claims what the data supports. The
[learning guide](LEARNING_GUIDE.md) explains every query and every figure, including the
parts I found difficult. I am comfortable walking through any of it line by line.
