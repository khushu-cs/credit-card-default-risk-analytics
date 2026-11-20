-- Q5. Which behaviours signal default before it happens?
-- Default rate next month by (a) September repayment status and (b) how many of the last 6 months were late.

SELECT 'September status' AS signal,
       CASE WHEN sep_status = -2 THEN '1. No balance' WHEN sep_status = -1 THEN '2. Paid in full'
            WHEN sep_status = 0 THEN '3. Revolving' WHEN sep_status = 1 THEN '4. 1 month late'
            WHEN sep_status = 2 THEN '5. 2 months late' ELSE '6. 3+ months late' END AS value,
       COUNT(*) AS customers, ROUND(100 * AVG(defaulted), 1) AS default_rate_pct
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Late months (of last 6)',
       CASE WHEN months_late_count >= 4 THEN '4-6 months' WHEN months_late_count = 1 THEN '1 month' ELSE months_late_count::INT || ' months' END,
       COUNT(*), ROUND(100 * AVG(defaulted), 1)
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Payment behaviour', payment_behaviour, COUNT(*), ROUND(100 * AVG(defaulted), 1)
FROM customer_features GROUP BY 1, 2
ORDER BY signal, value;
