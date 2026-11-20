"""Create and execute notebooks/analysis.ipynb: the step-by-step walkthrough, from raw file to risk score."""

from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parent.parent
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

cells = [
    md("""# Credit Card Default Risk: walkthrough on real data

**Data:** 30,000 real credit card customers of a Taiwanese bank, with six months of bills, payments and repayment
status (April–September 2005), and whether each customer defaulted in October 2005.
Source: Yeh, I. (2009), *Default of Credit Card Clients*, UCI Machine Learning Repository, https://doi.org/10.24432/C55S3H

**Questions:**
1. What does the portfolio look like, and how much is at risk?
2. Who defaults?
3. What behaviour warns us early?
4. Can we score every customer's risk, and how should the bank act on it?"""),
    code("""import sys
from pathlib import Path
import pandas as pd
from IPython.display import Image, display

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from run_sql import connect

con = connect()
pd.set_option("display.float_format", "{:,.2f}".format)
pd.set_option("display.max_colwidth", 120)
sql = lambda f: con.sql((ROOT / "sql" / f).read_text()).df()
chart = lambda n: display(Image(filename=str(ROOT / "images" / f"{n}.png"), width=900))"""),
    md("## 1. Look at the raw file first\nThe raw Excel file has an extra header row, and its columns are coded (`PAY_0`, `BILL_AMT1` and so on)."),
    code("""raw = pd.read_excel(ROOT / "data/raw/default_of_credit_card_clients.xls", header=1)
print(raw.shape)
raw.head()"""),
    md("### Codes that the source never explains\nEducation is documented as 1–4, marital status as 1–3, and repayment status as -1 or 1–9. The data contains other values:"),
    code("""print("EDUCATION:", raw["EDUCATION"].value_counts().sort_index().to_dict())
print("MARRIAGE: ", raw["MARRIAGE"].value_counts().sort_index().to_dict())
print("PAY_0 (Sep):", raw["PAY_0"].value_counts().sort_index().to_dict())
print("PAY_2 (Aug):", raw["PAY_2"].value_counts().sort_index().to_dict())"""),
    md("""Two things stand out:
- `EDUCATION` has 0, 5 and 6, and `MARRIAGE` has 0. None of these are documented.
- Status **1** ("1 month late") appears 3,688 times in September (`PAY_0`), but only 28 times in August.
  The months were clearly recorded differently, so month-to-month comparisons should use **2+ months late** instead."""),
    md("## 2. Clean it\n`src/clean_data.py` fixes or flags each issue and reshapes the data into two tables: one row per customer, and one row per customer per month. Every decision is logged:"),
    code('pd.read_csv(ROOT / "reports/data_quality.csv")'),
    code("""for t in ["customers", "statements"]:
    print(t, con.sql(f"SELECT COUNT(*) FROM {t}").fetchall()[0][0])
con.sql("SELECT * FROM statements LIMIT 6").df()"""),
    md("## 3. Portfolio overview"),
    code('sql("01_portfolio_overview.sql").T'),
    code('sql("03_monthly_trend.sql")'),
    code('chart("02_monthly_trend")'),
    md("""**What it means:** balances grew **32% in six months** (NT$1.17B → NT$1.54B) and utilization rose from 23% to 31%.
22% of customers defaulted the next month. That's very high, and consistent with Taiwan's 2005–06 card-debt crisis."""),
    md("## 4. Who defaults?"),
    code('sql("02_default_by_segment.sql")'),
    code('chart("01_default_by_segment")'),
    code('sql("06_utilization_by_limit.sql").pivot(index="limit_band", columns="utilization_band", values="default_rate_pct")'),
    code('chart("05_utilization_by_limit")'),
    md("""**What it means:** the size of the credit line is the clearest profile signal: 32% default at NT$50K or less, compared with 12% above NT$400K.
Demographic differences are small. For large lines, high utilization nearly doubles the risk."""),
    md("## 5. Early warning signs"),
    code('sql("05_early_warning.sql")'),
    code('chart("03_early_warning")'),
    code('sql("04_roll_rates.sql")'),
    code('chart("04_roll_rates")'),
    code('sql("07_payment_behaviour.sql")'),
    code('chart("06_payment_behaviour")'),
    md("""**What it means:** payment history beats everything else. One month late takes default risk from about 13% to 34%, and two months late takes it to 69%.
Customers behind on payments are 32% of customers but hold nearly two-thirds of defaulted balances.

**A surprise worth flagging:** customers who pay in full defaulted *slightly more often* (12.5%) than minimum payers (11.2%).
Real data doesn't always match the textbook. I report it rather than hide it."""),
    md("## 6. Risk score (behaviour-only logistic regression)\nTrained on 70% of customers and tested on the 30% it never saw. Demographics are deliberately excluded."),
    code('pd.read_csv(ROOT / "reports/results/model_metrics.csv")'),
    code('pd.read_csv(ROOT / "reports/results/model_factors.csv")'),
    code('chart("07_model_performance")'),
    code('chart("08_model_factors")'),
    code('sql("09_risk_tiers.sql")'),
    code('chart("09_risk_tiers")'),
    code('sql("10_tier_actions.sql")'),
    md("""**What it means:** the score ranks risk well (AUC about 0.76 across 5-fold cross-validation). The riskiest 20% of customers contain about half of all defaulters,
and predicted default rates match actual ones closely in every tier. A bank could use the tiers to decide who gets
credit-line increases, reminders, outreach or reduced limits."""),
    md("""## 7. Limitations
- Only six months of history, so no long-term trends or seasonality.
- No transaction or fraud data (banks don't publish it).
- Status codes -2 and 0 are undocumented; I used the common interpretation.
- 866 customers had no bills for six months, yet 37% are marked as defaulting. I'd raise this with the data owner."""),
]

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})
nbf.write(nb, ROOT / "notebooks" / "analysis.ipynb")
print("wrote notebooks/analysis.ipynb")
