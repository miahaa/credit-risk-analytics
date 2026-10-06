# Credit risk analytics

This project explores credit risk using the South German Credit dataset. Data cleaning is complete. Focused EDA is implemented; modeling is still in development. SQL analysis and a dashboard/visualization are planned. No models, SQL analyses, or dashboard have been implemented.

## Repository structure

```text
data/
  raw/SouthGermanCredit.asc              Original source data
  processed/south_german_credit_clean.csv Validated cleaned export
notebooks/
  01_data_cleaning.ipynb                 Implemented cleaning workflow
  02_exploratory_analysis.ipynb          Implemented focused EDA
src/                                    Reserved for reusable Python code
sql/                                    Reserved for SQL analysis
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

## Planned next stages

- EDA: distributions, category profiles, and relationships with credit outcomes.
- SQL analysis: reproducible queries and grouped summaries.
- Modeling: leakage-safe preprocessing, stratified evaluation, and baseline comparisons.
- Dashboard/visualization: communicate findings and dataset limitations.

Cleaning and focused EDA are implemented today. Open `notebooks/02_exploratory_analysis.ipynb` and run all cells after cleaning; it reads the processed CSV without modifying it. EDA contains descriptive tables and four figures, with no modeling.
