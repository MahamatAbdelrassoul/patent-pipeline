"""
generate_reports.py
Runs all 7 SQL queries and produces the console report, CSV files, and JSON.
Run this fourth (last).
"""

import os
import sqlite3
import json
import csv

DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "patents.db")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def run_query(conn, sql):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]

# ── The 7 required SQL queries ──────────────────────────────────

Q1_TOP_INVENTORS = """
SELECT i.name AS inventor_name, i.country,
       COUNT(DISTINCT r.patent_id) AS patent_count
FROM inventors i
JOIN relationships r ON r.inventor_id = i.inventor_id
GROUP BY i.inventor_id
ORDER BY patent_count DESC
LIMIT 20;
"""

Q2_TOP_COMPANIES = """
SELECT c.name AS company_name,
       COUNT(DISTINCT r.patent_id) AS patent_count
FROM companies c
JOIN relationships r ON r.company_id = c.company_id
GROUP BY c.company_id
ORDER BY patent_count DESC
LIMIT 20;
"""

Q3_COUNTRIES = """
SELECT i.country,
       COUNT(DISTINCT r.patent_id) AS patent_count,
       ROUND(100.0 * COUNT(DISTINCT r.patent_id)
             / (SELECT COUNT(*) FROM patents), 2) AS share_pct
FROM inventors i
JOIN relationships r ON r.inventor_id = i.inventor_id
WHERE i.country NOT IN ('UNKNOWN', '')
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 20;
"""

Q4_YEARLY = """
SELECT year, COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;
"""

Q5_JOIN = """
SELECT p.patent_id, p.title, p.year,
       i.name AS inventor_name, i.country,
       c.name AS company_name
FROM patents p
LEFT JOIN relationships r ON r.patent_id   = p.patent_id
LEFT JOIN inventors     i ON i.inventor_id = r.inventor_id
LEFT JOIN companies     c ON c.company_id  = r.company_id
ORDER BY p.year DESC
LIMIT 100;
"""

Q6_CTE = """
WITH company_yearly AS (
    SELECT c.company_id, c.name AS company_name, p.year,
           COUNT(DISTINCT r.patent_id) AS yearly_count
    FROM companies c
    JOIN relationships r ON r.company_id = c.company_id
    JOIN patents       p ON p.patent_id  = r.patent_id
    WHERE p.year IS NOT NULL
    GROUP BY c.company_id, c.name, p.year
),
company_totals AS (
    SELECT company_name,
           SUM(yearly_count)           AS total_patents,
           COUNT(DISTINCT year)        AS active_years,
           ROUND(AVG(yearly_count), 1) AS avg_per_year
    FROM company_yearly
    GROUP BY company_id, company_name
)
SELECT ROW_NUMBER() OVER (ORDER BY total_patents DESC) AS rank,
       company_name, total_patents, active_years, avg_per_year
FROM company_totals
ORDER BY total_patents DESC
LIMIT 10;
"""

Q7_WINDOW = """
WITH inv AS (
    SELECT i.name AS inventor_name, i.country,
           COUNT(DISTINCT r.patent_id) AS patent_count
    FROM inventors i
    JOIN relationships r ON r.inventor_id = i.inventor_id
    GROUP BY i.inventor_id
)
SELECT RANK()  OVER (ORDER BY patent_count DESC)                    AS overall_rank,
       RANK()  OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
       inventor_name, country, patent_count,
       NTILE(4) OVER (ORDER BY patent_count DESC)                   AS quartile
FROM inv
ORDER BY overall_rank
LIMIT 30;
"""

# ── Console report ───────────────────────────────────────────────

def print_line(char="═", width=62):
    print(char * width)

def console_report(conn):
    total = run_query(conn, "SELECT COUNT(*) AS n FROM patents;")[0]["n"]
    inventors  = run_query(conn, Q1_TOP_INVENTORS)
    companies  = run_query(conn, Q2_TOP_COMPANIES)
    countries  = run_query(conn, Q3_COUNTRIES)
    yearly     = run_query(conn, Q4_YEARLY)
    cte_result = run_query(conn, Q6_CTE)
    ranked     = run_query(conn, Q7_WINDOW)

    print_line()
    print("        GLOBAL PATENT INTELLIGENCE REPORT")
    print_line()
    print(f"\n  Total Patents: {total:,}\n")

    print_line("─")
    print("  Q1 · TOP 10 INVENTORS")
    print_line("─")
    for i, r in enumerate(inventors[:10], 1):
        print(f"  {i:>2}. {r['inventor_name']:<35} {r['patent_count']:>5} patents  [{r['country']}]")

    print()
    print_line("─")
    print("  Q2 · TOP 10 COMPANIES")
    print_line("─")
    for i, r in enumerate(companies[:10], 1):
        print(f"  {i:>2}. {r['company_name']:<38} {r['patent_count']:>5} patents")

    print()
    print_line("─")
    print("  Q3 · TOP 10 COUNTRIES")
    print_line("─")
    for i, r in enumerate(countries[:10], 1):
        print(f"  {i:>2}. {r['country']:<10} {r['patent_count']:>6} patents  ({r['share_pct']}%)")

    print()
    print_line("─")
    print("  Q4 · PATENTS PER YEAR")
    print_line("─")
    for r in yearly:
        bar = "█" * min(40, r["patent_count"] // max(1, total // 500))
        print(f"  {r['year']}  {bar:<40}  {r['patent_count']:,}")

    print()
    print_line("─")
    print("  Q6 · CTE — TOP COMPANIES (avg patents/year)")
    print_line("─")
    print(f"  {'Rank':<5} {'Company':<38} {'Total':>7} {'Yrs':>4} {'Avg/yr':>7}")
    for r in cte_result:
        print(f"  {r['rank']:<5} {r['company_name']:<38} {r['total_patents']:>7} {r['active_years']:>4} {r['avg_per_year']:>7}")

    print()
    print_line("─")
    print("  Q7 · INVENTOR RANKINGS (window functions)")
    print_line("─")
    print(f"  {'#':<5} {'C.Rank':<8} {'Inventor':<30} {'Country':<8} {'Patents':>7}")
    for r in ranked[:15]:
        print(f"  {r['overall_rank']:<5} {r['country_rank']:<8} {r['inventor_name']:<30} {r['country']:<8} {r['patent_count']:>7}")

    print()
    print_line()
    print("  END OF REPORT")
    print_line()

    return dict(total=total, inventors=inventors, companies=companies,
                countries=countries, yearly=yearly)

# ── Save CSVs ────────────────────────────────────────────────────

def save_csv(rows, filename):
    if not rows:
        return
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved {filename} ({len(rows)} rows)")

# ── Save JSON ────────────────────────────────────────────────────

def save_json(data):
    report = {
        "total_patents": data["total"],
        "top_inventors": [{"rank": i+1, "name": r["inventor_name"],
                           "country": r["country"], "patents": r["patent_count"]}
                          for i, r in enumerate(data["inventors"][:10])],
        "top_companies": [{"rank": i+1, "name": r["company_name"],
                           "patents": r["patent_count"]}
                          for i, r in enumerate(data["companies"][:10])],
        "top_countries": [{"rank": i+1, "country": r["country"],
                           "patents": r["patent_count"], "share_pct": r["share_pct"]}
                          for i, r in enumerate(data["countries"][:10])],
        "yearly_trends": [{"year": r["year"], "patents": r["patent_count"]}
                          for r in data["yearly"]],
    }
    path = os.path.join(REPORTS_DIR, "report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved report.json")

# ── Main ─────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        data = console_report(conn)
        print("\nSaving CSV files...")
        save_csv(data["inventors"], "top_inventors.csv")
        save_csv(data["companies"], "top_companies.csv")
        save_csv(data["countries"], "country_trends.csv")
        save_csv(data["yearly"],    "yearly_trends.csv")
        print("\nSaving JSON report...")
        save_json(data)
        join_rows = run_query(conn, Q5_JOIN)
        save_csv(join_rows, "join_sample.csv")
    finally:
        conn.close()
    print("\nAll reports saved to the reports/ folder!")

if __name__ == "__main__":
    main()