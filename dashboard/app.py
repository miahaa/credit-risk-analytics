"""Read-only Streamlit presentation of the project's saved analytical outputs."""
import json
import math
import os
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


CSV_ARTIFACTS = {
    "reconciliation": ("sql/results/01_source_reconciliation.csv", [
        "total_records", "bad_records", "good_records", "missing_value_rows",
        "invalid_target_rows", "target_label_mismatches", "missing_lookup_rows",
        "duplicate_record_ids", "row_position_issues"]),
    "accounts": ("sql/results/03_account_findings.csv", [
        "variable_name", "category_code", "category_label", "total_records",
        "bad_records", "bad_share_pct", "sparse_flag"]),
    "segments": ("sql/results/07_account_history_segments.csv", [
        "account_condition", "history_condition", "segment_label", "total_records",
        "bad_records", "bad_share_pct", "sparse_flag"]),
    "metrics": ("reports/modeling/test_metrics.csv", [
        "model", "candidate", "selected_primary", "threshold", "accuracy",
        "bad_precision", "bad_recall", "bad_f1", "specificity", "roc_auc",
        "average_precision", "brier_score", "tn", "fp", "fn", "tp", "flagged_pct"]),
    "associations": ("reports/modeling/logistic_associations.csv", [
        "variable", "comparison", "coefficient_contrast", "odds_ratio",
        "category_n", "reference_n", "sparse_flag"]),
    "cv": ("reports/modeling/cv_family_summary.csv", [
        "candidate", "family", "validation_average_precision_mean",
        "validation_average_precision_std", "validation_roc_auc_mean",
        "validation_roc_auc_std"]),
}
FIGURES = {
    "confusion": "images/modeling/02_test_confusion_matrices.png",
    "curves": "images/modeling/01_test_roc_pr.png",
    "calibration": "images/modeling/04_test_calibration.png",
}
ASSOCIATION_KEYS = [
    ("checking_status", "checking_status: no checking account vs ... >= 200 DM / salary for at least 1 year"),
    ("credit_history", "credit_history: critical account/other credits elsewhere vs all credits at this bank paid back duly"),
    ("purpose", "purpose: car (new) vs others"),
]
ACCENT = "#356579"
INK = "#193744"
MUTED = "#718690"


def project_root():
    """Script-relative paths work from any launch directory; allow an explicit checkout."""
    configured = os.environ.get("CREDIT_RISK_PROJECT_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path(__file__).resolve().parents[1]


def one_row(frame, description, **filters):
    result = frame
    for key, value in filters.items():
        result = result.loc[result[key].eq(value)]
    if len(result) != 1:
        raise ValueError(f"Expected exactly one {description}; found {len(result)}.")
    return result.iloc[0]


def numeric(frame, columns, description, nullable=()):
    for column in columns:
        values = pd.to_numeric(frame[column], errors="raise")
        if column not in nullable and values.isna().any():
            raise ValueError(f"Missing {column} in {description}.")
        if not values.dropna().map(math.isfinite).all():
            raise ValueError(f"Non-finite {column} in {description}.")
        frame[column] = values


def load_artifacts(root):
    """Validate input schemas and selected report consistency before rendering results."""
    tables = {}
    for key, (relative, columns) in CSV_ARTIFACTS.items():
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Missing artifact: {relative}.")
        frame = pd.read_csv(path)
        missing = set(columns) - set(frame.columns)
        if frame.empty or missing:
            raise ValueError(f"Malformed {relative}: empty table or missing columns {sorted(missing)}.")
        tables[key] = frame
    selection_path = root / "reports/modeling/selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    required = {"selected_candidate", "selected_family", "selected_parameters", "reference_threshold",
                "illustrative_threshold", "best_logistic", "best_tree", "seed", "test_size"}
    if not isinstance(selection, dict) or not required.issubset(selection):
        raise ValueError("selection.json is missing required selection/methodology keys.")
    parameters = selection["selected_parameters"]
    if (selection["selected_family"] != "logistic" or not isinstance(parameters, dict)
            or parameters.get("C") != 0.1 or parameters.get("amount_transform") != "raw"
            or selection["reference_threshold"] != 0.50 or selection["illustrative_threshold"] != 0.30):
        raise ValueError("Saved selection differs from the approved fixed dashboard narrative.")
    for relative in FIGURES.values():
        path = root / relative
        if not path.is_file() or path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Missing or invalid saved PNG: {relative}.")

    recon = tables["reconciliation"]
    numeric(recon, CSV_ARTIFACTS["reconciliation"][1], "source reconciliation")
    if len(recon) != 1 or recon.iloc[0, 3:].ne(0).any():
        raise ValueError("Source reconciliation contains import issues or unexpected rows.")
    source = recon.iloc[0]
    if source.total_records <= 0 or source.total_records != source.bad_records + source.good_records:
        raise ValueError("Source outcome counts do not reconcile.")
    for key in ["accounts", "segments"]:
        numeric(tables[key], ["total_records", "bad_records", "bad_share_pct", "sparse_flag"], key,
                nullable=["bad_share_pct"])
        frame = tables[key]
        if (frame.total_records.lt(0).any() or frame.bad_records.lt(0).any()
                or frame.bad_records.gt(frame.total_records).any()
                or not frame.sparse_flag.isin([0, 1]).all()
                or (frame.total_records.gt(0) & frame.bad_share_pct.isna()).any()
                or not frame.bad_share_pct.dropna().between(0, 100).all()
                or not frame.sparse_flag.eq(frame.total_records.lt(30).astype(int)).all()):
            raise ValueError(f"Invalid group counts, percentages or sparse flags in {key}.")
    checking = tables["accounts"].loc[tables["accounts"].variable_name.eq("checking_status")].copy()
    if len(checking) != 4 or set(checking.category_code) != {1, 2, 3, 4}:
        raise ValueError("Expected all four checking-status categories.")
    segments = tables["segments"]
    expected_segments = {(0, 0), (1, 0), (0, 1), (1, 1)}
    if len(segments) != 4 or set(zip(segments.account_condition, segments.history_condition)) != expected_segments:
        raise ValueError("Expected four mutually exclusive account/history segments.")
    for frame in [checking, segments]:
        if frame.total_records.sum() != source.total_records or frame.bad_records.sum() != source.bad_records:
            raise ValueError("Sample-group counts do not reconcile to the source report.")
    metrics = tables["metrics"]
    numeric(metrics, [c for c in CSV_ARTIFACTS["metrics"][1] if c not in ["model", "candidate"]],
            "test metrics", nullable=["bad_precision"])
    for column in ["accuracy", "bad_precision", "bad_recall", "bad_f1", "specificity", "roc_auc", "average_precision", "brier_score"]:
        if not metrics[column].dropna().between(0, 1).all():
            raise ValueError(f"Invalid {column} in test metrics.")
    if metrics[["tn", "fp", "fn", "tp"]].lt(0).any().any():
        raise ValueError("Negative confusion-matrix counts.")
    reference = one_row(metrics, "selected reference test result", model="logistic", threshold=0.50)
    alternative = one_row(metrics, "selected illustrative test result", model="logistic", threshold=0.30)
    tree = one_row(metrics, "tree comparator", model="tree", threshold=0.50)
    baseline = one_row(metrics, "majority baseline", model="most_frequent", threshold=0.50)
    if (reference.candidate != selection["selected_candidate"] or alternative.candidate != reference.candidate
            or reference.selected_primary != 1 or alternative.selected_primary != 1
            or tree.candidate != selection["best_tree"]):
        raise ValueError("Test metrics do not match the frozen selection.")
    test_total = int(reference[["tn", "fp", "fn", "tp"]].sum())
    test_bad = int(reference.tp + reference.fn)
    if test_total <= 0 or any(int(row[["tn", "fp", "fn", "tp"]].sum()) != test_total
                              or int(row.tp + row.fn) != test_bad
                              for row in [alternative, tree, baseline]):
        raise ValueError("Test populations differ across the displayed fixed configurations.")
    associations = tables["associations"]
    numeric(associations, ["coefficient_contrast", "odds_ratio", "category_n", "reference_n", "sparse_flag"], "associations")
    chosen = pd.DataFrame([one_row(associations, "named odds-ratio contrast", variable=variable, comparison=comparison)
                           for variable, comparison in ASSOCIATION_KEYS])
    if chosen.odds_ratio.le(0).any() or chosen.sparse_flag.ne(0).any():
        raise ValueError("The selected contrasts have invalid odds ratios or sparse support.")
    cv = tables["cv"]
    numeric(cv, CSV_ARTIFACTS["cv"][1][2:], "CV comparison")
    for family, candidate in [("logistic", selection["best_logistic"]), ("tree", selection["best_tree"])]:
        one_row(cv, f"{family} CV summary", family=family, candidate=candidate)
    return {**tables, "selection": selection, "checking": checking.sort_values("category_code"),
            "chosen_associations": chosen, "reference": reference, "alternative": alternative,
            "tree": tree, "baseline": baseline, "test_total": test_total, "test_bad": test_bad}


def checking_figure(frame):
    fig, ax = plt.subplots(figsize=(6.4, 3.0), layout="constrained")
    labels = [textwrap.fill(str(label).replace("...", "balance"), 38) + f"\n(n={int(n):,})"
              for label, n in zip(frame.category_label, frame.total_records)]
    bars = ax.barh(labels, frame.bad_share_pct, height=0.60, color=ACCENT)
    ax.bar_label(bars, labels=[f"{value:.1f}%" for value in frame.bad_share_pct], padding=5, fontsize=10)
    ax.invert_yaxis()
    ax.set(xlim=(0, 100), xlabel="Historical sample Bad share (%)", xticks=[0, 25, 50, 75, 100])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    return fig


def associations_figure(frame):
    fig, ax = plt.subplots(figsize=(10, 3.2), layout="constrained")
    labels = [textwrap.fill(row.comparison.replace("...", "balance").replace("_", " "), 78)
              + f"\nTraining support: {int(row.category_n)} vs {int(row.reference_n)}"
              for row in frame.itertuples()]
    ax.scatter(frame.odds_ratio, range(len(frame)), s=65, color=ACCENT, zorder=3)
    ax.set_yticks(range(len(frame)), labels)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set(xlim=(0.2, 6), xticks=[0.25, 0.5, 1, 2, 4], xticklabels=["0.25", "0.5", "1", "2", "4"],
           xlabel="Conditional modeled Bad odds ratio (log scale; named reference)")
    ax.axvline(1, color=MUTED, linestyle="--", linewidth=1)
    for i, value in enumerate(frame.odds_ratio):
        ax.annotate(f"{value:.2f}", (value, i), xytext=(7, -4), textcoords="offset points", fontsize=10)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return fig


def percentage(value):
    return "Undefined" if pd.isna(value) else f"{value:.1%}"


def main():
    st.set_page_config(page_title="Credit Risk Analytics", page_icon="📊", layout="wide")
    st.markdown("""<style>
    .block-container {max-width:1200px;padding-top:2rem;padding-bottom:3rem;}
    h1 {font-size:2.1rem !important;letter-spacing:-0.025em;}
    h2 {font-size:1.35rem !important;letter-spacing:-0.015em;}
    h3 {font-size:1.1rem !important;}
    [data-testid="stMetricValue"] {font-size:1.65rem;}
    </style>""", unsafe_allow_html=True)
    st.title("Credit Risk Analytics")
    st.write("Python data preparation and EDA · SQL risk segmentation · Interpretable machine learning")
    st.info("Historical, oversampled credit dataset. Results describe sample associations and model performance, "
            "not a production underwriting system or current population default probabilities.")
    source_column, model_column = st.columns(2)
    source_column.caption("**Source outcome:** `credit_risk = 0` → Bad · `credit_risk = 1` → Good")
    model_column.caption("**Modeling event:** `is_bad = 1` → Bad · `is_bad = 0` → Good")
    root = project_root()
    try:
        artifacts = load_artifacts(root)
    except (OSError, ValueError, KeyError, TypeError, pd.errors.ParserError) as error:
        st.error(f"Cannot render the saved analytical results: {error} "
                 "Check the saved report files and CREDIT_RISK_PROJECT_ROOT. The dashboard never regenerates analysis.")
        st.stop()

    source = artifacts["reconciliation"].iloc[0]
    st.header("Dataset snapshot")
    columns = st.columns(4)
    for column, label, value in zip(columns, ["Historical records", "Bad outcomes", "Good outcomes", "Locked test records"],
                                    [source.total_records, source.bad_records, source.good_records, artifacts["test_total"]]):
        column.metric(label, f"{int(value):,}")
    st.caption("Granted credits from 1973–1975. Bad records were deliberately oversampled; the sample mix is not a population default rate.")

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.header("Checking-status pattern")
        fig = checking_figure(artifacts["checking"])
        st.pyplot(fig, width="stretch")
        plt.close(fig)
        lower = one_row(artifacts["checking"], "no-account category", category_code=1)
        upper = one_row(artifacts["checking"], "highest checking category", category_code=4)
        st.caption(f"No checking account: {lower.bad_share_pct:.1f}% Bad (n={int(lower.total_records)}), "
                   f"versus {upper.bad_share_pct:.1f}% (n={int(upper.total_records)}) in the highest category. "
                   "This is an unadjusted historical sample association, not a causal effect.")
    with right:
        st.header("SQL account/history segments")
        segments = artifacts["segments"]
        segment_table = pd.DataFrame({
            "Segment": segments.segment_label + segments.sparse_flag.map({0: "", 1: " (sparse)"}),
            "Records": segments.total_records.astype(int), "Bad": segments.bad_records.astype(int),
            "Bad share": segments.bad_share_pct.map(lambda v: "Undefined" if pd.isna(v) else f"{v:.1f}%"),
        })
        st.table(segment_table.set_index("Segment"))
        st.caption("**Account condition:** checking-status codes 1 or 2. "
                   "**History condition:** credit-history codes 0 or 1.")
        both = one_row(segments, "both-conditions segment", account_condition=1, history_condition=1)
        neither = one_row(segments, "neither-condition segment", account_condition=0, history_condition=0)
        st.write(f"Both conditions: **{both.bad_share_pct:.1f}% Bad, n={int(both.total_records)}**. "
                 f"Neither: **{neither.bad_share_pct:.1f}% Bad, n={int(neither.total_records)}**.")
        st.caption("Descriptive segmentation, not an underwriting rule. The history-only group is sparse (n < 30); avoid strong conclusions from its percentage.")
    st.divider()

    st.header("Model performance · locked test set")
    parameters = artifacts["selection"]["selected_parameters"]
    st.write(f"**Selected: L2 Logistic Regression · C = {parameters['C']} · unlogged, scaled credit amount.** "
             "Selected using training cross-validation; the Decision Tree is a fixed comparator.")
    performance_rows = []
    for name, row in [("Majority Good baseline", artifacts["baseline"]),
                      ("Selected Logistic Regression", artifacts["reference"]),
                      ("Decision Tree comparator", artifacts["tree"])]:
        performance_rows.append({"Model · threshold 0.50": name, "Accuracy": percentage(row.accuracy),
                                 "Bad recall": percentage(row.bad_recall), "Bad precision": percentage(row.bad_precision),
                                 "Bad F1": f"{row.bad_f1:.3f}", "ROC-AUC": f"{row.roc_auc:.3f}",
                                 "Average precision": f"{row.average_precision:.3f}"})
    st.dataframe(pd.DataFrame(performance_rows), hide_index=True, width="stretch")
    reference = artifacts["reference"]
    st.caption(f"The majority baseline reports {percentage(artifacts['baseline'].accuracy)} accuracy while detecting "
               f"zero Bad records. Selected-model test Brier score: **{reference.brier_score:.3f}**. "
               f"Test sample: {artifacts['test_total']} records, including {artifacts['test_bad']} Bad. "
               "Average precision summarizes ranking across thresholds; it is distinct from precision at 0.50.")

    st.header("Threshold trade-off")
    threshold = st.radio("Display a frozen operating point", [0.50, 0.30],
                         format_func=lambda value: "Standard threshold · 0.50" if value == 0.50 else "Frozen illustrative threshold · 0.30",
                         horizontal=True, key="threshold")
    active = artifacts["reference"] if threshold == 0.50 else artifacts["alternative"]
    tradeoff_left, tradeoff_right = st.columns([1, 1.2], gap="large")
    with tradeoff_left:
        st.dataframe(pd.DataFrame({"Metric": ["Bad precision", "Bad recall", "Bad F1", "Specificity", "False positives", "False negatives", "Records flagged"],
                                   "Saved result": [percentage(active.bad_precision), percentage(active.bad_recall), f"{active.bad_f1:.3f}",
                                                    percentage(active.specificity), str(int(active.fp)), str(int(active.fn)),
                                                    f"{int(active.tp + active.fp)}/{artifacts['test_total']} ({active.flagged_pct:.1f}%)"]}),
                     hide_index=True, width="stretch")
        alternative = artifacts["alternative"]
        st.caption(f"At 0.50: {int(reference.tp)}/{artifacts['test_bad']} Bad detected; "
                   f"{int(reference.fp)} false positives; {int(reference.fn)} missed Bad. "
                   f"At 0.30: {int(alternative.tp)}/{artifacts['test_bad']} detected; "
                   f"{int(alternative.fp)} false positives; {int(alternative.fn)} missed Bad.")
    with tradeoff_right:
        st.image(str(root / FIGURES["confusion"]), width="stretch")
        st.caption("Saved paired confusion matrices remain visible at both operating points. Bad is the positive class.")
    st.caption("Threshold 0.30 was frozen from training out-of-fold predictions as an illustrative F1-based trade-off. "
               "It is not a financial optimum: false-positive and false-negative monetary costs are unknown. No test-set threshold tuning.")

    st.header("Three modeled associations")
    fig = associations_figure(artifacts["chosen_associations"])
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.caption("L2 Logistic Regression contrasts: exp(βcategory − βreference). Odds ratios describe conditional modeled associations, "
               "not probability multipliers or causal effects. Training support is shown for both sides of each comparison.")

    with st.expander("Technical evaluation details"):
        selection = artifacts["selection"]
        st.write(f"Stratified 80/20 split, seed {selection['seed']}; five identical shuffled stratified training folds. "
                 "Exactly 18 predictors; scaling inside each fold, semantic binary mapping and one-hot encoding for category codes. "
                 "Compared L2 Logistic C = 0.1/1/10 with logged versus raw-scaled amount, and shallow trees with depth 2/3/4 "
                 "and minimum leaf size 20/40. Mean training-CV AP guides selection; Logistic is preferred within 0.02 AP. "
                 "The model and illustrative threshold were frozen before final test evaluation.")
        cv_rows = []
        for row in artifacts["cv"].itertuples():
            cv_rows.append({"Candidate": row.candidate,
                            "CV AP · mean ± SD": f"{row.validation_average_precision_mean:.3f} ± {row.validation_average_precision_std:.3f}",
                            "CV ROC-AUC · mean ± SD": f"{row.validation_roc_auc_mean:.3f} ± {row.validation_roc_auc_std:.3f}"})
        st.dataframe(pd.DataFrame(cv_rows), hide_index=True, width="stretch")
        st.caption("Fold standard deviations are descriptive variability, not formal confidence intervals. No recalibration or prevalence correction.")
        st.image(str(root / FIGURES["curves"]), width="stretch")
        st.image(str(root / FIGURES["calibration"]), width="stretch")
        st.caption("Existing saved figures; calibration uses approximately five bins. These probabilities refer to the historical oversampled sample.")
        st.write("**Provenance:** the presentation reads saved CSV/JSON/PNG artifacts under `sql/results/`, `reports/modeling/`, "
                 "and `images/modeling/`. It does not execute SQL, notebooks, CV, model fitting or threshold optimization.")
        for key, label in [("segments", "Download SQL segments"), ("metrics", "Download saved test metrics")]:
            relative = CSV_ARTIFACTS[key][0]
            st.download_button(label, (root / relative).read_bytes(), file_name=Path(relative).name,
                               mime="text/csv", key=f"download_{key}")

    st.header("Limitations and responsible interpretation")
    st.markdown(
        "- **Historical selection:** granted credits from 1973–1975; Bad outcomes were deliberately oversampled. "
        "Sample shares and modeled probabilities are not current population default probabilities.\n"
        "- **Measurement and support:** amounts underwent an unknown transformation; category definitions are historical. "
        "Sparse categories require caution, and the test set contains only " + str(artifacts["test_bad"]) + " Bad records.\n"
        "- **Evaluation limits:** prior EDA examined the full dataset before the modeling split. The locked test is not a pristine external sample; "
        "training-CV search and out-of-fold threshold diagnostics can be optimistic.\n"
        "- **Demographic limits:** sex cannot reliably be recovered from `personal_status_sex`. It and `foreign_worker` are excluded "
        "from the primary model; small subgroup support and proxy effects prevent strong fairness conclusions. Age remains a predictor.\n"
        "- **Decision limits:** no financial loss or cost information is available. Threshold 0.30 is illustrative, "
        "not a lending policy. This project is not a production underwriting system."
    )
    st.caption("Portfolio workflow: raw data → Python cleaning → EDA → SQLite / SQL segmentation → interpretable modeling → read-only Streamlit report.")


if __name__ == "__main__":
    main()
