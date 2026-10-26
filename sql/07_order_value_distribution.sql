-- 07_order_value_distribution.sql
-- How big is a typical order?
--
-- The average order value on its own is misleading if a few very large
-- wholesale orders pull it upwards. This query groups orders into value bands
-- so I can see the shape of the distribution and compare the average with the
-- median.

WITH order_totals AS (
    SELECT
        invoice,
        country,
        ROUND(SUM(revenue), 2) AS order_value
    FROM sales
    GROUP BY invoice, country
)
SELECT
    CASE WHEN order_value < 50                        THEN 'a. Under GBP 50'
         WHEN order_value <  150                      THEN 'b. GBP 50-150'
         WHEN order_value <  350                      THEN 'c. GBP 150-350'
         WHEN order_value <  750                      THEN 'd. GBP 350-750'
         WHEN order_value < 2000                      THEN 'e. GBP 750-2,000'
         ELSE                                              'f. GBP 2,000+'
    END                                               AS order_value_band,
    COUNT(*)                                          AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_orders,
    ROUND(SUM(order_value), 2)                        AS revenue,
    ROUND(100.0 * SUM(order_value) / SUM(SUM(order_value)) OVER (), 1) AS pct_of_revenue
FROM order_totals
GROUP BY order_value_band
ORDER BY order_value_band;
