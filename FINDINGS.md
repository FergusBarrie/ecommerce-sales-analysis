# Findings — E-commerce Sales Analysis

**Business question:** Where does this retailer's revenue actually come from, and how did
it change between December 2009 and December 2011?

Every number below comes from the SQL in [`sql/`](sql/), run against the cleaned data.
The CSV behind each table is named so you can check it.

---

## 1. The business at a glance

`outputs/tables/01_overview.csv`

| Metric | Value |
|---|---|
| Period | 1 Dec 2009 – 9 Dec 2011 |
| Revenue | £19,097,385 |
| Orders | 39,336 |
| Transaction lines | 997,367 |
| Average order value | £485.49 |
| Median order value | £299.34 |
| Units sold | 10,798,048 |
| Identified customers | 5,839 |
| Products | 4,718 |
| Countries | 43 |

The gap between the mean (£485) and median (£299) order is the first thing worth noticing.
It says the order size distribution has a long right tail — a few very large orders. That
turns out to matter (section 5).

---

## 2. Growth came from bigger orders, not more of them

`outputs/tables/11_year_on_year.csv`

The data covers two complete 12-month windows. I compare those rather than calendar years,
because December 2011 is only nine days long and December is the biggest trading month —
a calendar comparison would make 2011 look like a collapse.

| | Dec 2009 – Nov 2010 | Dec 2010 – Nov 2011 | Change |
|---|---|---|---|
| Revenue | £9,226,575 | £9,425,361 | **+2.2%** |
| Orders | 19,633 | 18,890 | **−3.8%** |
| Units | 5,455,072 | 5,111,759 | **−6.3%** |
| Average order value | £469.95 | £498.96 | **+6.2%** |
| Active customers | 4,226 | 4,284 | +1.4% |
| UK share of revenue | 86.2% | 84.5% | −1.7pp |

Revenue is up, but the business handled fewer orders and shipped fewer items. All of the
growth came from a 6.2% rise in average order value.

I cannot tell from this data *why* average order value rose. The two plausible explanations
are higher prices and a shift in customer mix towards larger wholesale buyers. Both are
consistent with the UK share falling, since export orders are much larger (section 4).
Separating them would need a price list over time, which the dataset does not include.

---

## 3. Trading is strongly seasonal

`outputs/tables/02_monthly_sales_trend.csv`

| | Month | Revenue |
|---|---|---|
| Best month | November 2011 | £1,441,526 |
| Worst month | February 2011 | £504,844 |
| Ratio | | **2.9×** |

September to November produced **36.8%** of all revenue — three months out of every
twelve carrying over a third of the year. The pattern repeats in both years, so it is
seasonality rather than a one-off.

The shape is consistent with a gift retailer selling to shops that stock up before
Christmas. Note the drop in *December* itself: December 2010 fell 45.7% from November.
The retailer's peak is when its customers buy for Christmas, not when consumers do.

---

## 4. Export markets are individual accounts, not markets

`outputs/tables/05_sales_by_country.csv` and `09_top_customers_by_country.csv`

| Country | Revenue | Share | Avg order value | Customers |
|---|---|---|---|---|
| United Kingdom | £16,320,358 | 85.5% | £453 | 5,326 |
| Ireland (EIRE) | £606,326 | 3.2% | £1,047 | 3 |
| Netherlands | £546,889 | 2.9% | £2,544 | 22 |
| Germany | £380,127 | 2.0% | £505 | 107 |
| France | £296,064 | 1.6% | £495 | 93 |
| Australia | £166,770 | 0.9% | £1,939 | 15 |

Two things stand out.

**Export orders are much larger.** A Dutch order averages £2,544 against £453 in the UK.
These are almost certainly wholesale buyers rather than consumers.

**And the big export markets are one or two customers each:**

| Market | Concentration |
|---|---|
| Netherlands | one customer = **95.8%** of the country's revenue |
| Ireland | two customers = **92.1%** of the country's revenue |
| Germany | top three = 22.7% |
| France | top three = 28.7% |

Calling the Netherlands the third-largest "market" is misleading. It is one account. By
contrast Germany and France look like genuine markets with over 90 customers each.

---

## 5. Revenue depends on repeat buyers and large orders

`outputs/tables/06_customer_purchase_patterns.csv` (identified customers only — 77% of revenue)

| Orders placed | Customers | % of customers | Revenue | % of revenue |
|---|---|---|---|---|
| 10+ | 959 | 16.4% | £11,181,686 | **67.7%** |
| 4–9 | 1,654 | 28.3% | £3,425,705 | 20.7% |
| 2–3 | 1,613 | 27.6% | £1,361,447 | 8.2% |
| 1 | 1,613 | 27.6% | £553,268 | **3.3%** |

`outputs/tables/12_repeat_customer_share.csv`

In a typical month, **about 91%** of revenue came from customers who had bought before.
(The first few months of the data show less, but that is an artifact: customers whose
first-ever purchase predates December 2009 look like new customers because the data does
not go back far enough.)

`outputs/tables/07_order_value_distribution.csv`

| Order value | Orders | % of orders | % of revenue |
|---|---|---|---|
| Under £50 | 3,403 | 8.7% | 0.4% |
| £50–150 | 6,507 | 16.5% | 3.7% |
| £150–350 | 14,279 | 36.3% | 18.8% |
| £350–750 | 9,948 | 25.3% | 25.7% |
| £750–2,000 | 4,052 | 10.3% | 24.0% |
| £2,000+ | 1,147 | **2.9%** | **27.6%** |

The top 2.9% of orders produce more revenue than the bottom 61.5% combined.

---

## 6. No single product carries the business

`outputs/tables/03_top_products.csv`

| Product | Units | Revenue | Share |
|---|---|---|---|
| REGENCY CAKESTAND 3 TIER | 25,796 | £322,806 | 1.69% |
| WHITE HANGING HEART T-LIGHT HOLDER | 91,294 | £252,346 | 1.32% |
| PARTY BUNTING | 28,002 | £147,460 | 0.77% |
| JUMBO BAG RED RETROSPOT | 76,802 | £146,484 | 0.77% |
| ASSORTED COLOUR BIRD ORNAMENT | 79,632 | £128,654 | 0.67% |

The top 10 products together are only **7.3%** of revenue, across 4,718 products. The
retailer's revenue comes from breadth of range, not from hero products. This is the
opposite of the concentration seen in customers, and it is worth saying explicitly because
"find our best product" is a question that does not have a useful answer here.

By my keyword grouping (`outputs/tables/04_product_categories.csv`): Kitchen & Baking
18.3%, Home Decor 15.5%, Bags 10.2%, Storage & Boxes 9.2%, Candles & Lighting 9.1%, with
19.2% unmatched in "Other". Treat this as indicative — see the limitation below.

---

## 7. Data quality notes worth reporting

These are not side notes; two of them changed the numbers.

**Cancelled orders were being counted as revenue.** The dataset's two largest sales —
£168,470 of paper craft and £77,184 of storage jars — were each credited back in full
within two days. Separating credit notes without removing the matching sale left them in
the totals. Matching them back reduced revenue from £19.64m to £19.10m (−2.8%) and removed
both items from the best-sellers list. See
[`LEARNING_GUIDE.md`](LEARNING_GUIDE.md#step-7--the-one-i-nearly-missed-matching-cancelled-sales).

**£916k of credit notes could not be matched** to a specific sale line (partial returns,
postage refunds, credits with no customer ID). That is 4.8% of revenue, so £19.10m is still
a slight overstatement. `outputs/tables/08_cancellation_rate.csv` shows it month by month.

**There are 30 Saturday orders in two years,** against 8,120 on an average Thursday. This
is a gap in the data, not a shopping pattern. Any day-of-week conclusion from this dataset
should be treated carefully.

**22.7% of transaction lines have no customer ID.** Included in revenue, excluded from
per-customer figures.

---

## Recommendations

**1. Treat the largest accounts as a commercial risk and give them named contacts.**
One Dutch customer is 2.7% of total revenue on its own; two Irish accounts are another
2.9%. Country-level reporting hides this completely. The practical step is simple account
management, plus reporting revenue by account alongside revenue by country.

**2. Plan stock, cash and warehouse staffing around the autumn peak.**
November trades at 2.9 times February, and September–November is 36.8% of the year.
Planning on an average month means running short in the peak and holding too much stock in
spring. The monthly series in `outputs/tables/02_monthly_sales_trend.csv` is a reasonable
basis for that planning, since the pattern repeated in both years.

**3. Test whether one-time buyers can be converted into second-time buyers.**
They are 27.6% of identified customers and 3.3% of revenue. Customers who reach 10+ orders
are worth around £11,660 each on average, so a second order is the step that matters most.

I have deliberately not put a dollar value on recommendation 3. The data contains no
marketing costs and no channel information, so any figure I gave would be invented. What I
can say is which group is largest and what it is currently worth.

## Limitations

1. **Revenue only — no costs.** Nothing here speaks to profitability.
2. **No marketing, channel or campaign data,** so nothing here explains *why* anything
   changed.
3. **My categories are keyword-based** and leave 19.2% in "Other".
4. **Customer figures cover 77% of revenue** because of the missing IDs.
5. **£916k of unmatched credits** mean revenue is slightly overstated.
6. **Weekend data looks incomplete.**
7. **The data is from 2009–2011,** and the UK was coming out of recession during it. The
   patterns are real but not current.
8. **One retailer, one sector.** None of this generalises.
