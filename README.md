# Credit risk analytics

This project explores credit risk using the South German Credit dataset. Cleaning, focused EDA, and SQL analysis are complete. Predictive modeling and dashboard/visualization are not yet implemented.

## Repository structure

```text
data/
  raw/SouthGermanCredit.asc              Original source data
  processed/south_german_credit_clean.csv Validated cleaned export
  database/south_german_credit.sqlite     Generated SQLite database (Git-ignored)
notebooks/
  01_data_cleaning.ipynb                 Implemented cleaning workflow
  02_exploratory_analysis.ipynb          Implemented focused EDA
src/                                    Reserved for reusable Python code
sql/                                    SQLite schema, loader, queries, and CSV results
images/                                 Reserved for visual outputs
requirements.txt                        Current runtime dependencies
```

The empty reserved directories may not appear in a fresh Git clone. The local `.venv/` environment is ignored and must be created separately.

## Dataset source

Source: [South German Credit, UCI Machine Learning Repository](https://www.archive.ics.uci.edu/dataset/573/south%2Bgerman%2Bcredit%2Bupdate).

Citation: South German Credit [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5QG88.

The dataset is distributed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). Consult UCI's accompanying `codetable.txt` and `read_SouthGermanCredit.R` for category definitions; these reference files are not currently bundled here. Use the corrected South German documentation rather than the older Statlog German Credit code table.

The supplied source has 1,000 records, 20 predictors, and one target. The processed CSV has 22 columns because it adds a readable target label.

## Setup and execution

Python **3.14** is recommended; the cleaning workflow was verified with the existing Python 3.14 environment. Pandas, matplotlib, and the Jupyter Notebook application are declared as direct dependencies. Notebook installs its required kernel and execution infrastructure transitively.

From the repository root:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m notebook
```

Open `notebooks/01_data_cleaning.ipynb`, select the environment's Python kernel, and restart the kernel and run all cells. Outputs are retained for reading on GitHub. Execution regenerates `data/processed/south_german_credit_clean.csv`.

The notebook finds the checkout by searching the current directory and its parents, so it works from the repository root, `notebooks/`, or another directory within the checkout. When launching a kernel outside the checkout, set an explicit root before starting Jupyter:

```bash
export CREDIT_RISK_PROJECT_ROOT="/absolute/path/to/credit-risk-analytics"
python -m notebook
```

For noninteractive execution, from the repository root with the environment activated:

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/01_data_cleaning.ipynb
```

## Cleaning workflow

1. Locate the checkout and read the whitespace-delimited raw file.
2. Validate the exact raw column set and rename German columns to readable English names; verify the resulting names and order.
3. Validate the target and add `credit_risk_label`.
4. Reject missing labels or missing values anywhere in the final dataset.
5. Inspect a sample, quantitative summaries, category frequencies, and duplicate counts.
6. Validate again before export, create the processed directory if needed, and save without a dataframe index.

Cleaning does not sort, filter, impute, recode original values, or remove records. The supplied dataset contains no missing values or duplicate rows. Duplicate counts are reported rather than automatically removed.

### Variable semantics

| Group | Columns |
|---|---|
| Quantitative | `duration_months`, `credit_amount`, `age` |
| Ordinal | `employment_duration`, `installment_rate`, `residence_duration`, `property`, `number_credits`, `job` |
| Nominal | `checking_status`, `credit_history`, `purpose`, `savings`, `personal_status_sex`, `other_debtors`, `other_installment_plans`, `housing` |
| Binary/target | `people_liable`, `telephone`, `foreign_worker`, `credit_risk`, `credit_risk_label` |

These groups describe meaning; the underlying stored values remain unchanged. Ordinal and binary category codes must not be assumed to be literal measurements or exact counts.

### Target definition

- `credit_risk = 1`: Good credit; `credit_risk_label = "Good"`.
- `credit_risk = 0`: Bad credit; `credit_risk_label = "Bad"`.

There are 700 Good and 300 Bad records. Future models must exclude both target columns from predictors. With this encoding, a probability for class 1 represents Good credit, not default risk.

## Important limitations

- Records date from 1973–1975 and do not represent contemporary lending conditions.
- Bad credits were deliberately oversampled. The observed 30% Bad share is not a population default-rate estimate.
- Credit amounts are transformed historical DM values; the actual original amounts and transformation are unknown.
- Several variables encode ranges or categories rather than direct measurements. Means and correlations of nominal codes can be misleading.
- Sex cannot reliably be recovered from the combined `personal_status_sex` category. Demographic interpretations require care.
- Row order is strongly associated with the target: the final 200 records are all Bad. Future train/test splits should be shuffled and stratified, with a fixed random seed.
- The readable label is derived directly from the target and would cause leakage if used as a predictor.

These limitations come from the UCI dataset documentation and inspection of the supplied files. This repository is an exploratory learning project, not a validated lending decision system.

## Project status

- Cleaning: complete.
- EDA: complete, with descriptive tables and four figures.
- SQL analysis: complete, with ten reproducible reports.
- Predictive modeling: not yet implemented.
- Dashboard/visualization: not yet implemented; notebook figures are EDA outputs.

Cleaning, EDA, and SQL analysis are implemented today. Open `notebooks/02_exploratory_analysis.ipynb` and run all cells after cleaning; it reads the processed CSV without modifying it. EDA contains descriptive tables and four figures, with no modeling.


## SQL analysis

SQLite adds concentration reporting, overlapping account/history segments, and record drilldowns to the Python EDA. It uses one source table (`credit_records`), one corrected-label table (`category_lookup`), and a reporting view (`credit_reporting`). Technical `record_id` values preserve one-based CSV row positions; they are not customer IDs. All cleaned source values are retained.

Use Python's standard-library SQLite module (SQLite >=3.37; no extra packages). From the repository root:

```bash
python sql/load_database.py
python sql/run_analysis.py
```

The first command rebuilds and verifies the ignored database under `data/database/`. The second executes SQL and exports ordered CSV results. See [SQL documentation](sql/README.md) for root resolution, schema checks, definitions, and interpretation choices.

| Query | Business question |
|---|---|
| 01 | Does the database reconcile to the processed CSV? |
| 02 | Which longer loans meet the documented account review condition? |
| 03 | Do checking/history/savings findings match EDA? |
| 04 | Does median duration by outcome match EDA? |
| 05 | Which purposes contribute the most Bad records? |
| 06 | Where are outcomes concentrated by checking status and duration? |
| 07 | How do overlapping account/history conditions relate to outcomes? |
| 08 | How do duration composition and outcomes vary by amount quartile? |
| 09 | Which records have the largest recorded amounts within each purpose? |
| 10 | How does duration mix vary by employment category? |

### Selected executed results

Source reconciliation:

| Records | Bad | Good | Missing-value rows | Label mismatches | Missing lookup rows |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 300 | 700 | 0 | 0 | 0 |

Top three purposes by Bad count:

| Purpose | Records | Bad | Bad share | Share of all Bad records |
|---|---:|---:|---:|---:|
| Others | 234 | 89 | 38.03% | 29.67% |
| Furniture/equipment | 280 | 62 | 22.14% | 20.67% |
| Car (used) | 181 | 58 | 32.04% | 19.33% |

Account/history segmentation:

| Segment | Records | Bad | Bad share | Sparse (n<30) |
|---|---:|---:|---:|---|
| Neither condition | 436 | 54 | 12.39% | No |
| Account condition only | 475 | 193 | 40.63% | No |
| History condition only | 21 | 6 | 28.57% | Yes |
| Both conditions | 68 | 47 | 69.12% | No |

Account condition means checking-status codes 1 or 2; history condition means credit-history codes 0 or 1. These are descriptive definitions, not a credit score or underwriting rule.

Three findings from the executed SQL:

- The top three purposes account for **209/300 Bad records (69.67%)**. Their within-purpose percentages differ, showing why concentration and Bad share answer different questions.
- The both-conditions segment has **69.12% Bad (47/68)** versus **12.39% (54/436)** for neither condition. The history-only segment is sparse and should not drive strong conclusions.
- The highest recorded-amount quartile has **42% Bad (105/250)** and **61.2% of records (153/250) with duration >24 months**. Amount and duration composition overlap; this does not isolate an amount effect.

Complete [queries](sql/queries/) and [result CSVs](sql/results/) are available for review. Results describe this historical oversampled sample, not population default probabilities. Transformed amounts are not used to calculate financial exposure or losses. Duration cutoffs, sparse flags, review conditions, and deterministic quartile tie handling are documented in the SQL README.
