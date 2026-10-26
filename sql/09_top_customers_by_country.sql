-- 09_top_customers_by_country.sql
-- The three biggest customers in each of the top export markets.
--
-- This is the query where the JOIN and the window function really earn their
-- place. ROW_NUMBER() PARTITION BY country restarts the numbering for every
-- country, so filtering on rn <= 3 gives a top-three per country rather than
-- a top-three overall.

WITH customer_country AS (
    SELECT
        country,
        customer_id,
        COUNT(DISTINCT invoice) AS orders,
        ROUND(SUM(revenue), 2)  AS total_spend
    FROM sales
    WHERE customer_id IS NOT NULL
    GROUP BY country, customer_id
),
country_totals AS (
    SELECT country, ROUND(SUM(revenue), 2) AS country_revenue
    FROM sales
    GROUP BY country
    HAVING SUM(revenue) > 100000          -- only markets large enough to matter
),
ranked AS (
    SELECT
        cc.country,
        cc.customer_id,
        cc.orders,
        cc.total_spend,
        ct.country_revenue,
        ROW_NUMBER() OVER (PARTITION BY cc.country ORDER BY cc.total_spend DESC) AS rn
    FROM customer_country cc
    JOIN country_totals ct ON cc.country = ct.country
)
SELECT
    country,
    rn AS rank_in_country,
    customer_id,
    orders,
    total_spend,
    country_revenue,
    ROUND(100.0 * total_spend / country_revenue, 1) AS pct_of_country_revenue
FROM ranked
WHERE rn <= 3
ORDER BY country_revenue DESC, rn;
