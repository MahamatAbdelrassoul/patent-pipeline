"""
load_db.py
Database is now built directly by fetch_data.py.
This script just verifies everything loaded correctly.
"""

import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "patents.db")

def main():
    if not os.path.exists(DB_PATH):
        print("  ✗  patents.db not found — run fetch_data.py first!")
        return

    conn = sqlite3.connect(DB_PATH)
    print("=" * 60)
    print("  Database verification")
    print("=" * 60)

    for table in ["patents", "inventors", "companies", "relationships"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<20} → {count:>12,} rows")

    conn.close()
    print()
    print("  ✔  Database looks good!")
    print("     Next step: run generate_reports.py")

if __name__ == "__main__":
    main()