"""
load_db.py
Creates a SQLite database and loads the cleaned CSV files into it.
Run this third.
"""

import os
import sqlite3
import pandas as pd

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "patents.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# The SQL commands that create our 4 tables
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT    PRIMARY KEY,
    title        TEXT    NOT NULL,
    abstract     TEXT,
    filing_date  TEXT,
    year         INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id  TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL,
    country      TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id    TEXT    REFERENCES patents(patent_id),
    inventor_id  TEXT    REFERENCES inventors(inventor_id),
    company_id   TEXT    REFERENCES companies(company_id)
);

CREATE INDEX IF NOT EXISTS idx_rel_patent   ON relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_rel_company  ON relationships(company_id);
CREATE INDEX IF NOT EXISTS idx_pat_year     ON patents(year);
"""

def main():
    # Delete old database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed old database")

    # Connect (this creates the file)
    conn = sqlite3.connect(DB_PATH)

    # Create tables
    conn.executescript(SCHEMA)
    conn.commit()
    print("Tables created")

    # Save schema.sql file (required for submission)
    sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql")
    os.makedirs(sql_dir, exist_ok=True)
    with open(os.path.join(sql_dir, "schema.sql"), "w") as f:
        f.write(SCHEMA)

    # Load each CSV into its table
    for csv_file, table, pk in [
        ("clean_patents.csv",       "patents",       "patent_id"),
        ("clean_inventors.csv",     "inventors",     "inventor_id"),
        ("clean_companies.csv",     "companies",     "company_id"),
        ("clean_relationships.csv", "relationships", None),
    ]:
        df = pd.read_csv(os.path.join(DATA_DIR, csv_file), dtype=str)
        if pk:
            df = df[df[pk].notna() & (df[pk].str.strip() != "")]
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df.where(pd.notna(df), None)
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  Loaded {len(df)} rows → {table}")

    conn.close()
    size = os.path.getsize(DB_PATH) // 1024
    print(f"\nDone! Database saved: patents.db ({size} KB)")

if __name__ == "__main__":
    main()