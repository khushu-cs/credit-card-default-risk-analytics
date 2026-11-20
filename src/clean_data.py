"""
Clean the raw UCI "Default of Credit Card Clients" file into two analysis tables.

Source: Yeh, I. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository.
        https://doi.org/10.24432/C55S3H  (30,000 real card holders of a Taiwanese bank, Apr–Sep 2005)

Outputs (data/clean/):
  customers.csv    one row per customer: limit, demographics, bands, default flag
  statements.csv   one row per customer per month (Apr–Sep 2005): bill, payment, repayment status
  reports/data_quality.csv   every issue found, how many rows it affects, and what was done

    python src/clean_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "default_of_credit_card_clients.xls"
CLEAN = ROOT / "data" / "clean"
REPORTS = ROOT / "reports"

# raw column suffix -> calendar month (the source numbers months backwards from September)
MONTHS = {1: "2005-09-01", 2: "2005-08-01", 3: "2005-07-01", 4: "2005-06-01", 5: "2005-05-01", 6: "2005-04-01"}
EDUCATION = {1: "Graduate school", 2: "University", 3: "High school", 4: "Other"}
MARRIAGE = {1: "Married", 2: "Single", 3: "Other"}
SEX = {1: "Male", 2: "Female"}


def status_group(s: int) -> str:
    """Repayment status code -> readable group.
    Documented: -1 = paid duly, 1..8 = months of payment delay.
    Not documented by the source; common interpretation used here:
       -2 = no balance / card not used, 0 = revolving (minimum paid, not late)."""
    if s == -2:
        return "1. No balance"
    if s == -1:
        return "2. Paid in full"
    if s == 0:
        return "3. Revolving"
    if s <= 2:
        return "4. 1-2 months late"
    return "5. 3+ months late"


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    raw = pd.read_excel(RAW, header=1)  # row 0 holds X1..X23 labels; real names are on row 1
    raw = raw.rename(columns={"PAY_0": "PAY_1", "default payment next month": "DEFAULT"})  # source skips PAY_1
    issues = []

    def log(issue, n, action):
        issues.append({"issue": issue, "rows_affected": int(n), "action": action})

    log("Raw file has a second header row (X1..X23 labels)", 1, "Skipped; used the descriptive header row")
    log("Repayment status columns named PAY_0, PAY_2..PAY_6 (no PAY_1)", 6, "Renamed PAY_0 to PAY_1 so all six months line up")
    log("Duplicate customer IDs", raw["ID"].duplicated().sum(), "None found; no action")
    log("Missing values (any column)", raw.isna().sum().sum(), "None found; no action")

    # --- demographics ---
    edu_bad = raw["EDUCATION"].isin([0, 5, 6])
    log("EDUCATION codes 0, 5, 6 are not documented", edu_bad.sum(), "Grouped as 'Unknown'")
    mar_bad = raw["MARRIAGE"] == 0
    log("MARRIAGE code 0 is not documented", mar_bad.sum(), "Grouped as 'Unknown'")

    customers = pd.DataFrame({
        "customer_id": raw["ID"].map(lambda i: f"C{i:05d}"),
        "credit_limit": raw["LIMIT_BAL"].astype(int),
        "sex": raw["SEX"].map(SEX),
        "education": raw["EDUCATION"].map(EDUCATION).fillna("Unknown"),
        "marital_status": raw["MARRIAGE"].map(MARRIAGE).fillna("Unknown"),
        "age": raw["AGE"].astype(int),
        "defaulted": raw["DEFAULT"].astype(int),
    })
    customers["age_band"] = pd.cut(customers["age"], [0, 29, 39, 49, 59, 200],
                                   labels=["1. 21-29", "2. 30-39", "3. 40-49", "4. 50-59", "5. 60+"]).astype(str)
    customers["limit_band"] = pd.cut(customers["credit_limit"], [0, 50_000, 100_000, 200_000, 400_000, 10**9],
                                     labels=["1. <=50K", "2. 50-100K", "3. 100-200K", "4. 200-400K", "5. 400K+"]).astype(str)

    # --- monthly statements: wide (one row per customer) -> long (one row per customer-month) ---
    rows = []
    for k, month in MONTHS.items():
        rows.append(pd.DataFrame({
            "customer_id": customers["customer_id"],
            "month": month,
            "bill_amount": raw[f"BILL_AMT{k}"].astype(int),
            "payment_amount": raw[f"PAY_AMT{k}"].astype(int),   # amount paid during this month
            "repayment_status": raw[f"PAY_{k}"].astype(int),
            "credit_limit": raw["LIMIT_BAL"].astype(int),
        }))
    st = pd.concat(rows, ignore_index=True).sort_values(["customer_id", "month"]).reset_index(drop=True)

    neg = st["bill_amount"] < 0
    log("Negative bill amounts (customer overpaid = credit balance)", neg.sum(),
        "Kept; flagged has_credit_balance = 1; utilization floored at 0")
    contra = (st["repayment_status"] == -2) & (st["bill_amount"] > 0)
    log("Status -2 ('no balance') while the bill is above zero", contra.sum(),
        "Kept as reported; noted as a source inconsistency")
    over = st["bill_amount"] > st["credit_limit"]
    log("Bill above credit limit (over-limit)", over.sum(), "Kept; flagged is_over_limit = 1")
    sep1 = ((st["month"] == "2005-09-01") & (st["repayment_status"] == 1)).sum()
    other1 = ((st["month"] != "2005-09-01") & (st["repayment_status"] == 1)).sum()
    log(f"Status 1 ('1 month late') appears {sep1:,} times in September but only {other1} times in Apr–Aug",
        sep1 + other1, "Month-to-month trends use 2+ months late (status >= 2), which is recorded consistently")
    inactive = st.groupby("customer_id")["bill_amount"].apply(lambda s: (s == 0).all())
    log("Customers with a zero bill in all six months (inactive)", inactive.sum(), "Kept; excluded from utilization averages")
    log("Undocumented status codes -2 and 0", st["repayment_status"].isin([-2, 0]).sum(),
        "Interpreted as -2 = no balance, 0 = revolving (paid minimum, not late)")

    st["status_group"] = st["repayment_status"].map(status_group)
    st["months_late"] = st["repayment_status"].clip(lower=0)
    st["utilization"] = (st["bill_amount"].clip(lower=0) / st["credit_limit"]).round(4)
    st["is_over_limit"] = over.astype(int)
    st["has_credit_balance"] = neg.astype(int)

    customers.to_csv(CLEAN / "customers.csv", index=False)
    st.to_csv(CLEAN / "statements.csv", index=False)
    pd.DataFrame(issues).to_csv(REPORTS / "data_quality.csv", index=False)
    print(f"customers {len(customers):,} | statements {len(st):,}")
    print(pd.DataFrame(issues).to_string(index=False))


if __name__ == "__main__":
    main()
