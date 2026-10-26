-- 06_customer_purchase_patterns.sql
-- How often customers order, and how concentrated revenue is.
--
-- Only rows with a customer ID can be used here, so this query covers about
-- 77% of revenue. The remaining rows have no ID at all (they are not a single
-- anonymous customer, they are unknown), so counting them would be wrong.
--
-- NTILE(10) splits customers into ten equal-sized groups ordered by spend,
-- which is an easy way to show revenue concentration without a complicated
-- calculation.

WITH customer_totals AS (
    SELECT
        customer_id,
        COUNT(DISTINCT invoice)                          AS orders,
        ROUND(SUM(revenue), 2)                           AS total_spend,
        ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value,
        MIN(invoice_day)                                 AS first_order_day,
        MAX(invoice_day)                                 AS last_order_day
    FROM sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
banded AS (
    SELECT
        *,
        CASE WHEN orders = 1 THEN '1 order'
             WHEN orders BETWEEN 2 AND 3  THEN '2-3 orders'
             WHEN orders BETWEEN 4 AND 9  THEN '4-9 orders'
             ELSE '10+ orders'
        END AS order_band,
        NTILE(10) OVER (ORDER BY total_spend DESC) AS spend_decile
    FROM customer_totals
)
SELECT
    order_band,
    COUNT(*)                                           AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_customers,
    ROUND(SUM(total_spend), 2)                         AS revenue,
    ROUND(100.0 * SUM(total_spend) / SUM(SUM(total_spend)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(avg_order_value), 2)                     AS mean_avg_order_value
FROM banded
GROUP BY order_band
ORDER BY revenue DESC;
