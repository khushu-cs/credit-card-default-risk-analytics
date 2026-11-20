"""
Train an interpretable default-prediction model (logistic regression) and score every customer.

This is a "behaviour score": like the scores banks use for existing accounts, it uses only how the
customer has used and repaid the card, plus the size of their credit line. Demographics (sex, age,
education, marital status) are deliberately left out: fair-lending rules restrict their use, and
behaviour is a far stronger signal anyway.

Why logistic regression: banks need to explain credit decisions to customers and regulators,
so a model where each factor's effect is visible is preferred over a "black box".

Outputs:
  data/clean/risk_scores.csv          customer_id, probability of default, risk decile, risk tier, test-set flag
  reports/results/model_metrics.csv   AUC, KS, Gini on the held-out test set
  reports/results/model_factors.csv   each factor's effect on the odds of default
  reports/results/model_gains.csv     default capture by risk decile (test set)

    python src/train_model.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from run_sql import connect

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "reports" / "results"
SEED = 42

NUMERIC = {
    "sep_status_late": "Months late in September",
    "max_months_late": "Worst delay in last 6 months (months)",
    "months_late_count": "Number of late months (of 6)",
    "sep_utilization": "Utilization in September",
    "pay_ratio": "Share of bills paid (last 5 months)",
    "log_limit": "Credit limit (log)",
    "is_inactive": "No bills in 6 months (inactive)",
}
CATEGORICAL = {}
TIERS = [(0.0, 0.10, "1. Low"), (0.10, 0.25, "2. Medium"), (0.25, 0.50, "3. High"), (0.50, 1.01, "4. Very high")]


def load() -> pd.DataFrame:
    df = connect().sql("SELECT * FROM customer_features ORDER BY customer_id").df()
    df["sep_status_late"] = df["sep_status"].clip(lower=0)
    df["sep_utilization"] = df["sep_utilization"].clip(upper=1.5)
    df["is_inactive"] = (df["payment_behaviour"] == "5. Inactive").astype(int)
    df["pay_ratio"] = df["pay_ratio"].fillna(1.0).clip(upper=1.0)   # no bills -> nothing owed
    df["log_limit"] = np.log(df["credit_limit"])
    return df


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    df = load()
    X, y = df[list(NUMERIC) + list(CATEGORICAL)], df["defaulted"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=SEED)

    model = Pipeline([
        ("prep", ColumnTransformer([("num", StandardScaler(), list(NUMERIC))])),
        ("lr", LogisticRegression(max_iter=2000)),
    ])
    model.fit(X_tr, y_tr)

    # 5-fold cross-validation on all customers: how stable is the AUC across different splits?
    cv = cross_val_score(model, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), scoring="roc_auc")

    p_te = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, p_te)
    fpr, tpr, _ = roc_curve(y_te, p_te)
    ks = float(np.max(tpr - fpr))
    pd.DataFrame([
        {"metric": "AUC (test set)", "value": round(auc, 3), "meaning": "0.5 = coin flip, 1.0 = perfect ranking of risky vs safe customers"},
        {"metric": "Gini (test set)", "value": round(2 * auc - 1, 3), "meaning": "2 x AUC - 1; common in bank credit scoring"},
        {"metric": "KS (test set)", "value": round(ks, 3), "meaning": "max separation between defaulters and non-defaulters"},
        {"metric": "AUC (5-fold CV mean)", "value": round(cv.mean(), 3), "meaning": f"average over 5 different splits (range {cv.min():.3f}–{cv.max():.3f})"},
        {"metric": "Train customers", "value": len(X_tr), "meaning": "70% of customers"},
        {"metric": "Test customers", "value": len(X_te), "meaning": "30% held out, never seen in training"},
        {"metric": "Default rate", "value": round(float(y.mean()), 3), "meaning": "share of customers who defaulted"},
    ]).to_csv(RES / "model_metrics.csv", index=False)

    # factor effects: odds multiplier for +1 standard deviation (numeric) or vs. baseline group (categorical)
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["lr"].coef_[0]
    rows = []
    for n, c in zip(names, coefs):
        kind, col = n.split("__", 1)
        if kind == "num":
            label = NUMERIC[col]
        else:
            base, val = col.rsplit("_", 1)
            label = f"{CATEGORICAL[base]}: {val}"
        rows.append({"factor": label, "coefficient": round(c, 3), "odds_multiplier": round(float(np.exp(c)), 2),
                     "type": "per 1 std. dev. increase" if kind == "num" else "vs. baseline group"})
    pd.DataFrame(rows).sort_values("coefficient", key=abs, ascending=False).to_csv(RES / "model_factors.csv", index=False)

    # gains table on the test set: sort by risk, split into 10 equal groups
    te = pd.DataFrame({"p": p_te, "y": y_te.values}).sort_values("p", ascending=False).reset_index(drop=True)
    te["decile"] = te.index * 10 // len(te) + 1
    g = te.groupby("decile").agg(customers=("y", "size"), defaults=("y", "sum"), avg_pd=("p", "mean")).reset_index()
    g["default_rate_pct"] = (100 * g["defaults"] / g["customers"]).round(1)
    g["cum_pct_of_defaults_caught"] = (100 * g["defaults"].cumsum() / g["defaults"].sum()).round(1)
    g["cum_pct_of_customers"] = (100 * g["customers"].cumsum() / g["customers"].sum()).round(1)
    g["avg_predicted_pd_pct"] = (100 * g["avg_pd"]).round(1)
    g.drop(columns="avg_pd").to_csv(RES / "model_gains.csv", index=False)

    # score everyone (model trained on 70%); deciles & tiers for portfolio views
    df["pd_score"] = model.predict_proba(X)[:, 1].round(4)
    df["risk_decile"] = pd.qcut(df["pd_score"].rank(method="first", ascending=False), 10, labels=range(1, 11)).astype(int)
    df["risk_tier"] = pd.cut(df["pd_score"], [t[0] for t in TIERS] + [1.01], labels=[t[2] for t in TIERS], right=False).astype(str)
    df["in_test_set"] = df.index.isin(X_te.index).astype(int)
    df[["customer_id", "pd_score", "risk_decile", "risk_tier", "in_test_set"]].to_csv(ROOT / "data" / "clean" / "risk_scores.csv", index=False)

    print(pd.read_csv(RES / "model_metrics.csv").to_string(index=False))
    print(pd.read_csv(RES / "model_factors.csv").to_string(index=False))
    print(g.to_string(index=False))


if __name__ == "__main__":
    main()
