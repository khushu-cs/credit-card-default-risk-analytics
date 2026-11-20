"""
Turn the SQL and model results (reports/results/*.csv) into README charts (images/*.png).

    python src/run_sql.py && python src/train_model.py && python src/make_charts.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "reports" / "results"
IMG = ROOT / "images"

BLUE, LBLUE, ORANGE, AQUA = "#2a78d6", "#9ec5f4", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ = LinearSegmentedColormap.from_list("seq", ["#e8f1fc", "#9ec5f4", "#5598e7", "#256abf", "#0d366b"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10.5, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK2, "ytick.color": INK2, "legend.frameon": False,
})
PCT = mtick.PercentFormatter(decimals=0)
strip = lambda s: s.str.replace(r"^\d\. ", "", regex=True)


def load(name):
    return pd.read_csv(RES / f"{name}.csv")


def save(fig, name, note=None):
    if note:
        fig.text(0.01, 0.005, note, color=INK2, fontsize=9, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.035 if note else 0, 1, 1))
    fig.savefig(IMG / f"{name}.png", dpi=160)
    plt.close(fig)


def hbar(ax, labels, values, color=BLUE, fmt="{:.1f}%"):
    ax.barh(labels, values, color=color, height=0.6)
    for i, v in enumerate(values):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=9.5)
    ax.set_xlim(0, max(values) * 1.25)
    ax.grid(axis="y", visible=False)


def segments():
    d = load("02_default_by_segment")
    overall = 22.1
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, dim, title in zip(axes, ["Credit limit (NT$)", "Age", "Education"], ["By credit limit (NT$)", "By age", "By education"]):
        s = d[d["dimension"] == dim].copy()
        if dim == "Education":
            s = s[s["segment"].isin(["Graduate school", "University", "High school"])]
            s = s.set_index("segment").loc[["High school", "University", "Graduate school"]].reset_index()
        else:
            s = s.iloc[::-1]
        hbar(ax, strip(s["segment"]), s["default_rate_pct"].tolist())
        ax.axvline(overall, color=INK2, lw=1, ls="--")
        ax.xaxis.set_major_formatter(PCT)
        ax.set_title(title, fontsize=11)
    fig.suptitle("Default rate by customer segment (dashed line = portfolio average 22.1%)", x=0.01, ha="left", fontweight="bold", fontsize=13)
    save(fig, "01_default_by_segment", "Education groups 'Other' and 'Unknown' (468 customers) are hidden: too small to compare.")


def trend():
    d = load("03_monthly_trend")
    d["m"] = pd.to_datetime(d["month"]).dt.strftime("%b")
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.9))
    ax = axes[0]
    ax.bar(d["m"], d["total_balance_bn"], color=BLUE, width=0.6)
    for i, v in enumerate(d["total_balance_bn"]):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5)
    ax.set_title("Total balances owed (NT$ billion)", fontsize=11)
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    ax.plot(d["m"], d["utilization_pct"], color=BLUE, lw=2, marker="o", ms=7, label="Utilization")
    ax.plot(d["m"], d["late_2plus_months_pct"], color=ORANGE, lw=2, marker="o", ms=7, label="2+ months late")
    for col, lab in [("utilization_pct", "Utilization"), ("late_2plus_months_pct", "2+ months late")]:
        ax.text(5.15, d[col].iloc[-1], lab, va="center", fontsize=9.5)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(0, 35)
    ax.set_xlim(-0.3, 6.6)
    ax.set_title("Utilization and share of accounts 2+ months late", fontsize=11)
    ax.grid(axis="x", visible=False)
    fig.suptitle("April–September 2005: balances grew 32% in six months", x=0.01, ha="left", fontweight="bold", fontsize=13)
    save(fig, "02_monthly_trend", "The September dip in '2+ months late' is likely a recording change (more '1 month late' codes that month), not a real improvement.")


def early_warning():
    d = load("05_early_warning")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    s = d[d["signal"] == "September status"]
    hbar(axes[0], strip(s["value"]), s["default_rate_pct"].tolist(), ORANGE)
    axes[0].set_title("By repayment status in September", fontsize=11)
    s = d[d["signal"] == "Late months (of last 6)"]
    hbar(axes[1], s["value"].str.replace("^1 months", "1 month", regex=True), s["default_rate_pct"].tolist(), ORANGE)
    axes[1].set_title("By number of late months (of last 6)", fontsize=11)
    for ax in axes:
        ax.xaxis.set_major_formatter(PCT)
        ax.invert_yaxis()
    fig.suptitle("Default rate next month: payment history is the strongest warning sign", x=0.01, ha="left", fontweight="bold", fontsize=13)
    save(fig, "03_early_warning")


def roll():
    d = load("04_roll_rates")
    cols = ["to_no_balance_pct", "to_paid_in_full_pct", "to_revolving_pct", "to_1_2_late_pct", "to_3plus_late_pct"]
    labs = ["No balance", "Paid in full", "Revolving", "1–2 months late", "3+ months late"]
    z = d[cols].values
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    im = ax.imshow(z, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(5), labs, rotation=20, ha="right")
    ax.set_yticks(range(5), strip(d["from_status"]))
    ax.grid(False)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f"{z[i, j]:.0f}%", ha="center", va="center", fontsize=10, color="white" if z[i, j] > 50 else INK)
    ax.set_xlabel("Status next month")
    ax.set_ylabel("Status this month")
    ax.set_title("Roll rates: where accounts move from one month to the next")
    fig.colorbar(im, ax=ax, shrink=0.8, format=PCT)
    save(fig, "04_roll_rates")


def util_limit():
    d = load("06_utilization_by_limit")
    piv = d.pivot(index="limit_band", columns="utilization_band", values="default_rate_pct")
    fig, ax = plt.subplots(figsize=(8, 4.4))
    im = ax.imshow(piv.values, cmap=SEQ, aspect="auto")
    ax.set_xticks(range(4), strip(pd.Series(piv.columns)))
    ax.set_yticks(range(5), strip(pd.Series(piv.index)))
    ax.grid(False)
    vmax = np.nanmax(piv.values)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=10, color="white" if v > vmax * 0.65 else INK)
    ax.set_xlabel("Utilization in September (balance ÷ limit)")
    ax.set_ylabel("Credit limit (NT$)")
    ax.set_title("Default rate by credit limit and utilization")
    fig.colorbar(im, ax=ax, shrink=0.8, format=PCT)
    save(fig, "05_utilization_by_limit", "Small credit lines default more at every utilization level; for large lines (200K+), high utilization is the warning sign.")


def behaviour():
    d = load("07_payment_behaviour")
    d = d[d["payment_behaviour"] != "5. Inactive"]
    labels = strip(d["payment_behaviour"])
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(x - 0.2, d["pct_customers"], 0.38, color=LBLUE, label="% of customers")
    ax.bar(x + 0.2, d["pct_of_defaulted_balances"], 0.38, color=ORANGE, label="% of defaulted balances")
    for i, r in enumerate(d.itertuples()):
        ax.text(i - 0.2, r.pct_customers + 1, f"{r.pct_customers:.0f}%", ha="center", fontsize=9, color=INK2)
        ax.text(i + 0.2, r.pct_of_defaulted_balances + 1, f"{r.pct_of_defaulted_balances:.0f}%", ha="center", fontsize=9)
        ax.text(i, -9, f"default rate {r.default_rate_pct:.0f}%", ha="center", fontsize=9, color=INK2)
    ax.set_xticks(x, labels)
    ax.set_ylim(-12, 75)
    ax.set_yticks(range(0, 80, 10))
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    ax.set_title("Payment behaviour: customers behind on payments hold 64% of defaulted balances")
    save(fig, "06_payment_behaviour", "Inactive customers (no bills in 6 months, 3% of customers) are excluded.")


def gains():
    d = load("model_gains")
    m = load("model_metrics").set_index("metric")["value"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    ax = axes[0]
    x = np.r_[0, d["cum_pct_of_customers"]]
    y = np.r_[0, d["cum_pct_of_defaults_caught"]]
    ax.plot(x, y, color=BLUE, lw=2, marker="o", ms=6, label="Model")
    ax.plot([0, 100], [0, 100], color=INK2, lw=1, ls="--", label="Random")
    ax.annotate(f"Top 20% riskiest\n= {d['cum_pct_of_defaults_caught'].iloc[1]:.0f}% of defaulters", (20, d["cum_pct_of_defaults_caught"].iloc[1]),
                xytext=(45, 22), fontsize=9.5, arrowprops=dict(arrowstyle="->", color=INK2))
    ax.xaxis.set_major_formatter(PCT); ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Customers reviewed, riskiest first"); ax.set_ylabel("Defaulters caught")
    ax.legend(loc="lower right")
    ax.set_title(f"Gains chart (test set) · AUC {m['AUC (test set)']:.2f} (cross-validated {m['AUC (5-fold CV mean)']:.2f})", fontsize=11)
    ax = axes[1]
    ax.bar(d["decile"].astype(str), d["default_rate_pct"], color=[ORANGE if i < 2 else BLUE for i in range(10)], width=0.6)
    for i, v in enumerate(d["default_rate_pct"]):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9)
    ax.axhline(22.1, color=INK2, lw=1, ls="--")
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Risk decile (1 = riskiest 10%)")
    ax.grid(axis="x", visible=False)
    ax.set_title("Actual default rate by risk decile (test set)", fontsize=11)
    fig.suptitle("The behaviour score ranks risk well on customers it never saw", x=0.01, ha="left", fontweight="bold", fontsize=13)
    save(fig, "07_model_performance", "Test set = 9,000 customers (30%) held out from training.")


def factors():
    d = load("model_factors").sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(9, 3.9))
    colors = [ORANGE if c > 0 else BLUE for c in d["coefficient"]]
    ax.barh(d["factor"], d["odds_multiplier"] - 1, left=1, color=colors, height=0.6)
    ax.axvline(1, color=INK2, lw=1)
    for i, (v, c) in enumerate(zip(d["odds_multiplier"], d["coefficient"])):
        ax.text(v + (0.01 if c > 0 else -0.01), i, f"×{v:.2f}", va="center", ha="left" if c > 0 else "right", fontsize=9.5)
    ax.set_xlim(0.7, 1.7)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Change in odds of default (per 1 standard deviation increase)")
    ax.set_title("What drives the risk score")
    save(fig, "08_model_factors", "Orange = raises risk, blue = lowers risk. Demographics (sex, age, education, marital status) are deliberately not used.")


def tiers():
    d = load("09_risk_tiers")
    labels = strip(d["risk_tier"])
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(x - 0.2, d["pct_customers"], 0.38, color=LBLUE, label="% of customers")
    ax.bar(x + 0.2, d["pct_of_all_defaulters"], 0.38, color=ORANGE, label="% of all defaulters")
    for i, r in enumerate(d.itertuples()):
        ax.text(i - 0.2, r.pct_customers + 1, f"{r.pct_customers:.0f}%", ha="center", fontsize=9, color=INK2)
        ax.text(i + 0.2, r.pct_of_all_defaulters + 1, f"{r.pct_of_all_defaulters:.0f}%", ha="center", fontsize=9)
        ax.text(i, -9, f"predicted {r.predicted_default_pct:.0f}% · actual {r.actual_default_pct:.0f}%", ha="center", fontsize=9, color=INK2)
    ax.set_xticks(x, labels)
    ax.set_ylim(-12, 75)
    ax.set_yticks(range(0, 80, 10))
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    hi = d[d["risk_tier"].isin(["3. High", "4. Very high"])]
    ax.set_title(f"Risk tiers: High + Very high = {hi['pct_customers'].sum():.0f}% of customers but {hi['pct_of_all_defaulters'].sum():.0f}% of defaulters")
    save(fig, "09_risk_tiers", "Tiers by predicted chance of default: Low <10%, Medium 10–25%, High 25–50%, Very high 50%+.")


if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    for f in [segments, trend, early_warning, roll, util_limit, behaviour, gains, factors, tiers]:
        f()
        print("saved", f.__name__)
