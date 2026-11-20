"""
Prepare compact data for the dashboard: one row per customer (as column arrays) plus small
monthly and roll-rate summaries. All filtering happens in the browser.
"""

from pathlib import Path

import pandas as pd

from run_sql import connect

ROOT = Path(__file__).resolve().parent.parent

LIMIT = ["1. <=50K", "2. 50-100K", "3. 100-200K", "4. 200-400K", "5. 400K+"]
AGE = ["1. 21-29", "2. 30-39", "3. 40-49", "4. 50-59", "5. 60+"]
EDU = ["Graduate school", "University", "High school", "Other", "Unknown"]
MAR = ["Married", "Single", "Other", "Unknown"]
BEH = ["1. Pays in full", "2. Partial payer", "3. Minimum payer", "4. Behind on payments", "5. Inactive"]
TIER = ["1. Low", "2. Medium", "3. High", "4. Very high"]
UTIL = ["1. <30%", "2. 30-70%", "3. 70-90%", "4. 90%+"]
STATUS = ["1. No balance", "2. Paid in full", "3. Revolving", "4. 1-2 months late", "5. 3+ months late"]
MONTHS = ["2005-04-01", "2005-05-01", "2005-06-01", "2005-07-01", "2005-08-01", "2005-09-01"]

idx = lambda col, vals: "(CASE " + " ".join(f"WHEN {col} = '{v}' THEN {i}" for i, v in enumerate(vals)) + " END)"
DIMS = f"{idx('c.limit_band', LIMIT)} AS L, {idx('c.age_band', AGE)} AS A, {idx('c.education', EDU)} AS E, {idx('c.marital_status', MAR)} AS M"


def build() -> dict:
    con = connect()
    cust = con.sql(f"""
        SELECT {DIMS}, c.defaulted AS d, f.sep_status AS st, f.months_late_count::INT AS lc,
               ROUND(100 * LEAST(f.sep_utilization, 1.5))::INT AS u, GREATEST(f.sep_balance, 0)::BIGINT AS bal,
               {idx('f.payment_behaviour', BEH)} AS pb, ROUND(1000 * r.pd_score)::INT AS pd,
               {idx('r.risk_tier', TIER)} AS t, (c.credit_limit // 1000)::INT AS lim,
               {idx('f.utilization_band', UTIL)} AS ub, r.in_test_set AS te
        FROM customers c JOIN customer_features f USING (customer_id) JOIN risk_scores r USING (customer_id)
        ORDER BY c.customer_id""").df()
    monthly = con.sql(f"""
        SELECT {idx("strftime(s.month, '%Y-%m-%d')", MONTHS)} AS m, {DIMS},
               COUNT(*) AS n, SUM(GREATEST(s.bill_amount, 0))::BIGINT AS bal, SUM(s.credit_limit)::BIGINT AS lim,
               SUM(s.payment_amount)::BIGINT AS paid, SUM((s.repayment_status = -1)::INT) AS full,
               SUM((s.repayment_status = 0)::INT) AS rev, SUM((s.repayment_status >= 2)::INT) AS late2
        FROM statements s JOIN customers c USING (customer_id) GROUP BY ALL ORDER BY ALL""").df()
    roll = con.sql(f"""
        WITH p AS (SELECT customer_id, status_group AS f,
                          LEAD(status_group) OVER (PARTITION BY customer_id ORDER BY month) AS t FROM statements)
        SELECT {idx('p.f', STATUS)} AS fr, {idx('p.t', STATUS)} AS tt, {DIMS}, COUNT(*) AS n
        FROM p JOIN customers c USING (customer_id) WHERE p.t IS NOT NULL GROUP BY ALL ORDER BY ALL""").df()
    factors = pd.read_csv(ROOT / "reports/results/model_factors.csv")
    metrics = pd.read_csv(ROOT / "reports/results/model_metrics.csv")
    quality = pd.read_csv(ROOT / "reports/data_quality.csv")
    cols = lambda df: {"cols": list(df.columns), "rows": df.astype(int).values.tolist()}
    return {
        "cust": {c: cust[c].astype(int).tolist() for c in cust.columns},
        "monthly": cols(monthly), "roll": cols(roll),
        "factors": factors[["factor", "odds_multiplier", "coefficient"]].to_dict("records"),
        "metrics": dict(zip(metrics["metric"], metrics["value"])),
        "quality": quality.to_dict("records"),
        "dims": {"limit": LIMIT, "age": AGE, "edu": EDU, "mar": MAR, "beh": BEH, "tier": TIER, "util": UTIL,
                 "status": STATUS, "months": ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]},
    }


if __name__ == "__main__":
    import json
    d = build()
    print({k: (len(v["rows"]) if isinstance(v, dict) and "rows" in v else "") for k, v in d.items()})
    print(f"JSON size: {len(json.dumps(d, separators=(',', ':')))/1e6:.2f} MB")
