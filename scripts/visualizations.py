"""
visualizations.py
Génère des graphiques à partir des données de brevets.
Run: python scripts/visualizations.py
"""

import os
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "patents.db")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_data(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

def chart_yearly_trends():
    print("  Creating yearly trends chart...")
    df = get_data("""
        SELECT year, COUNT(*) as patent_count
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["year"], df["patent_count"], color="#2196F3",
            linewidth=2.5, marker="o", markersize=4)
    ax.fill_between(df["year"], df["patent_count"], alpha=0.15, color="#2196F3")
    ax.set_title("Patent Grants Per Year (1976–2025)", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Patents", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_facecolor("#f9f9f9")
    fig.tight_layout()
    path = os.path.join(REPORTS_DIR, "chart_yearly_trends.png")
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"    ✔  Saved chart_yearly_trends.png")

def chart_top_countries():
    print("  Creating top countries chart...")
    df = get_data("""
        SELECT i.country,
               COUNT(DISTINCT r.patent_id) AS patent_count
        FROM inventors i
        JOIN relationships r ON r.inventor_id = i.inventor_id
        WHERE i.country NOT IN ('UNKNOWN', '')
        GROUP BY i.country
        ORDER BY patent_count DESC
        LIMIT 10
    """)
    colors = ["#2196F3","#4CAF50","#FF5722","#9C27B0","#FF9800",
              "#00BCD4","#E91E63","#8BC34A","#FFC107","#3F51B5"]
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        df["patent_count"],
        labels=df["country"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.82,
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Top 10 Countries by Patent Count", fontsize=16,
                 fontweight="bold", pad=20)
    fig.tight_layout()
    path = os.path.join(REPORTS_DIR, "chart_top_countries.png")
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"    ✔  Saved chart_top_countries.png")

def chart_top_companies():
    print("  Creating top companies chart...")
    df = get_data("""
        SELECT c.name AS company_name,
               COUNT(DISTINCT r.patent_id) AS patent_count
        FROM companies c
        JOIN relationships r ON r.company_id = c.company_id
        GROUP BY c.company_id
        ORDER BY patent_count DESC
        LIMIT 10
    """)
    # Shorten long names
    df["short_name"] = df["company_name"].apply(
        lambda x: x[:30] + "..." if len(x) > 30 else x
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df["short_name"][::-1], df["patent_count"][::-1],
                   color="#2196F3", edgecolor="white")
    for bar, val in zip(bars, df["patent_count"][::-1]):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9)
    ax.set_title("Top 10 Companies by Patent Count", fontsize=16,
                 fontweight="bold", pad=15)
    ax.set_xlabel("Number of Patents", fontsize=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_facecolor("#f9f9f9")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    fig.tight_layout()
    path = os.path.join(REPORTS_DIR, "chart_top_companies.png")
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"    ✔  Saved chart_top_companies.png")

def chart_top_inventors():
    print("  Creating top inventors chart...")
    df = get_data("""
        SELECT i.name AS inventor_name,
               COUNT(DISTINCT r.patent_id) AS patent_count
        FROM inventors i
        JOIN relationships r ON r.inventor_id = i.inventor_id
        GROUP BY i.inventor_id
        ORDER BY patent_count DESC
        LIMIT 10
    """)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df["inventor_name"][::-1], df["patent_count"][::-1],
                   color="#4CAF50", edgecolor="white")
    for bar, val in zip(bars, df["patent_count"][::-1]):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9)
    ax.set_title("Top 10 Inventors by Patent Count", fontsize=16,
                 fontweight="bold", pad=15)
    ax.set_xlabel("Number of Patents", fontsize=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_facecolor("#f9f9f9")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    fig.tight_layout()
    path = os.path.join(REPORTS_DIR, "chart_top_inventors.png")
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"    ✔  Saved chart_top_inventors.png")

def main():
    print("=" * 60)
    print("  Generating visualizations...")
    print("=" * 60)
    chart_yearly_trends()
    chart_top_countries()
    chart_top_companies()
    chart_top_inventors()
    print()
    print("=" * 60)
    print("  ✔  All charts saved to reports/")
    print("=" * 60)

if __name__ == "__main__":
    main()