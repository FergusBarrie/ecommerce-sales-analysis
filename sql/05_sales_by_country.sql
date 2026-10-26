-- 05_sales_by_country.sql
-- Revenue by country, which is the closest thing this dataset has to a
-- region breakdown.
--
-- The retailer is based in the UK, so I expect the UK to dominate. The
-- interesting question is which export markets are worth attention, and
-- whether their average order value differs from the UK.

SELECT
    country,
    COUNT(DISTINCT invoice)                          AS orders,
    COUNT(DISTINCT customer_id)                      AS customers,
    ROUND(SUM(revenue), 2)                           AS revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS share_of_revenue_pct,
    RANK() OVER (ORDER BY SUM(revenue) DESC)         AS revenue_rank
FROM sales
GROUP BY country
ORDER BY revenue DESC;
