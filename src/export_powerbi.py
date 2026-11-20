"""
Export a Power BI-ready star schema into powerbi/data/.

    dim_customer.csv    one row per customer: profile, bands, behaviour segment, risk score & tier, default flag
    dim_month.csv       one row per month (calendar table)
    fact_statement.csv  one row per customer per month: bill, payment, status, utilization

    python src/export_powerbi.py
"""

from pathlib import Path

from run_sql import connect

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "powerbi" / "data"

QUERIES = {
    "dim_customer": """
        SELECT f.customer_id, f.credit_limit, f.limit_band, f.sex, f.education, f.marital_status, f.age, f.age_band,
               f.payment_behaviour, f.utilization_band, ROUND(f.sep_utilization, 4) AS sep_utilization,
               f.sep_status, f.months_late_count::INT AS months_late_count, f.max_months_late,
               ROUND(r.pd_score, 4) AS predicted_default_prob, r.risk_tier, r.risk_decile, r.in_test_set,
               f.defaulted
        FROM customer_features f JOIN risk_scores r USING (customer_id) ORDER BY 1""",
    "dim_month": """
        SELECT DISTINCT month, strftime(month, '%b %Y') AS month_name, month(month) AS month_number
        FROM statements ORDER BY 1""",
    "fact_statement": """
        SELECT customer_id, month, bill_amount, payment_amount, repayment_status, status_group, months_late,
               utilization, is_over_limit, has_credit_balance, credit_limit,
               (repayment_status >= 2)::INT AS is_2plus_late
        FROM statements ORDER BY customer_id, month""",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()
    for name, q in QUERIES.items():
        path = OUT / f"{name}.csv"
        con.execute(f"COPY ({q}) TO '{path}' (HEADER, DELIMITER ',')")
        n = con.sql(f"SELECT COUNT(*) FROM '{path}'").fetchall()[0][0]
        print(f"{name:<16} {n:>8,} rows  {path.stat().st_size/1e6:5.1f} MB")


if __name__ == "__main__":
    main()
