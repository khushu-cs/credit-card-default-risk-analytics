# Build the Power BI Report: Step-by-Step Guide

You'll build a 3-page Power BI report on the **real** credit card data (30,000 customers, Apr–Sep 2005):

1. **Portfolio Overview**: balances, utilization, default rate
2. **Early Warning**: which behaviours come before default
3. **Risk Tiers**: the risk score and what to do with each tier

Time: about 2–3 hours. You need **Power BI Desktop** (free, Windows; Microsoft Store → "Power BI Desktop").

> Take a screenshot after each page. You'll add them to GitHub at the end.

---

## Part 0: Understand the data (5 min)

The `powerbi/data` folder has 3 files:

| File | Type | One row = | Useful columns |
|---|---|---|---|
| `dim_customer.csv` | Dimension ("who") | one customer | limit_band, age_band, education, payment_behaviour, risk_tier, predicted_default_prob, **defaulted** |
| `dim_month.csv` | Dimension ("when") | one month | month, month_name |
| `fact_statement.csv` | Fact ("what happened") | one customer in one month | bill_amount, payment_amount, repayment_status, status_group, utilization, is_2plus_late |

This is a **star schema**: the fact table sits in the middle, and the dimension tables describe it.
`defaulted` = 1 if the customer defaulted in October 2005. Amounts are in **NT$** (New Taiwan dollars).

---

## Part 1: Load the data (10 min)

1. Unzip the data pack. You'll get a `data` folder with 3 CSV files.
2. Open Power BI Desktop → **Blank report**.
3. **Home → Get data → Text/CSV** → pick `dim_customer.csv` → **Load**.
4. Repeat for `dim_month.csv` and `fact_statement.csv`.
5. **Check types:** click the **Table view** icon on the left. Make sure `month` (in both `dim_month` and `fact_statement`) is type **Date**, and that amounts and `utilization` are **Decimal number**.

---

## Part 2: Connect the tables (5 min)

1. Click the **Model view** icon on the left.
2. Delete any relationships Power BI guessed wrongly (right-click → Delete).
3. Drag to create these two relationships:

| From (one side) | To (many side) |
|---|---|
| `dim_customer[customer_id]` | `fact_statement[customer_id]` |
| `dim_month[month]` | `fact_statement[month]` |

Each line should show **1** on the dimension side and **\*** on the fact side.

---

## Part 3: Create the measures (15 min)

Right-click a table → **New measure** → paste → Enter.

**On `dim_customer`:**
```DAX
Customers = COUNTROWS(dim_customer)
```
```DAX
Default Rate = AVERAGE(dim_customer[defaulted])
```
```DAX
Predicted Default Rate = AVERAGE(dim_customer[predicted_default_prob])
```
```DAX
Total Credit Lines = SUM(dim_customer[credit_limit])
```
```DAX
Share of Defaulters =
DIVIDE(
    SUM(dim_customer[defaulted]),
    CALCULATE(SUM(dim_customer[defaulted]), ALL(dim_customer[risk_tier]))
)
```

**On `fact_statement`:**
```DAX
Total Balance = SUMX(FILTER(fact_statement, fact_statement[bill_amount] > 0), fact_statement[bill_amount])
```
```DAX
Utilization = DIVIDE([Total Balance], SUM(fact_statement[credit_limit]))
```
```DAX
2+ Months Late Rate = AVERAGE(fact_statement[is_2plus_late])
```
```DAX
Total Payments = SUM(fact_statement[payment_amount])
```

**Format:** rates (`Default Rate`, `Predicted Default Rate`, `Share of Defaulters`, `Utilization`, `2+ Months Late Rate`) → **Percentage**, 1 decimal. Amounts → **Whole number** with thousands separator.

> **What the DAX means:** `AVERAGE` of a 0/1 column = the share of 1s, so it gives you a rate. `SUMX(FILTER(...))` adds only the rows that match a condition (here, positive bills). `ALL(column)` removes a filter. `Share of Defaulters` uses it to divide each tier's defaulters by *all* defaulters.

---

## Part 4: Page 1, Portfolio Overview (30 min)

1. **Title** (Insert → Text box): "Credit Card Portfolio Overview (Apr–Sep 2005)"
2. **4 cards** across the top: `Customers`, `Total Credit Lines`, `Utilization`, `Default Rate`
3. **Column chart:** X-axis = `dim_month[month_name]`, Y-axis = `Total Balance`. Sort by month: click **…** → Sort axis → month_name, then go to the Table view, select `month_name` → **Sort by column** → `month`.
4. **Line chart:** X = `dim_month[month_name]`, Y = `Utilization`
5. **Bar chart:** Y = `dim_customer[limit_band]`, X = `Default Rate`. Turn on data labels.
6. **Slicers** (dropdown style): `limit_band`, `age_band`, `education`, `marital_status`
7. **Text box:** your 2 recommendations, in your own words

✅ **Check (no slicers):** Customers **30,000** · Default Rate **22.1%** · Utilization in Sep 2005 **30.6%** (Apr 2005: 23.3%)

---

## Part 5: Page 2, Early Warning (30 min)

1. **Cards:** `Default Rate`, `2+ Months Late Rate`
2. **Bar chart:** Y = `dim_customer[sep_status]`, X = `Default Rate`
   - Tip: status -2 = no balance, -1 = paid in full, 0 = revolving, 1+ = months late. Add a text box explaining this.
3. **Bar chart:** Y = `dim_customer[months_late_count]`, X = `Default Rate`
4. **Matrix (heatmap):** Rows = `limit_band`, Columns = `utilization_band`, Values = `Default Rate` → Format → Cell elements → **Background color: On** → gradient white → dark blue
5. **Line chart:** X = `month_name`, Y = `2+ Months Late Rate`
6. **Text box:** recommendation

✅ **Check:** customers with `months_late_count` = 0 → **11.7%** default; 6 → **70.3%**

---

## Part 6: Page 3, Risk Tiers (30 min)

1. **Clustered column chart:** X = `risk_tier`, Y = `Default Rate` **and** `Predicted Default Rate` (two bars per tier, so you can see whether the model's predictions match reality)
2. **Bar chart:** X = `risk_tier`, Y = `Share of Defaulters`
3. **Table:** `risk_tier`, `Customers`, `Default Rate`, `Share of Defaulters`
4. **Slicer:** `in_test_set` (1 = customers the model never saw in training)
5. **Text box:** what action you'd take for each tier

✅ **Check:** Very high tier → **3,354** customers, **66.2%** default rate; Low tier → **7.3%**

---

## Part 7: Polish (20 min)

- One **theme** for all pages (View → Themes).
- Same layout on every page: title top-left, KPI cards in a row, slicers on the left side.
- **Sync slicers** across pages (View → Sync slicers).
- Click a bar and check that the other visuals filter (cross-filtering).

---

## Part 8: Save and add to GitHub (10 min)

1. **File → Save as** → `credit_card_risk.pbix`
2. Screenshot each page (**Win + Shift + S**) → `powerbi_overview.png`, `powerbi_early_warning.png`, `powerbi_risk_tiers.png`
3. Upload the `.pbix` (if under 25 MB) and the screenshots to the repo's `powerbi` folder.
4. Tell Claude, and a "Power BI version" section with your screenshots will be added to the README.

---

## Interview questions this prepares you for

- **"What's a star schema?"** Fact tables hold events and numbers; dimension tables describe who, what and when; keys connect them.
- **"Measure vs calculated column?"** A column is computed once per row and stored. A measure is computed on the fly for whatever filters are active.
- **"Why does AVERAGE of a 0/1 column give a rate?"** Because the average of 0s and 1s equals the share of 1s.
- **"What does ALL() do?"** It removes filters from a column or table. It's used for "share of total" calculations.
- **"How would you check whether a model is any good in Power BI?"** Compare predicted and actual default rates by tier (calibration), using only test-set customers.
