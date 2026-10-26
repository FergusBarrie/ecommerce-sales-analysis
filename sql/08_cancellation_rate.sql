-- 08_cancellation_rate.sql
-- How much value is credited back each month, and how much of it I was able
-- to match to the original sale.
--
-- During cleaning I split credit notes (invoices starting with 'C') into their
-- own table and flagged the ones I could pair with the exact sale they
-- reverse. Those sales have already been removed from the sales table, so the
-- revenue column below is net of them. The unmatched credits are mostly
-- partial returns, postage refunds and credits with no customer ID; they still
-- reduce the money the business keeps, so I report them separately instead of
-- pretending the revenue figure is exact.
--
-- A LEFT JOIN is the right choice here: every month has sales, but a month
-- might have no credits at all, and I do not want to lose that month.

WITH monthly_sales AS (
    SELECT invoice_month,
           ROUND(SUM(revenue), 2)  AS net_revenue,
           COUNT(DISTINCT invoice)  AS orders
    FROM sales
    GROUP BY invoice_month
),
monthly_credits AS (
    SELECT invoice_month,
           ROUND(ABS(SUM(CASE WHEN matched_to_sale = 1 THEN revenue ELSE 0 END)), 2) AS matched_credit,
           ROUND(ABS(SUM(CASE WHEN matched_to_sale = 0 THEN revenue ELSE 0 END)), 2) AS unmatched_credit,
           COUNT(DISTINCT invoice) AS credit_notes
    FROM cancellations
    GROUP BY invoice_month
)
SELECT
    s.invoice_month,
    s.net_revenue,
    s.orders,
    COALESCE(c.credit_notes, 0)      AS credit_notes,
    COALESCE(c.matched_credit, 0)    AS matched_credit_removed,
    COALESCE(c.unmatched_credit, 0)  AS unmatched_credit_remaining,
    ROUND(100.0 * COALESCE(c.unmatched_credit, 0) / s.net_revenue, 1) AS unmatched_credit_pct
FROM monthly_sales s
LEFT JOIN monthly_credits c ON s.invoice_month = c.invoice_month
ORDER BY s.invoice_month;
