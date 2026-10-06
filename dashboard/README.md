# Credit Risk Analytics dashboard

A single-page Streamlit case study for a quick portfolio review: historical account patterns, SQL segments, held-out model evaluation, frozen threshold trade-offs, and three supported model contrasts.

The app reads saved artifacts. It does not run notebooks, rebuild SQLite, fit models, calculate cross-validation, optimize thresholds, or score applicants. Source encoding is **0 = Bad / 1 = Good**; the modeling event is **is_bad = 1 for Bad / 0 for Good**. Historical, deliberately oversampled outcomes are not present-day population default probabilities. This is not a production underwriting system.

## Local setup and launch

Python **3.14** was used to verify this app. From the repository root, a separate dashboard environment needs only the three direct dependencies in this folder:

```bash
python3.14 -m venv dashboard/.venv
source dashboard/.venv/bin/activate
python -m pip install -r dashboard/requirements.txt
python -m streamlit run dashboard/app.py --browser.gatherUsageStats false
```

Open the localhost URL shown in the terminal. Stop the server with Ctrl+C. The app resolves artifact paths relative to its own file, so launching with an absolute app path also works from outside the repository. An optional `CREDIT_RISK_PROJECT_ROOT` environment variable points to another complete checkout.

No public deployment is configured. For a future deployment, set the entry point to `dashboard/app.py` and install `dashboard/requirements.txt`; include the saved artifacts listed below. Deployment is a separate step.

## Artifact provenance

Paths below are relative to the repository root.

| Saved artifact | Presentation use |
|---|---|
| `sql/results/01_source_reconciliation.csv` | Total, Good and Bad counts; import checks |
| `sql/results/03_account_findings.csv` | Checking-status labels, counts and sample Bad shares |
| `sql/results/07_account_history_segments.csv` | Four descriptive account/history segments and sparse flags |
| `reports/modeling/selection.json` | Frozen model configuration, thresholds and split metadata |
| `reports/modeling/test_metrics.csv` | Baseline, Logistic and Tree metrics; fixed operating-point results |
| `reports/modeling/logistic_associations.csv` | Three named odds-ratio contrasts and training support |
| `reports/modeling/cv_family_summary.csv` | Saved family-level training CV comparison |
| `images/modeling/02_test_confusion_matrices.png` | Paired saved threshold confusion matrices |
| `images/modeling/01_test_roc_pr.png` | Existing ROC/PR figure in technical details |
| `images/modeling/04_test_calibration.png` | Existing calibration figure in technical details |

The app checks required files, schemas, selection keys, numeric ranges and displayed population reconciliation before rendering analytical results. Missing or malformed inputs produce a visible error. Repair or reproduce upstream artifacts separately; the app never regenerates them.

## Layout and interpretation

Six primary blocks: dataset KPIs, checking-status chart, SQL segment table, model-performance table, threshold comparison with paired confusion matrices, and three modeled associations. Methodology, CV, ROC/PR and calibration are in a technical expander. The only analytical control switches between the two previously frozen thresholds (0.50 and 0.30). Optional downloads return the original saved segment and test-metric CSV bytes.

SQL account condition means checking-status codes 1 or 2; history condition means credit-history codes 0 or 1. Groups below 30 records are marked sparse. The modeled contrasts name their reference categories and show training support; odds ratios are conditional model associations, not probability multipliers or causal effects. The lower threshold is an illustrative training-selected detection trade-off with unknown financial costs.

## Verification and screenshots

Verified locally with Streamlit 1.65.0: server launch, all sections, five loaded chart images, both frozen threshold displays, technical details, and visible missing/malformed-artifact handling using temporary fixtures. Displayed counts, percentages and metrics match saved artifacts after presentation rounding. SHA-256 checks confirmed all 47 existing analytical files were unchanged.

Actual browser screenshots are saved in `images/dashboard/overview.png` and `images/dashboard/model_tradeoff.png`. They show portions of the scrolling page in the local narrow preview; wider browser windows give the charts and tables more room. No public URL has been created.
