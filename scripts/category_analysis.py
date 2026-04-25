"""
category_analysis.py
Advanced analysis of patent categories using USPC classification.
Run: python scripts/category_analysis.py
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "patents.db")
RAW_DIR     = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def main():
    print("=" * 60)
    print("  ADVANCED PATENT CATEGORY ANALYSIS")
    print("=" * 60)

    # ── Load USPC data ──────────────────────────────────────────
    print("\n  Loading category data...")
    uspc_df = pd.read_csv(
        os.path.join(RAW_DIR, "g_uspc_at_issue.tsv"),
        sep="\t",
        usecols=["patent_id", "uspc_mainclass_id", "uspc_mainclass_title"],
        dtype=str,
        on_bad_lines="skip",
        nrows=3000000,
    )
    uspc_df = uspc_df[uspc_df["uspc_sequence"] if "uspc_sequence" in uspc_df.columns else uspc_df.index >= 0]
    # Keep only primary classification (first per patent)
    uspc_df = uspc_df.dropna(subset=["uspc_mainclass_id", "uspc_mainclass_title"])
    uspc_df = uspc_df.drop_duplicates(subset="patent_id", keep="first")
    print(f"    → {len(uspc_df):,} patents with category data")

    # ── Get valid patent IDs from database ──────────────────────
    print("  Loading patent IDs from database...")
    conn = sqlite3.connect(DB_PATH)
    valid_ids = pd.read_sql("SELECT patent_id FROM patents", conn)["patent_id"]
    conn.close()
    uspc_df = uspc_df[uspc_df["patent_id"].isin(valid_ids)]
    print(f"    → {len(uspc_df):,} matched to our database")

    # ── Analysis 1: Top 15 patent categories ───────────────────
    print("\n  Analysis 1: Top patent categories...")
    top_categories = (
        uspc_df.groupby(["uspc_mainclass_id", "uspc_mainclass_title"])
        .size()
        .reset_index(name="patent_count")
        .sort_values("patent_count", ascending=False)
        .head(15)
    )
    top_categories["short_title"] = top_categories["uspc_mainclass_title"].apply(
        lambda x: x[:40] + "..." if len(str(x)) > 40 else x
    )

    # Save CSV
    top_categories.to_csv(
        os.path.join(REPORTS_DIR, "top_categories.csv"), index=False
    )
    print(f"    ✔  top_categories.csv saved")

    # Chart
    fig, ax = plt.subplots(figsize=(14, 8))
    bars = ax.barh(
        top_categories["short_title"][::-1],
        top_categories["patent_count"][::-1],
        color="#1a73e8", edgecolor="white", height=0.6
    )
    for bar, val in zip(bars, top_categories["patent_count"][::-1]):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9, color="#5f6368")
    ax.set_title("Top 15 Patent Categories (USPC Classification)",
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Patents", fontsize=11, color="#5f6368")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
    fig.tight_layout()
    fig.savefig(os.path.join(REPORTS_DIR, "chart_top_categories.png"), dpi=150)
    plt.close()
    print(f"    ✔  chart_top_categories.png saved")

    # ── Analysis 2: Category trends over time ──────────────────
    print("\n  Analysis 2: Top categories over time...")
    conn = sqlite3.connect(DB_PATH)
    years_df = pd.read_sql(
        "SELECT patent_id, year FROM patents WHERE year IS NOT NULL", conn
    )
    conn.close()

    merged = uspc_df.merge(years_df, on="patent_id", how="inner")

    # Get top 5 categories
    top5 = top_categories["uspc_mainclass_id"].head(5).tolist()
    top5_titles = dict(zip(
        top_categories["uspc_mainclass_id"].head(5),
        top_categories["short_title"].head(5)
    ))

    trend_df = (
        merged[merged["uspc_mainclass_id"].isin(top5)]
        .groupby(["year", "uspc_mainclass_id"])
        .size()
        .reset_index(name="count")
    )

    colors = ["#1a73e8", "#34a853", "#ea4335", "#fbbc04", "#ff6d00"]
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, cat_id in enumerate(top5):
        cat_data = trend_df[trend_df["uspc_mainclass_id"] == cat_id]
        if len(cat_data) > 0:
            ax.plot(
                cat_data["year"],
                cat_data["count"],
                color=colors[i],
                linewidth=2,
                marker="o",
                markersize=3,
                label=top5_titles.get(cat_id, cat_id)[:30]
            )
    ax.set_title("Top 5 Patent Categories Over Time",
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Year", fontsize=11, color="#5f6368")
    ax.set_ylabel("Number of Patents", fontsize=11, color="#5f6368")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(fontsize=8, loc="upper left")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#dadce0")
    fig.tight_layout()
    fig.savefig(os.path.join(REPORTS_DIR, "chart_category_trends.png"), dpi=150)
    plt.close()
    print(f"    ✔  chart_category_trends.png saved")

    # ── Analysis 3: Top companies per category ─────────────────
    print("\n  Analysis 3: Top companies per category...")
    conn = sqlite3.connect(DB_PATH)
    companies_df = pd.read_sql("""
        SELECT r.patent_id, c.name AS company_name
        FROM relationships r
        JOIN companies c ON c.company_id = r.company_id
        WHERE c.name IS NOT NULL
    """, conn)
    conn.close()

    cat_company = merged.merge(companies_df, on="patent_id", how="inner")
    top_cat_id = top_categories["uspc_mainclass_id"].iloc[0]
    top_cat_title = top_categories["uspc_mainclass_title"].iloc[0]

    top_co_in_cat = (
        cat_company[cat_company["uspc_mainclass_id"] == top_cat_id]
        .groupby("company_name")
        .size()
        .reset_index(name="patent_count")
        .sort_values("patent_count", ascending=False)
        .head(10)
    )
    top_co_in_cat["short_name"] = top_co_in_cat["company_name"].apply(
        lambda x: x[:30] + "..." if len(str(x)) > 30 else x
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(
        top_co_in_cat["short_name"][::-1],
        top_co_in_cat["patent_count"][::-1],
        color="#34a853", edgecolor="white", height=0.6
    )
    for bar, val in zip(bars, top_co_in_cat["patent_count"][::-1]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9, color="#5f6368")
    short_cat = top_cat_title[:50] + "..." if len(top_cat_title) > 50 else top_cat_title
    ax.set_title(f"Top Companies in: {short_cat}",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Patents", fontsize=11, color="#5f6368")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
    fig.tight_layout()
    fig.savefig(os.path.join(REPORTS_DIR, "chart_companies_in_top_category.png"), dpi=150)
    plt.close()
    print(f"    ✔  chart_companies_in_top_category.png saved")

    # ── Console Summary ─────────────────────────────────────────
    print()
    print("=" * 60)
    print("  TOP 10 PATENT CATEGORIES")
    print("=" * 60)
    for i, row in top_categories.head(10).iterrows():
        print(f"  {row['uspc_mainclass_id']:<10} {row['short_title']:<45} {int(row['patent_count']):>8,}")

    print()
    print("=" * 60)
    print("  ✔  Category analysis complete!")
    print("     Reports saved to reports/")
    print("=" * 60)

if __name__ == "__main__":
    main()