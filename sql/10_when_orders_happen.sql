-- 10_when_orders_happen.sql
-- Which days of the week and which hours of the day produce the most orders.
--
-- This is a simple operational question: if the warehouse and customer
-- service team need to know when the work arrives, the answer is in the
-- invoice timestamps. There are no Saturday invoices in this dataset at all,
-- which is itself worth reporting.

SELECT
    weekday,
    COUNT(DISTINCT invoice)                          AS orders,
    ROUND(SUM(revenue), 2)                           AS revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value,
    MIN(hour)                                        AS earliest_hour,
    MAX(hour)                                        AS latest_hour
FROM sales
GROUP BY weekday
ORDER BY orders DESC;
