"""
clean_data.py
Data is now cleaned inside fetch_data.py directly.
This script exports clean CSV files from the database.
Run this second.
"""

import os, sqlite3
import pandas as pd

DB_PATH   = os.path.join(os.path.dirname(__file__), "..", "patents.db")
DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    print("=" * 60)
    print("  Exporting clean CSV files from database ...")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    tables = [
        ("SELECT * FROM patents",       "clean_patents.csv"),
        ("SELECT * FROM inventors",     "clean_inventors.csv"),
        ("SELECT * FROM companies",     "clean_companies.csv"),
        ("SELECT * FROM relationships", "clean_relationships.csv"),
    ]

    for sql, filename in tables:
        print(f"  Exporting {filename} ...")
        df = pd.read_sql(sql, conn)
        df.to_csv(os.path.join(DATA_DIR, filename), index=False)
        print(f"    ✔  {len(df):,} rows")

    conn.close()
    print()
    print("  ✔  All CSV files saved to data/")
    print("     Next step: run generate_reports.py")

if __name__ == "__main__":
    main()