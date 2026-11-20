-- Setup: load the cleaned tables and build one feature row per customer.
-- Run from the project root (src/run_sql.py does this automatically).

CREATE OR REPLACE VIEW customers  AS SELECT * FROM read_csv_auto('data/clean/customers.csv');
CREATE OR REPLACE VIEW statements AS SELECT * FROM read_csv_auto('data/clean/statements.csv');

-- Payment ratio: how much of last month's bill was paid this month.
-- (payment_amount in month m is paid during month m, i.e. against the bill from month m-1)
CREATE OR REPLACE VIEW monthly_payments AS
SELECT
    customer_id,
    month,
    bill_amount,
    LEAD(payment_amount) OVER (PARTITION BY customer_id ORDER BY month) AS paid_next_month
FROM statements;

CREATE OR REPLACE VIEW customer_features AS
WITH agg AS (
    SELECT
        s.customer_id,
        MAX(s.repayment_status) FILTER (WHERE s.month = DATE '2005-09-01')  AS sep_status,
        MAX(s.months_late)                                                 AS max_months_late,
        SUM((s.repayment_status >= 1)::INT)                                AS months_late_count,
        AVG(s.utilization) FILTER (WHERE s.bill_amount > 0)                AS avg_utilization,
        MAX(s.utilization) FILTER (WHERE s.month = DATE '2005-09-01')      AS sep_utilization,
        MAX(s.bill_amount) FILTER (WHERE s.month = DATE '2005-09-01')      AS sep_balance,
        SUM(ABS(s.bill_amount))                                            AS total_abs_bills
    FROM statements s
    GROUP BY 1
),
pay AS (
    SELECT customer_id,
           SUM(LEAST(paid_next_month, GREATEST(bill_amount, 0)))           AS paid,
           SUM(GREATEST(bill_amount, 0))                                    AS billed
    FROM monthly_payments
    WHERE month < DATE '2005-09-01'
    GROUP BY 1
)
SELECT
    c.*,
    a.sep_status, a.max_months_late, a.months_late_count,
    COALESCE(a.avg_utilization, 0)              AS avg_utilization,
    GREATEST(COALESCE(a.sep_utilization, 0), 0) AS sep_utilization,
    a.sep_balance,
    CASE WHEN p.billed > 0 THEN p.paid / p.billed END AS pay_ratio,
    CASE
        WHEN a.total_abs_bills = 0                        THEN '5. Inactive'
        WHEN a.max_months_late >= 2 OR a.sep_status >= 1  THEN '4. Behind on payments'
        WHEN p.billed > 0 AND p.paid / p.billed >= 0.9    THEN '1. Pays in full'
        WHEN p.billed > 0 AND p.paid / p.billed < 0.1     THEN '3. Minimum payer'
        ELSE                                                   '2. Partial payer'
    END AS payment_behaviour,
    CASE
        WHEN COALESCE(a.sep_utilization, 0) < 0.3 THEN '1. <30%'
        WHEN a.sep_utilization < 0.7              THEN '2. 30-70%'
        WHEN a.sep_utilization < 0.9              THEN '3. 70-90%'
        ELSE                                           '4. 90%+'
    END AS utilization_band
FROM customers c
JOIN agg a USING (customer_id)
LEFT JOIN pay p USING (customer_id);

-- Note: the risk_scores view (model output used by 09 and 10) is added by src/run_sql.py
-- once src/train_model.py has created data/clean/risk_scores.csv.
