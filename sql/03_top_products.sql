-- 03_top_products.sql
-- The 20 products that brought in the most revenue over the two years.
--
-- I report revenue rather than units sold, because the cheapest items sell in
-- huge volumes without contributing much money. The share_of_total_pct column
-- uses SUM(...) OVER () - a window function with no ORDER BY, which gives the
-- grand total on every row so I can divide by it.

SELECT
    stock_code,
    description,
    SUM(quantity)                                     AS units_sold,
    COUNT(DISTINCT invoice)                           AS orders_containing_item,
    ROUND(SUM(revenue), 2)                            AS revenue,
    ROUND(AVG(price), 2)                              AS avg_unit_price,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS share_of_total_pct
FROM sales
GROUP BY stock_code, description
ORDER BY revenue DESC
LIMIT 20;
