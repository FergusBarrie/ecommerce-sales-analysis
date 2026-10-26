-- 02_monthly_sales_trend.sql
-- Monthly revenue, order count and average order value, plus the
-- month-on-month change and a running total.
--
-- Two things worth knowing about this output:
--   1. The data starts on 2009-12-01 and ends on 2011-12-09, so the final
--      month (2011-12) only covers nine days. I flag it rather than delete
--      it, and I exclude it from any growth comparison.
--   2. LAG() and SUM() OVER are window functions. They let me compare a row
--      with the previous row without writing a self-join.

WITH monthly AS (
    SELECT
        invoice_month,
        ROUND(SUM(revenue), 2)                           AS revenue,
        COUNT(DISTINCT invoice)                          AS orders,
        COUNT(DISTINCT customer_id)                      AS active_customers,
        SUM(quantity)                                    AS units,
        ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value
    FROM sales
    GROUP BY invoice_month
)
SELECT
    invoice_month,
    revenue,
    orders,
    active_customers,
    units,
    avg_order_value,
    LAG(revenue) OVER (ORDER BY invoice_month) AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY invoice_month))
        / LAG(revenue) OVER (ORDER BY invoice_month), 1
    )                                          AS mom_change_pct,
    ROUND(SUM(revenue) OVER (ORDER BY invoice_month), 2) AS running_total_revenue,
    CASE WHEN invoice_month = '2011-12' THEN 'partial month (9 days only)'
         ELSE 'complete month'
    END                                        AS month_status
FROM monthly
ORDER BY invoice_month;
