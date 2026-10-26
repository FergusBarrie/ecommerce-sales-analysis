-- 01_overview.sql
-- Headline numbers for the whole cleaned dataset.
-- This is the first query I run on any new dataset: it tells me the size of
-- the business, the period covered, and whether the totals look sensible.

SELECT
    MIN(invoice_day)                                AS first_day,
    MAX(invoice_day)                                AS last_day,
    COUNT(*)                                        AS transaction_lines,
    COUNT(DISTINCT invoice)                         AS orders,
    COUNT(DISTINCT customer_id)                     AS identified_customers,
    COUNT(DISTINCT stock_code)                      AS products,
    COUNT(DISTINCT country)                         AS countries,
    ROUND(SUM(revenue), 2)                          AS total_revenue,
    SUM(quantity)                                   AS total_units,
    -- Average order value: total revenue divided by the number of distinct
    -- invoices, not the average of the revenue column (that would give the
    -- average line value, which is a different and much smaller number).
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value,
    ROUND(SUM(revenue) / SUM(quantity), 2)          AS avg_revenue_per_unit
FROM sales;
