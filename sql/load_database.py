"""Rebuild the generated SQLite database from the cleaned CSV; no dependencies."""
import csv
import os
from pathlib import Path
import sqlite3
import tempfile

DATABASE_NAME = "south_german_credit.sqlite"
CSV_COLUMNS = ['checking_status', 'duration_months', 'credit_history', 'purpose', 'credit_amount', 'savings', 'employment_duration', 'installment_rate', 'personal_status_sex', 'other_debtors', 'residence_duration', 'property', 'age', 'other_installment_plans', 'housing', 'number_credits', 'job', 'people_liable', 'telephone', 'foreign_worker', 'credit_risk', 'credit_risk_label']


def find_project_root():
    configured = os.environ.get("CREDIT_RISK_PROJECT_ROOT")
    cwd = Path.cwd().resolve()
    candidates = ([Path(configured).expanduser().resolve()] if configured else
                  [cwd, *cwd.parents, Path(__file__).resolve().parent.parent])
    for candidate in candidates:
        if (candidate / "data/processed/south_german_credit_clean.csv").is_file() and (candidate / "sql/schema.sql").is_file():
            return candidate
    raise FileNotFoundError("Set CREDIT_RISK_PROJECT_ROOT to the project checkout.")


def verify_database(connection, source_rows):
    actual = connection.execute(
        "SELECT record_id, " + ", ".join(CSV_COLUMNS) + " FROM credit_records ORDER BY record_id"
    ).fetchall()
    expected = [tuple([i, *row]) for i, row in enumerate(source_rows, 1)]
    if actual != expected:
        raise ValueError("Database rows differ from the processed CSV.")
    source_bad = sum(row[CSV_COLUMNS.index("credit_risk")] == 0 for row in source_rows)
    source_good = len(source_rows) - source_bad
    reconciliation = connection.execute(
        (find_project_root() / "sql/queries/01_source_reconciliation.sql").read_text()
    ).fetchone()
    if reconciliation[:3] != (len(source_rows), source_bad, source_good):
        raise ValueError("Row or outcome counts do not reconcile.")
    # All validation columns after the three counts must report zero issues.
    if any(reconciliation[3:]):
        raise ValueError(f"Reconciliation reported issues: {reconciliation}")
    if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise ValueError("SQLite integrity check failed.")


def load_database():
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise RuntimeError("SQLite >= 3.37 is required for STRICT tables.")
    root = find_project_root()
    with (root / "data/processed/south_german_credit_clean.csv").open(newline="") as stream:
        reader = csv.reader(stream)
        if next(reader) != CSV_COLUMNS:
            raise ValueError("Processed CSV header does not match the expected schema.")
        raw_rows = list(reader)
    if not raw_rows or any(len(row) != len(CSV_COLUMNS) for row in raw_rows):
        raise ValueError("CSV is empty or contains malformed rows.")
    rows = []
    for row in raw_rows:
        converted = [int(value) if col != "credit_risk_label" else value
                     for col, value in zip(CSV_COLUMNS, row)]
        if [str(value) for value in converted] != row:
            raise ValueError("CSV values cannot be represented exactly by the declared types.")
        rows.append(converted)
    directory = root / "data/database"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / DATABASE_NAME
    # Build a fresh database beside the destination and replace only after verification.
    handle = tempfile.NamedTemporaryFile(prefix=".credit-build-", suffix=".sqlite", dir=directory, delete=False)
    temporary = Path(handle.name)
    handle.close()
    connection = None
    try:
        connection = sqlite3.connect(temporary)
        connection.executescript("BEGIN IMMEDIATE;\n" + (root / "sql/schema.sql").read_text() + "\n" + (root / "sql/category_lookup.sql").read_text())
        placeholders = ", ".join("?" for _ in range(len(CSV_COLUMNS) + 1))
        connection.executemany(
            "INSERT INTO credit_records (record_id, " + ", ".join(CSV_COLUMNS) + ") VALUES (" + placeholders + ")",
            [tuple([i, *row]) for i, row in enumerate(rows, 1)],
        )
        verify_database(connection, rows)
        connection.commit()
        connection.close()
        connection = None
        temporary.replace(destination)
    finally:
        if connection is not None:
            connection.rollback()
            connection.close()
        temporary.unlink(missing_ok=True)
    print(f"Loaded and verified {len(rows)} records: {destination}")
    return destination


if __name__ == "__main__":
    load_database()
