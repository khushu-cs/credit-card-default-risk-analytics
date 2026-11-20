-- Q2. Which customer groups default most? Default rate by demographic and credit-limit segment.
-- Business use: understanding where risk sits. Note: sex is shown for analysis only;
-- US fair-lending law (ECOA) does not allow sex to be used in credit decisions.

SELECT 'Credit limit (NT$)' AS dimension, limit_band AS segment,
       COUNT(*) AS customers, ROUND(100 * AVG(defaulted), 1) AS default_rate_pct,
       ROUND(AVG(credit_limit), 0) AS avg_limit
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Age', age_band, COUNT(*), ROUND(100 * AVG(defaulted), 1), ROUND(AVG(credit_limit), 0)
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Education', education, COUNT(*), ROUND(100 * AVG(defaulted), 1), ROUND(AVG(credit_limit), 0)
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Marital status', marital_status, COUNT(*), ROUND(100 * AVG(defaulted), 1), ROUND(AVG(credit_limit), 0)
FROM customer_features GROUP BY 1, 2
UNION ALL
SELECT 'Sex', sex, COUNT(*), ROUND(100 * AVG(defaulted), 1), ROUND(AVG(credit_limit), 0)
FROM customer_features GROUP BY 1, 2
ORDER BY dimension, segment;
