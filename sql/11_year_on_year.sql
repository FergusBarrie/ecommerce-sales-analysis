-- 11_year_on_year.sql
-- A like-for-like comparison of the two years in the dataset.
--
-- The data runs from 2009-12-01 to 2011-12-09. That is not two calendar
-- years, but it does contain two complete 12-month periods:
--     Year 1 = Dec 2009 to Nov 2010
--     Year 2 = Dec 2010 to Nov 2011
-- Comparing those two windows is fair. Comparing calendar 2010 with calendar
-- 2011 would not be, because 2011 is missing most of December - the single
-- biggest trading month of the year.
--
-- The nine days of December 2011 are excluded from both periods.

WITH periods AS (
    SELECT
        CASE WHEN invoice_month BETWEEN '2009-12' AND '2010-11' THEN 'Year 1 (Dec 2009 - Nov 2010)'
             WHEN invoice_month BETWEEN '2010-12' AND '2011-11' THEN 'Year 2 (Dec 2010 - Nov 2011)'
             ELSE 'Excluded (partial Dec 2011)'
        END AS period,
        invoice, customer_id, quantity, revenue, country
    FROM sales
)
SELECT
    period,
    COUNT(DISTINCT invoice)                          AS orders,
    COUNT(DISTINCT customer_id)                      AS active_customers,
    SUM(quantity)                                    AS units,
    ROUND(SUM(revenue), 2)                           AS revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value,
    ROUND(SUM(revenue) / COUNT(DISTINCT customer_id), 2) AS revenue_per_active_customer,
    ROUND(100.0 * SUM(CASE WHEN country = 'United Kingdom' THEN revenue ELSE 0 END)
          / SUM(revenue), 1)                         AS uk_share_of_revenue_pct
FROM periods
WHERE period <> 'Excluded (partial Dec 2011)'
GROUP BY period
ORDER BY period;
