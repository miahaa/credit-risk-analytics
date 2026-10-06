"""Execute the ten SQL reports and export deterministic UTF-8 CSV results."""
import csv
from pathlib import Path
import sqlite3
import tempfile

from load_database import DATABASE_NAME, find_project_root

QUERY_NAMES = ['01_source_reconciliation', '02_review_segment', '03_account_findings', '04_duration_by_outcome', '05_purpose_concentration', '06_checking_duration_concentration', '07_account_history_segments', '08_amount_quartiles', '09_top_amounts_by_purpose', '10_employment_duration_mix']


def run_analysis():
    root = find_project_root()
    database = root / "data/database" / DATABASE_NAME
    if not database.is_file():
        raise FileNotFoundError("Run sql/load_database.py first.")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    results = root / "sql/results"
    results.mkdir(parents=True, exist_ok=True)
    try:
        # Execute all reports before replacing any saved results.
        with tempfile.TemporaryDirectory(prefix=".report-build-", dir=results) as temporary:
            for name in QUERY_NAMES:
                query = (root / "sql/queries" / f"{name}.sql").read_text()
                cursor = connection.execute(query)
                if cursor.description is None:
                    raise ValueError(f"{name} did not return a report.")
                rows = cursor.fetchall()
                if name == "01_source_reconciliation" and (len(rows) != 1 or any(rows[0][3:])):
                    raise ValueError("Database reconciliation failed.")
                with (Path(temporary) / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.writer(stream, lineterminator="\n")
                    writer.writerow([field[0] for field in cursor.description])
                    writer.writerows(rows)
                print(f"{name}: {len(rows)} result rows")
            for name in QUERY_NAMES:
                (Path(temporary) / f"{name}.csv").replace(results / f"{name}.csv")
    finally:
        connection.close()


if __name__ == "__main__":
    run_analysis()
