-- Q7. How do customers pay, and where does the money at risk sit?
-- Segments built from 6 months of bills and payments (see customer_features in 00_setup.sql).

SELECT
    payment_behaviour,
    COUNT(*)                                                         AS customers,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                 AS pct_customers,
    ROUND(100 * AVG(defaulted), 1)                                   AS default_rate_pct,
    ROUND(SUM(GREATEST(sep_balance, 0)) / 1e6, 1)                    AS balance_m,
    ROUND(100 * SUM(GREATEST(sep_balance, 0)) / SUM(SUM(GREATEST(sep_balance, 0))) OVER (), 1) AS pct_of_balances,
    ROUND(100 * SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1)
          / SUM(SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1)) OVER (), 1)        AS pct_of_defaulted_balances,
    ROUND(AVG(credit_limit), 0)                                      AS avg_limit
FROM customer_features
GROUP BY 1
ORDER BY 1;
