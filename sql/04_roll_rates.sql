-- Q4. Roll rates: where does each account go the next month?
-- Rows = status this month, columns = share of accounts in each status the following month.
-- Credit-risk teams use this "transition matrix" to forecast how many accounts will reach default.

WITH pairs AS (
    SELECT
        status_group AS from_status,
        LEAD(status_group) OVER (PARTITION BY customer_id ORDER BY month) AS to_status
    FROM statements
)
SELECT
    from_status,
    COUNT(*) AS account_months,
    ROUND(100 * AVG((to_status = '1. No balance')::INT), 1)       AS to_no_balance_pct,
    ROUND(100 * AVG((to_status = '2. Paid in full')::INT), 1)     AS to_paid_in_full_pct,
    ROUND(100 * AVG((to_status = '3. Revolving')::INT), 1)        AS to_revolving_pct,
    ROUND(100 * AVG((to_status = '4. 1-2 months late')::INT), 1)  AS to_1_2_late_pct,
    ROUND(100 * AVG((to_status = '5. 3+ months late')::INT), 1)   AS to_3plus_late_pct
FROM pairs
WHERE to_status IS NOT NULL
GROUP BY 1
ORDER BY 1;
