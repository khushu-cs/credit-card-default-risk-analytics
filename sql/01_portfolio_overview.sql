-- Q1. What does the portfolio look like? Headline KPIs as of September 2005.
-- Business use: the first slide of any portfolio review.

SELECT
    COUNT(*)                                                    AS customers,
    ROUND(SUM(credit_limit) / 1e9, 2)                           AS total_credit_lines_bn,
    ROUND(AVG(credit_limit), 0)                                 AS avg_credit_limit,
    ROUND(SUM(GREATEST(sep_balance, 0)) / 1e9, 2)               AS total_balance_bn,
    ROUND(100 * SUM(GREATEST(sep_balance, 0)) / SUM(credit_limit), 1) AS portfolio_utilization_pct,
    ROUND(100 * AVG((sep_status >= 1)::INT), 1)                 AS late_in_september_pct,
    ROUND(100 * AVG(defaulted), 1)                              AS default_rate_pct,
    ROUND(SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1) / 1e9, 2) AS balance_of_defaulters_bn,
    ROUND(100 * SUM(GREATEST(sep_balance, 0)) FILTER (WHERE defaulted = 1)
          / SUM(GREATEST(sep_balance, 0)), 1)                   AS balance_at_risk_pct
FROM customer_features;
