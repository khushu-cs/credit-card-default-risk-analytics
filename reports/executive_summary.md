# Executive Summary: Credit Card Default Risk Review

**To:** Head of Card Risk · **From:** Risk Analytics · **Data:** 30,000 card accounts, April–September 2005 (real data, UCI)

## Bottom line
**22% of customers defaulted** in October 2005, and the portfolio was getting riskier: balances grew **32% in six months** while credit lines didn't, so utilization rose from 23% to 31%. Default is highly predictable from **payment behaviour**. A simple, explainable risk score finds **half of all defaulters in the riskiest 20% of customers**, which gives the bank a practical way to act early.

## What we found

**1. Payment history is the strongest warning sign.**
Customers current in September defaulted ~13% of the time. One month late: 34%. Two months late: 69%. Customers late in 4+ of the last 6 months defaulted 64% of the time.

**2. Money at risk is concentrated.**
Customers already behind on payments are 32% of customers but held 64% of the balances that went into default.

**3. Credit-line size matters; demographics barely do.**
Default ranged from 32% (lines ≤ NT$50K) to 12% (lines > NT$400K). Age, education and marital status differences were small. For large lines, using 90%+ of the line raised default from about 14% to 25%.

**4. A behaviour-only score works well.**
Using only repayment and usage behaviour (no demographics), the model scored AUC of about 0.76 (5-fold cross-validation) on customers it never saw. Predicted and actual default rates match within each risk tier:

| Tier | % of customers | Actual default rate | % of all defaulters |
|---|---|---|---|
| Low (<10% predicted) | 17% | 7.3% | 6% |
| Medium (10–25%) | 57% | 14.5% | 38% |
| High (25–50%) | 14% | 36.8% | 23% |
| Very high (50%+) | 11% | 66.2% | 34% |

**5. One surprise.**
Customers who paid in full defaulted slightly more often (12.5%) than minimum payers (11.2%). This needs investigating before "pays in full" is used as a safety signal.

## Recommendations

| Priority | Action | Why | Owner |
|---|---|---|---|
| 1 | Contact customers at their **first** missed payment | Risk nearly triples from current to 1 month late; only 25% of late accounts catch up on their own | Collections |
| 2 | **Reduce available credit** for the Very high tier and freeze increases for High | 25% of customers hold 57% of defaulters | Credit policy |
| 3 | Offer **credit-line increases** to the Low tier | 17% of customers with a 7.3% default rate: safe growth | Card marketing |
| 4 | Monitor **portfolio utilization** monthly | It rose 8 points in 6 months, an early sign of stress | Portfolio management |
| 5 | Keep demographics **out** of credit decisions | Weak signal, and restricted by fair-lending rules | Model governance |

## Data notes
Real data with documented cleaning (12 issues logged). Undocumented repayment codes were interpreted the common way. "1 month late" codes are recorded inconsistently across months, so trends use 2+ months late. 866 customers with no bills are marked as defaulting, which should be raised with the data owner. Data is from Taiwan, 2005: patterns transfer to other portfolios, but default levels don't.
