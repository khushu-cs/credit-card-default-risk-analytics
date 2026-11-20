-- Q6. Does using more of the credit line mean more risk, and does it depend on the size of the line?
-- Default rate by September utilization band and credit-limit band.

SELECT
    limit_band,
    utilization_band,
    COUNT(*)                          AS customers,
    ROUND(100 * AVG(defaulted), 1)    AS default_rate_pct
FROM customer_features
GROUP BY 1, 2
ORDER BY 1, 2;
