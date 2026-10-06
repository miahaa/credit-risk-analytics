# SQLite credit analysis

This layer adds reproducible portfolio-style reporting, concentration analysis, and record drilldowns to the Python EDA. It uses SQLite and Python's standard-library `sqlite3`/`csv` modules; no additional Python packages or database server are needed. SQLite **3.37 or newer** is required for the schema's `STRICT` tables. Check the SQLite library used by Python with:

```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

## Reproduce the reports

From the repository root, using the project's Python environment:

```bash
python sql/load_database.py
python sql/run_analysis.py
```

The loader also works from another directory when invoked by its absolute path: root discovery searches the current directory and parents, then the script's checkout. Set `CREDIT_RISK_PROJECT_ROOT` to explicitly choose a checkout. Neither script edits the CSV or notebooks.

The loader builds a fresh database beside the destination, loads and verifies it in a transaction, and replaces `data/database/south_german_credit.sqlite` only after success. An unsuccessful build preserves the previous database. Each run reassigns `record_id` from the same one-based CSV row position; it does not append records. The database is generated and ignored by Git.

The runner opens the database read-only, executes all ten queries, and saves their results as matching filenames under `results/`. Every query has a deterministic ordering. CSVs use UTF-8, LF newlines, headers, and blank cells for SQL NULL. Percentages are rounded to two decimals in SQL. No timestamps or machine-specific paths enter result CSVs.

## Architecture and checks

- `credit_records`: all 22 processed CSV fields plus `record_id INTEGER PRIMARY KEY`. Numeric fields stay integers, the label stays text, and all original values are retained. `record_id` is a technical source-row identifier, not a customer identifier. Use `ORDER BY record_id` to reconstruct CSV order.
- `category_lookup`: corrected labels and display order for all 17 categorical predictors, keyed by `(variable_name, category_code)`. The EDA's nine mapped variables use identical definitions; the remaining definitions come from the same corrected UCI code table/R reader.
- `credit_reporting`: a view that joins readable labels and derives `is_bad`, `duration_band`, and `duration_band_order`. It retains all source columns.

Source: [UCI South German Credit](https://www.archive.ics.uci.edu/dataset/573/south%2Bgerman%2Bcredit%2Bupdate), [corrected code table and R reader archive](https://archive.ics.uci.edu/static/public/573/south+german+credit+update.zip). `category_lookup.sql` embeds the definitions so runtime needs no network connection. Labels must not be replaced with the older Statlog code table.

`schema.sql` enforces NOT NULL fields, allowed category codes, positive quantitative values, a binary target, and target/label agreement. The loader also verifies:

- Exact CSV header, row widths, and exact representation of every source value.
- Total count and Good/Bad counts against the current source CSV.
- Lookup coverage for all categorical predictors and target-label consistency.
- Every database row and identifier against the CSV in source order.
- SQLite integrity and the source-reconciliation report's issue columns.

SQL contains the business calculations. Python handles loading, verification, query execution, and export. No ORM, migration framework, custom indexes, or transaction/customer tables are needed for this sample.

## Queries and business purpose

| Query | Business purpose | SQL demonstrated |
|---|---|---|
| [01_source_reconciliation](queries/01_source_reconciliation.sql) | Confirm the reporting population and absence of import issues | Conditional aggregation, view joins |
| [02_review_segment](queries/02_review_segment.sql) | Inspect loans >24 months with no checking account or negative balance | WHERE filtering, window aggregates, ordering |
| [03_account_findings](queries/03_account_findings.sql) | Reconcile checking/history/savings comparisons with EDA | GROUP BY, UNION ALL, CTEs, LEFT JOIN |
| [04_duration_by_outcome](queries/04_duration_by_outcome.sql) | Reconcile median duration by outcome | ROW_NUMBER, partition counts, middle-position aggregation |
| [05_purpose_concentration](queries/05_purpose_concentration.sql) | Separate purpose Bad share from contribution to all Bad records | DENSE_RANK, window totals, aggregation |
| [06_checking_duration_concentration](queries/06_checking_duration_concentration.sql) | Identify concentration across checking status and duration | CTEs, CROSS JOIN, window totals |
| [07_account_history_segments](queries/07_account_history_segments.sql) | Examine overlap of account and history conditions | CASE WHEN, multi-condition grouping |
| [08_amount_quartiles](queries/08_amount_quartiles.sql) | Compare outcomes and duration composition by amount rank | NTILE(4), conditional aggregation |
| [09_top_amounts_by_purpose](queries/09_top_amounts_by_purpose.sql) | Drill into the three largest recorded amounts per observed purpose | Partitioned ROW_NUMBER, ranking filters |
| [10_employment_duration_mix](queries/10_employment_duration_mix.sql) | Compare loan-duration mix and outcomes within employment categories | CASE WHEN, conditional aggregation, lookup joins |

The corresponding result CSVs are in [results/](results/). Query 1 checks counts; query 3 reconciles selected account findings; query 4 reconciles the EDA's median durations. Other reports add concentration, overlapping segments, and composition/drilldown context rather than repeat all EDA tables.

## Definitions and interpretation

- **0 = Bad; 1 = Good.** `is_bad = 1` only when `credit_risk = 0`. `credit_risk_label` is display-only; both outcome columns must be excluded from future predictors.
- **Bad share** = Bad records / total records in that group. **Share of all Bad records** = group Bad records / all 300 sampled Bad records. These have different denominators.
- **Sparse** means n < 30, a review heuristic rather than a reliability guarantee. The employment report flags each duration cell as well as its overall category. Empty documented groups remain visible where appropriate, with NULL Bad share, not zero risk. Education has no records and therefore no top-record drilldown.
- Query 2 uses checking codes 1 or 2 and duration >24 months. This is a descriptive review condition, not a lending policy or risk score.
- Query 7 defines **account condition = checking-status codes 1 or 2** and **history condition = credit-history codes 0 or 1**. Its four groups are mutually exclusive and exhaustive.
- Query 6 uses <=12, >12–24, >24–36, >36 months, matching EDA. Queries 8 and 10 use <=12, >12–24, >24 months for more compact composition reporting. Boundaries are reporting choices, not optimized risk cutoffs.
- Query 8 uses `NTILE(4) OVER (ORDER BY credit_amount, record_id)`. **Equal amounts can be split across quartiles**; source-row identifiers make the split reproducible. These are equal-record-count rank groups, not fixed currency bands. The source amounts have an unknown monotonic transformation.
- Query 9 orders by amount descending, then record ID ascending, and returns exactly three records per purpose when available. It does not include every tie or rank records by risk.
- Median duration averages the middle one/two observations, handling both odd and even group sizes.
- All category codes are identifiers or ordered bands; never interpret their means as direct financial quantities.

The sample dates from 1973–1975, deliberately oversamples Bad credits, and contains transformed amounts. Percentages are sample associations, not population default probabilities. The data describe granted credits rather than all applicants. Sparse groups require caution, joint comparisons do not establish causation, and `personal_status_sex` does not recover sex. No financial exposure, losses, expected loss, income, profitability, or payment history beyond the documented categories is inferred.

## Findings and human review

Executed reports show:

1. The top three purposes by Bad count—others, furniture/equipment, and used cars—contain **209/300 Bad records (69.67%)**, despite different within-purpose Bad shares. This illustrates concentration versus rate.
2. Both defined account/history conditions have **47/68 Bad records (69.12%)**, compared with **54/436 (12.39%)** for neither condition. History-condition-only has only 21 records and is flagged sparse.
3. The highest recorded-amount quartile has **105/250 Bad records (42%)**, and **153/250 (61.2%)** have durations >24 months. This composition difference provides context, not independent predictive importance.

Review the duration boundaries, sparse threshold, named review conditions, quartile tie behavior, and historical labels before extending the analysis. SQL checks agree with EDA, but this descriptive layer is not a validated decision system.
