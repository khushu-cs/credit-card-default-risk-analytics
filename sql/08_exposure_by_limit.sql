-- Q8. Where is the money at risk? Balances owed by customers who defaulted, by credit-limit band.
-- Low-limit customers default more often, but high-limit customers can carry more of the dollars at risk.

SELECT
    limit_band,
    COUNT(*)                                                        AS customers,
    ROUND(100 * AVG(defaulted), 1)                                  AS default_rate_pct,
    ROUND(SUM(GREATEST(sep_balance, 0)) / 1e6, 1)                   AS balance_m,
    ROUND(SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1) / 1e6, 1) AS defaulted_balance_m,
    ROUND(100 * SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1)
          / SUM(SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1)) OVER (), 1) AS pct_of_all_defaulted_balance
FROM customer_features
GROUP BY 1
ORDER BY 1;
