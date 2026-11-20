"""
Run every SQL analysis in sql/ against the data and save each result as a CSV in reports/results/.

    python src/run_sql.py          # run all
    python src/run_sql.py 06       # run only files starting with 06
"""

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "reports" / "results"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((SQL_DIR / "00_setup.sql").read_text())
    if (ROOT / "data" / "clean" / "risk_scores.csv").exists():  # model output, created by train_model.py
        con.execute("CREATE OR REPLACE VIEW risk_scores AS SELECT * FROM read_csv_auto('data/clean/risk_scores.csv')")
    return con


def run(prefix: str = "") -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = connect()
    for f in sorted(SQL_DIR.glob(f"{prefix}*.sql")):
        if f.name.startswith("00_"):
            continue
        if f.stem[:2] in ("09", "10") and not (ROOT / "data" / "clean" / "risk_scores.csv").exists():
            print(f"skipping {f.stem}: run src/train_model.py first")
            continue
        df = con.sql(f.read_text()).df()
        df.to_csv(OUT_DIR / f"{f.stem}.csv", index=False)
        print(f"\n=== {f.stem} ===")
        print(df.to_string(index=False, max_rows=40))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "")
