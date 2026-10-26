-- 12_repeat_customer_share.sql
-- For each month, how much revenue came from customers who had already
-- bought before, and how much from customers buying for the first time?
--
-- The logic: find each customer's first order date, then label every order as
-- "first order" or "repeat order" by comparing it with that date. This is the
-- simplest version of a returning-customer measure and it is easy to explain.
--
-- Caveat: customers who first bought before 2009-12-01 look like new
-- customers here, because the data does not go back far enough to know
-- otherwise. That makes the first few months look more new-customer heavy
-- than they really were.

WITH first_order AS (
    SELECT customer_id, MIN(invoice_day) AS first_day
    FROM sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
labelled AS (
    SELECT
        s.invoice_month,
        s.invoice,
        s.revenue,
        CASE WHEN s.invoice_day = f.first_day THEN 'New customer'
             ELSE 'Returning customer'
        END AS customer_type
    FROM sales s
    JOIN first_order f ON s.customer_id = f.customer_id
)
SELECT
    invoice_month,
    ROUND(SUM(CASE WHEN customer_type = 'New customer'       THEN revenue ELSE 0 END), 2) AS new_customer_revenue,
    ROUND(SUM(CASE WHEN customer_type = 'Returning customer' THEN revenue ELSE 0 END), 2) AS returning_customer_revenue,
    COUNT(DISTINCT CASE WHEN customer_type = 'New customer'       THEN invoice END) AS new_customer_orders,
    COUNT(DISTINCT CASE WHEN customer_type = 'Returning customer' THEN invoice END) AS returning_customer_orders,
    ROUND(100.0 * SUM(CASE WHEN customer_type = 'Returning customer' THEN revenue ELSE 0 END)
          / SUM(revenue), 1) AS returning_share_of_revenue_pct
FROM labelled
GROUP BY invoice_month
ORDER BY invoice_month;
