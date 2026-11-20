-- Q10. What would a risk-based action plan look like, and who is affected?
-- For each tier: typical profile, and the action a card team could take.

SELECT
    r.risk_tier,
    COUNT(*)                                                     AS customers,
    ROUND(AVG(f.credit_limit), 0)                                AS avg_limit,
    ROUND(100 * AVG(f.sep_utilization), 0)                       AS avg_utilization_pct,
    ROUND(100 * AVG((f.sep_status >= 1)::INT), 0)                AS late_in_sept_pct,
    ROUND(AVG(f.months_late_count), 1)                           AS avg_late_months,
    CASE r.risk_tier
        WHEN '1. Low'       THEN 'Eligible for credit-line increases and retention offers'
        WHEN '2. Medium'    THEN 'Monitor monthly; payment reminders before due date'
        WHEN '3. High'      THEN 'Freeze line increases; proactive outreach and payment plans'
        ELSE                     'Reduce available credit; early collections contact'
    END AS suggested_action
FROM risk_scores r
JOIN customer_features f USING (customer_id)
GROUP BY 1
ORDER BY 1;
