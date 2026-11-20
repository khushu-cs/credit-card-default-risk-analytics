-- Q9. How should the bank act on the model? Customers grouped into risk tiers by predicted probability of default.
-- Compares predicted vs actual default rate (calibration) and shows where balances at risk sit.
-- Tiers: Low < 10% · Medium 10–25% · High 25–50% · Very high 50%+ predicted chance of default.

SELECT
    r.risk_tier,
    COUNT(*)                                                           AS customers,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                   AS pct_customers,
    ROUND(100 * AVG(r.pd_score), 1)                                    AS predicted_default_pct,
    ROUND(100 * AVG(f.defaulted), 1)                                   AS actual_default_pct,
    ROUND(SUM(GREATEST(f.sep_balance, 0)) / 1e6, 1)                    AS balance_m,
    ROUND(100 * SUM(f.defaulted) / SUM(SUM(f.defaulted)) OVER (), 1)   AS pct_of_all_defaulters,
    ROUND(100 * SUM(GREATEST(f.sep_balance, 0)) FILTER (WHERE f.defaulted = 1)
          / SUM(SUM(GREATEST(f.sep_balance, 0)) FILTER (WHERE f.defaulted = 1)) OVER (), 1) AS pct_of_defaulted_balance
FROM risk_scores r
JOIN customer_features f USING (customer_id)
GROUP BY 1
ORDER BY 1;
