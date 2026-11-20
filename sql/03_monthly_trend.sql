-- Q3. How did the portfolio move month by month (Apr–Sep 2005)?
-- "2+ months late" is used because 1-month-late codes are only recorded consistently in September
-- (see reports/data_quality.csv).

SELECT
    month,
    ROUND(SUM(GREATEST(bill_amount, 0)) / 1e9, 3)                       AS total_balance_bn,
    ROUND(100 * SUM(GREATEST(bill_amount, 0)) / SUM(credit_limit), 1)   AS utilization_pct,
    ROUND(SUM(payment_amount) / 1e9, 3)                                 AS payments_bn,
    ROUND(100 * AVG((repayment_status = -1)::INT), 1)                   AS paid_in_full_pct,
    ROUND(100 * AVG((repayment_status = 0)::INT), 1)                    AS revolving_pct,
    ROUND(100 * AVG((repayment_status >= 2)::INT), 1)                   AS late_2plus_months_pct
FROM statements
GROUP BY 1
ORDER BY 1;
