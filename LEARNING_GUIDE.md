# Learning guide — E-commerce Sales Analysis

This guide exists so that I can explain every part of this project rather than just show
the output. It goes through each query, each figure and each decision, and ends with
interview questions and exercises.

Work through it with the database open in one window and this file in another:

```bash
sqlite3 data/clean/retail.db
sqlite> .mode column
sqlite> .headers on
```

---

## 1. The dataset in one paragraph

Online Retail II is a real transaction log from a UK-based online gift retailer that sells
mostly to small businesses. Each row is **one product line on one invoice** — not one
order. An order with eight different products is eight rows sharing an invoice number.
Getting this right matters: if you count rows you are counting product lines, and if you
want orders you must count **distinct invoice numbers**.

Columns: `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`,
`Customer ID`, `Country`. There is no revenue column — revenue is `Quantity × Price`, which
I calculate during cleaning.

**Be able to say:** "1,067,371 rows, two years, one row per product line per invoice, no
revenue column, no cost column, no category column."

---

## 2. The cleaning, step by step

Open `scripts/01_clean_data.py` alongside this. Each step below matches a numbered step in
the script, and the row counts are in `outputs/cleaning_log.txt`.

### Step 1 — 34,335 exact duplicate rows

```python
df = df.drop_duplicates()
```

A row that matches another on *every* column — same invoice, same product, same quantity,
same price, same timestamp to the second — is a data entry duplicate. Two genuinely
separate sales of the same product on the same invoice would be entered as one line with
a higher quantity.

**Why it matters:** leaving them in would inflate revenue by about 3%.

### Step 2 — 19,104 credit notes moved aside

Invoice numbers starting with `C` are credit notes and always have a negative quantity.
I move them to a separate `cancellations` table rather than deleting them, because the
return rate is a finding in its own right.

### Step 3 — 6 rows with invoices starting with `A`

Reading their descriptions showed "Adjust bad debt" with values around −£24,600. These are
accounting adjustments, not sales.

**The lesson:** when a handful of rows look strange, read them before deciding. It took
one query.

### Step 4 — 9,407 rows with quantity ≤ 0 or price ≤ 0

After removing the `C` invoices, 3,393 negative-quantity rows remained, plus 6,014 rows
priced at zero (mostly samples and errors). Neither can be a sale.

### Step 5 — 4,555 postage, fee and adjustment lines (£821,337)

The stock code column contains entries that are not products. I found them by listing
every code that does **not** look like a product code (five digits, sometimes followed by
letters) and reading its description:

| Code | Description |
|---|---|
| `POST`, `DOT`, `C2` | Postage and carriage |
| `M` | Manual adjustment |
| `D` | Discount |
| `S` | Samples |
| `B` | Adjust bad debt |
| `BANK CHARGES`, `AMAZONFEE`, `CRUK` | Fees and commission |
| `TEST001`, `TEST002` | Test products |
| `GIFT_0001_*` | Gift vouchers |

These are real money, but counting them as products would put "POSTAGE" in the
best-sellers list. Note that `DCGS...`, `PADS` and `SP1002` *are* real products despite
odd codes — which is why I read the descriptions instead of just dropping everything
non-standard.

### Step 6 — missing descriptions

4,382 rows had no description. The code fills them from the most common description for
the same stock code, then drops any that remain. In the end it filled **zero**, because
every row with a missing description was priced at zero and had already gone in step 4.
I left the code in place because it would matter on a different extract of the same data.

**Be able to say:** "The fallback didn't fire on this dataset — the missing descriptions
all overlapped with the zero-price rows I'd already removed."

### Step 7 — the one I nearly missed: matching cancelled sales

This is the most important part of the cleaning and the best thing to talk about in an
interview.

Removing credit notes in step 2 but keeping the original sale means **a cancelled order
still counts as revenue**. I only noticed because the top-products list contained
"PAPER CRAFT, LITTLE BIRDIE" with 80,995 units sold in a single order worth £168,470 —
far out of line with everything else. Looking it up:

```sql
SELECT invoice, stock_code, quantity, price, revenue, invoice_day
FROM sales WHERE stock_code = '23843';
-- invoice 581483, 80995 units, 2011-12-09, £168,469.60

SELECT invoice, stock_code, quantity, price, invoice_month
FROM cancellations WHERE stock_code = '23843';
-- invoice C581484, -80995 units  <- the whole thing was credited back
```

The same was true of the second-largest sale (74,215 ceramic storage jars, £77,184).

The fix pairs each credit note with the sale it reverses:

```python
match_keys = ["customer_id", "stock_code", "quantity", "price"]
sales_pool["pair_no"] = sales_pool.groupby(match_keys).cumcount()
credits["pair_no"]    = credits.groupby(match_keys).cumcount()
paired = credits.merge(sales_pool, on=match_keys + ["pair_no"])
paired = paired[paired.invoice_date_sale <= paired.invoice_date_credit]
```

Three things to understand here:

- **The match is strict:** same customer, same product, same quantity, same price.
- **`cumcount()` makes it one-to-one.** If a customer bought the same item three times and
  returned it once, `cumcount()` numbers the sales 0, 1, 2 and the credit 0, so only one
  sale is cancelled — not all three. Without this, a single return could wipe out every
  matching sale.
- **The date check** stops a credit cancelling a sale that happened afterwards.

Result: 5,990 of 19,104 credit lines matched. Revenue fell from £19.64m to £19.10m, a 2.8%
correction. The remaining £916k of credits are partial returns, postage refunds and credits
with no customer ID — I report them in `sql/08_cancellation_rate.sql` rather than guessing.

**The lesson:** an outlier in a top-10 list is worth five minutes of investigation. In this
case it changed the headline number.

### The missing customer IDs — a decision, not a cleaning step

226,761 rows (22.7%) have no customer ID. I **kept** them, because the money was taken and
they belong in revenue. But I exclude them from everything measured per customer.

The wrong thing to do is treat blank as one customer — that would create a single
"customer" accounting for 23% of revenue. They are not one customer; they are unknown.

**Be able to say:** "Revenue figures cover 100% of the clean data; customer figures cover
77% of it. I say so wherever it matters."

---

## 3. The SQL, query by query

### `01_overview.sql` — always run this first

```sql
SELECT COUNT(DISTINCT invoice) AS orders,
       ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value
FROM sales;
```

The one thing to understand: **average order value is total revenue ÷ distinct invoices**,
not `AVG(revenue)`. `AVG(revenue)` would give the average *product line* value, about
£19 — a different and much smaller number. Mixing these up is a common and very visible
mistake.

### `02_monthly_sales_trend.sql` — window functions

```sql
LAG(revenue) OVER (ORDER BY invoice_month) AS prev_month_revenue
SUM(revenue) OVER (ORDER BY invoice_month) AS running_total_revenue
```

- `LAG(revenue) OVER (ORDER BY invoice_month)` returns the previous row's revenue, so I can
  calculate month-on-month growth without joining the table to itself.
- `SUM(...) OVER (ORDER BY ...)` gives a running total, because an `ORDER BY` inside
  `OVER()` makes the window "all rows up to this one".
- The first row's `LAG` is `NULL` — there is no earlier month. That is correct, not a bug.

The `CASE WHEN invoice_month = '2011-12'` flag marks the nine-day month. I chose to flag
rather than delete it so nobody is surprised by a missing month, but every growth figure
excludes it.

**Why the chart exists:** a monthly revenue chart is the fastest way to see seasonality.
One look shows the September–November ramp and the February trough.

### `03_top_products.sql` — share of total with a window

```sql
ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS share_of_total_pct
```

`SUM(SUM(revenue)) OVER ()` looks strange but is a neat trick. The inner `SUM(revenue)`
is the normal group total. The outer `SUM(...) OVER ()` — with an **empty** `OVER()`, so no
partitioning and no ordering — totals that across all groups, giving the grand total on
every row. Dividing by it turns the group total into a percentage.

Note `100.0` not `100`: in SQLite, integer ÷ integer truncates, so `100` would give zeros.

**Why revenue rather than units:** the best-selling product by units is a cheap item sold
in bulk, which tells you very little about where the money is.

### `04_product_categories.sql` — `CASE WHEN`, and its limits

The dataset has no category column, so I build one with `CASE WHEN ... LIKE '%...%'`.

The critical detail: **`CASE` stops at the first matching branch.** So "CHRISTMAS CANDLE"
is counted as Christmas, not Candles, because the Christmas branch comes first. Reordering
the branches changes the answer. I put seasonal first on purpose — at this retailer the
Christmas range is a buying decision in its own right.

About 19% of revenue lands in `Other`. I report that number rather than hide it, because
it is the honest measure of how good the grouping is. If anyone asked me to improve it, the
answer is a proper product master file, not more keywords.

### `05_sales_by_country.sql` — `RANK()`

`RANK() OVER (ORDER BY SUM(revenue) DESC)` numbers the countries by revenue. Worth knowing
the difference between the three ranking functions:

| Function | On a tie | Next value |
|---|---|---|
| `ROW_NUMBER()` | arbitrary distinct numbers | continues |
| `RANK()` | same number | skips (1, 2, 2, 4) |
| `DENSE_RANK()` | same number | no gap (1, 2, 2, 3) |

### `06_customer_purchase_patterns.sql` — CTEs and `NTILE`

Three chained CTEs: totals per customer → add bands → aggregate the bands. A CTE is just a
named temporary result, written `WITH name AS (...)`. Chaining them keeps each step
readable; the alternative is one deeply nested subquery.

`NTILE(10) OVER (ORDER BY total_spend DESC)` splits customers into ten equal-sized groups
by spend. It is the simplest way to show revenue concentration.

`WHERE customer_id IS NOT NULL` is what restricts this query to 77% of revenue. Use
`IS NOT NULL`, never `!= NULL` — in SQL, anything compared with `NULL` is unknown, so
`customer_id != NULL` returns no rows at all.

### `07_order_value_distribution.sql` — why the mean is not enough

The mean order value is £485; the median is £299. The mean is 62% higher because a small
number of very large wholesale orders pull it up. Bands show the real shape: 2.9% of orders
exceed £2,000 and produce 27.6% of revenue.

The `a.`, `b.`, `c.` prefixes on the band labels exist so `ORDER BY order_value_band` sorts
them in the right order — alphabetically, "GBP 50-150" would come before "Under GBP 50".
A small, practical trick.

### `08_cancellation_rate.sql` — `LEFT JOIN` and `COALESCE`

Two CTEs (monthly sales, monthly credits) joined on month. A `LEFT JOIN` keeps every month
that has sales even if it has no credits; an inner join would silently drop such a month.
`COALESCE(x, 0)` turns the resulting `NULL` into `0` so the percentage still calculates.

**Be able to say:** "`LEFT JOIN` keeps all rows from the left table. I used it because a
month with no credit notes should still appear, showing zero."

### `09_top_customers_by_country.sql` — the top-N-per-group pattern

```sql
ROW_NUMBER() OVER (PARTITION BY cc.country ORDER BY cc.total_spend DESC) AS rn
...
WHERE rn <= 3
```

`PARTITION BY country` restarts the numbering for each country, so `rn <= 3` gives the top
three *per country* instead of the top three overall. This is the standard "top N per
group" pattern and a very common interview question.

Note the filtering happens in an outer query. You cannot write `WHERE ROW_NUMBER() ... <= 3`
directly, because `WHERE` is evaluated before window functions.

`HAVING SUM(revenue) > 100000` in the `country_totals` CTE keeps only markets above £100k.
`HAVING` filters *after* grouping; `WHERE` filters *before*. That is another standard
question.

This query produced the most surprising finding in the project: one Dutch customer is
95.8% of Dutch revenue.

### `10_when_orders_happen.sql` — the sanity check that found something

A simple `GROUP BY weekday`. The result: 30 Saturday orders in two years, against 8,120 on
Thursdays. That is not a shopping pattern, it is almost certainly a gap in the data.

**The lesson:** run the boring descriptive queries. They are where you find out whether you
can trust the dataset.

### `11_year_on_year.sql` — picking a fair comparison

The data runs 1 Dec 2009 to 9 Dec 2011. Calendar 2010 vs calendar 2011 would be unfair,
because 2011 is missing almost all of December — the biggest trading month. So I compare
**Dec 2009–Nov 2010 against Dec 2010–Nov 2011**: two complete, equal, like-for-like
12-month windows.

This is the single most important analytical judgement in the project, and it changes the
story. Growth of +2.2% on revenue with −3.8% orders and −6.3% units means something quite
different from "sales are up".

### `12_repeat_customer_share.sql` — new vs returning

Find each customer's first order date, then label each order by comparing against it.

```sql
CASE WHEN s.invoice_day = f.first_day THEN 'New customer' ELSE 'Returning customer' END
```

The honest caveat is in the file's comments: a customer whose first-ever purchase was
before December 2009 is wrongly labelled "new" here, because the data does not go back far
enough. That is why December 2009 shows only 38% returning revenue while later months show
around 91%. The early months are an artifact of where the data starts — not a trend.

---

## 4. How each headline figure is calculated

| Figure | Calculation | Where |
|---|---|---|
| Revenue £19,097,385 | `SUM(quantity × price)` over the clean sales table | `01_overview.sql` |
| Orders 39,336 | `COUNT(DISTINCT invoice)` | `01_overview.sql` |
| Average order value £485.49 | revenue ÷ distinct invoices | `01_overview.sql` |
| Median order value £299.34 | order totals sorted, middle value | `04_export_for_website.py` |
| YoY revenue +2.2% | (£9,425,361 ÷ £9,226,575) − 1 | `11_year_on_year.sql` |
| Autumn share 36.8% | Sep+Oct+Nov revenue ÷ total complete-month revenue | `04_export_for_website.py` |
| Peak-to-trough 2.9× | Nov 2011 £1,441,526 ÷ Feb 2011 £504,844 | `04_export_for_website.py` |
| Top 16.4% of customers → 67.7% of revenue | customers with 10+ orders, as % of identified customers and of their revenue | `06_customer_purchase_patterns.sql` |
| Dutch concentration 95.8% | top Dutch customer's spend ÷ Dutch revenue | `09_top_customers_by_country.sql` |

---

## 5. Why each chart exists

A chart should answer a question. These are the questions:

| Chart | Question it answers |
|---|---|
| Monthly revenue column chart with 3-month moving average | Is the business growing, and how seasonal is it? The moving average is there because the month-to-month swings are large enough to hide the underlying level. |
| Revenue by category (horizontal bars) | Which ranges carry the business? Horizontal because the labels are long. |
| Average order value by market (columns) | Are export customers different from UK customers? This is where the wholesale pattern shows up. |
| Share of customers vs share of revenue (paired columns) | How concentrated is revenue? Two bars side by side make the gap between 16% of customers and 68% of revenue obvious instantly. |
| New vs returning revenue (stacked) | How dependent is the business on repeat buyers? |

Charts I deliberately did **not** make: a pie chart of 43 countries (unreadable), and
anything 3-D.

---

## 6. Likely interview questions

**"Walk me through how you cleaned this data."**
Seven steps, all logged with row counts. Duplicates, credit notes, bad-debt adjustments,
impossible values, non-product lines, missing descriptions, and matching cancelled sales
back to their credit notes. The last one changed revenue by 2.8%.

**"What was the hardest part?"**
Realising that removing credit notes without removing the matching sale leaves cancelled
orders in revenue. I found it by investigating an outlier in the top-products list.

**"Why is average order value calculated that way?"**
Because a row is a product line, not an order. Revenue ÷ `COUNT(DISTINCT invoice)` gives
order value; `AVG(revenue)` would give line value, around £19.

**"23% of rows have no customer ID. What did you do?"**
Kept them for revenue, excluded them from per-customer analysis, and stated that wherever
it matters. Treating blank as a single customer would invent a customer worth 23% of
revenue.

**"The business says sales grew. Do you agree?"**
Revenue grew 2.2% like-for-like, yes. But orders fell 3.8% and units fell 6.3% — growth
came entirely from a 6.2% rise in average order value. Whether that is good depends on
whether prices rose or the customer mix shifted towards wholesale, and I cannot tell which
from this data.

**"What would you do with more data?"**
Product costs, to talk about margin instead of revenue. Marketing spend by channel, to say
anything about acquisition. And a product master file, to replace my keyword categories.

**"What's the difference between `WHERE` and `HAVING`?"**
`WHERE` filters rows before grouping; `HAVING` filters groups after. `09_top_customers_by_country.sql`
uses `HAVING SUM(revenue) > 100000` because the condition is on a group total.

**"Explain a window function."**
It calculates across a set of rows related to the current row, without collapsing them into
one row like `GROUP BY` does. In `02_monthly_sales_trend.sql`, `LAG(revenue)` gives the
previous month's revenue while keeping one row per month.

**"How confident are you in the £19.1m figure?"**
Confident that it follows from the cleaning rules, which are all documented. It is still
slightly overstated, because £916k of credit notes could not be matched to a specific sale.
I would quote it as "about £19.1m" and mention the credits.

---

## 7. Exercises

Do these yourself. Answers are reachable with the SQL already in the repository.

### Beginner

1. Total revenue for 2010 only. *(Hint: `WHERE invoice_month LIKE '2010-%'`.)*
2. The 10 products with the highest **unit** sales. Compare with the top 10 by revenue —
   how many appear in both lists?
3. How many customers placed exactly one order? What share of revenue is that?
4. Revenue for Germany and France separately, each month of 2011.

### Intermediate

5. Rewrite `07_order_value_distribution.sql` with bands of your own choosing. Does the
   conclusion about large orders survive?
6. Add a `DENSE_RANK()` column to `05_sales_by_country.sql` next to `RANK()`. Construct a
   case where they differ.
7. Calculate average order value by month for the UK and for non-UK separately. Does the
   6.2% rise in AOV come from one of them or both?
8. Using `cancellations`, find the five products with the highest credit rate (credited
   value ÷ sales value). Does anything look like a quality problem?

### Harder

9. Find customers who ordered in the first half of 2010 but never again. How much revenue
   did they represent? *(This is the start of churn analysis — Project 3 goes further.)*
10. Reproduce the step 7 reversal matching in pure SQL instead of pandas, using
    `ROW_NUMBER()` in place of `cumcount()`. Do you get 5,990 matches?
11. Change the `CASE WHEN` order in `04_product_categories.sql` so Christmas comes last.
    How much revenue moves, and which category gains most?

### Excel

12. In `excel/ecommerce_sales_dashboard.xlsx`, click any cell in the Monthly sheet's
    "mom change" column and read the formula. Then add a column computing each month's
    share of annual revenue.
13. Rebuild the "Revenue by category" chart as a PivotChart from `outputs/tables/04_product_categories.csv`.
14. Add a KPI to the Dashboard sheet: revenue per active customer per month.

---

## 8. Things I would do differently next time

- **Check for cancelled sales before writing any analysis.** I built the top-products table
  twice because of this.
- **Decide on the comparison window first.** I wrote monthly trends before noticing the
  partial December, which meant redoing the growth figures.
- **Write the data-quality queries earlier.** `10_when_orders_happen.sql` took two minutes
  and told me the weekend data is unreliable. That belonged at the start, not the end.
