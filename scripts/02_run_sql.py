"""
Run every .sql file in sql/ against data/clean/retail.db and save the result
as a CSV in outputs/tables/.

This keeps the SQL in plain .sql files (so it can be read, reviewed and run in
any SQLite client) while still giving me reproducible CSV outputs for the
charts and the write-up.

Usage: python scripts/02_run_sql.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "clean" / "retail.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs" / "tables"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        query = sql_file.read_text(encoding="utf-8")
        result = pd.read_sql_query(query, con)
        out_path = OUT_DIR / (sql_file.stem + ".csv")
        result.to_csv(out_path, index=False)
        print("=" * 78)
        print(sql_file.name, "->", out_path.name, "({} rows)".format(len(result)))
        with pd.option_context("display.width", 200, "display.max_columns", 30):
            print(result.head(15).to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
