"""
dashboard.py
Professional Patent Intelligence Dashboard
Run: streamlit run dashboard.py
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DB_PATH = os.path.join(os.path.dirname(__file__), "patents.db")

st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="https://www.gstatic.com/images/branding/product/1x/patents_48dp.png",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@300;400;500&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .top-bar { background: #1a73e8; padding: 18px 32px; border-radius: 8px; margin-bottom: 24px; display: flex; align-items: center; gap: 16px; }
    .top-bar h1 { color: white; font-family: 'Google Sans', sans-serif; font-size: 24px; font-weight: 500; margin: 0; }
    .top-bar p { color: rgba(255,255,255,0.85); font-size: 13px; margin: 4px 0 0 0; }
    .kpi-card { background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .kpi-icon { font-family: 'Material Icons'; font-size: 32px; color: #1a73e8; display: block; margin-bottom: 8px; }
    .kpi-value { font-family: 'Google Sans', sans-serif; font-size: 28px; font-weight: 700; color: #202124; display: block; }
    .kpi-label { font-size: 13px; color: #5f6368; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .section-header { display: flex; align-items: center; gap: 10px; margin: 24px 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #1a73e8; }
    .section-header span.material-icons { font-family: 'Material Icons'; color: #1a73e8; font-size: 22px; }
    .section-header h2 { font-family: 'Google Sans', sans-serif; font-size: 18px; font-weight: 500; color: #202124; margin: 0; }
    .stTextInput input { border-radius: 24px !important; border: 1px solid #dadce0 !important; padding: 10px 20px !important; font-size: 14px !important; }
    .footer { text-align: center; color: #5f6368; font-size: 12px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e0e0e0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
""", unsafe_allow_html=True)


@st.cache_data
def get_data(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_category_data():
    uspc_df = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data", "raw", "g_uspc_at_issue.tsv"),
        sep="\t",
        usecols=["patent_id", "uspc_mainclass_id", "uspc_mainclass_title"],
        dtype=str,
        on_bad_lines="skip",
        nrows=3000000,
    )
    uspc_df = uspc_df.dropna(subset=["uspc_mainclass_id", "uspc_mainclass_title"])
    uspc_df = uspc_df.drop_duplicates(subset="patent_id", keep="first")
    conn = sqlite3.connect(DB_PATH)
    valid_ids = pd.read_sql("SELECT patent_id, year FROM patents WHERE year IS NOT NULL", conn)
    conn.close()
    uspc_df = uspc_df[uspc_df["patent_id"].isin(valid_ids["patent_id"])]
    uspc_df = uspc_df.merge(valid_ids, on="patent_id", how="inner")
    return uspc_df


# ── Header ──────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
    <span class="material-icons" style="font-size:40px; color:white;">lightbulb</span>
    <div>
        <h1>Global Patent Intelligence Dashboard</h1>
        <p>9,454,161 real patents · 1976–2025 · Source: PatentsView / USPTO Open Data Portal</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── KPI Cards ───────────────────────────────────────────────────
total     = get_data("SELECT COUNT(*) as n FROM patents")["n"][0]
inventors = get_data("SELECT COUNT(*) as n FROM inventors")["n"][0]
companies = get_data("SELECT COUNT(*) as n FROM companies")["n"][0]
countries = get_data("SELECT COUNT(DISTINCT country) as n FROM inventors WHERE country != 'UNKNOWN'")["n"][0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-card"><span class="kpi-icon material-icons">description</span><span class="kpi-value">{total:,}</span><span class="kpi-label">Total Patents</span></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card"><span class="kpi-icon material-icons">person</span><span class="kpi-value">{inventors:,}</span><span class="kpi-label">Inventors</span></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card"><span class="kpi-icon material-icons">business</span><span class="kpi-value">{companies:,}</span><span class="kpi-label">Companies</span></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card"><span class="kpi-icon material-icons">public</span><span class="kpi-value">{countries:,}</span><span class="kpi-label">Countries</span></div>""", unsafe_allow_html=True)


# ── Yearly Trends ───────────────────────────────────────────────
st.markdown("""<div class="section-header"><span class="material-icons">trending_up</span><h2>Patent Grants Per Year (1976–2025)</h2></div>""", unsafe_allow_html=True)

yearly = get_data("SELECT year, COUNT(*) as patent_count FROM patents WHERE year IS NOT NULL GROUP BY year ORDER BY year")
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(yearly["year"], yearly["patent_count"], color="#1a73e8", linewidth=2.5, marker="o", markersize=3)
ax.fill_between(yearly["year"], yearly["patent_count"], alpha=0.12, color="#1a73e8")
ax.set_xlabel("Year", fontsize=11, color="#5f6368")
ax.set_ylabel("Number of Patents", fontsize=11, color="#5f6368")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.grid(axis="y", linestyle="--", alpha=0.4, color="#dadce0")
ax.set_facecolor("white")
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
st.pyplot(fig)
plt.close()


# ── Countries + Companies ────────────────────────────────────────
st.markdown("""<div class="section-header"><span class="material-icons">bar_chart</span><h2>Top Countries and Companies</h2></div>""", unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown("**Top 10 Countries by Patent Output**")
    countries_df = get_data("""
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS patent_count
        FROM inventors i
        JOIN relationships r ON r.inventor_id = i.inventor_id
        WHERE i.country NOT IN ('UNKNOWN', '')
        GROUP BY i.country ORDER BY patent_count DESC LIMIT 10
    """)
    colors = ["#1a73e8","#34a853","#ea4335","#fbbc04","#ff6d00","#00897b","#8e24aa","#43a047","#e53935","#3949ab"]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.pie(countries_df["patent_count"], labels=countries_df["country"], autopct="%1.1f%%", colors=colors, startangle=140, pctdistance=0.82)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()

with right:
    st.markdown("**Top 10 Companies by Patent Count**")
    companies_df = get_data("""
        SELECT c.name AS company_name, COUNT(DISTINCT r.patent_id) AS patent_count
        FROM companies c
        JOIN relationships r ON r.company_id = c.company_id
        GROUP BY c.company_id ORDER BY patent_count DESC LIMIT 10
    """)
    companies_df["short_name"] = companies_df["company_name"].apply(lambda x: x[:28] + "..." if len(x) > 28 else x)
    fig, ax = plt.subplots(figsize=(7, 6))
    bars = ax.barh(companies_df["short_name"][::-1], companies_df["patent_count"][::-1], color="#1a73e8", edgecolor="white", height=0.6)
    for bar, val in zip(bars, companies_df["patent_count"][::-1]):
        ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height() / 2, f"{int(val):,}", va="center", fontsize=9, color="#5f6368")
    ax.set_xlabel("Number of Patents", fontsize=10, color="#5f6368")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()


# ── Top Inventors ───────────────────────────────────────────────
st.markdown("""<div class="section-header"><span class="material-icons">emoji_events</span><h2>Top 20 Inventors</h2></div>""", unsafe_allow_html=True)

inventors_df = get_data("""
    SELECT i.name AS inventor_name, i.country, COUNT(DISTINCT r.patent_id) AS patent_count
    FROM inventors i
    JOIN relationships r ON r.inventor_id = i.inventor_id
    GROUP BY i.inventor_id ORDER BY patent_count DESC LIMIT 20
""")
fig, ax = plt.subplots(figsize=(14, 8))
bars = ax.barh(inventors_df["inventor_name"][::-1], inventors_df["patent_count"][::-1], color="#34a853", edgecolor="white", height=0.6)
for i, (val, country) in enumerate(zip(inventors_df["patent_count"][::-1], inventors_df["country"][::-1])):
    ax.text(val + 10, i, f"{int(val):,}  [{country}]", va="center", fontsize=9, color="#5f6368")
ax.set_xlabel("Number of Patents", fontsize=11, color="#5f6368")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_facecolor("white")
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
fig.tight_layout()
st.pyplot(fig)
plt.close()


# ── Category Analysis ────────────────────────────────────────────
st.markdown("""<div class="section-header"><span class="material-icons">category</span><h2>Advanced Patent Category Analysis</h2></div>""", unsafe_allow_html=True)

with st.spinner("Loading category data..."):
    uspc_df = get_category_data()

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

# Chart 1 — Top categories
st.markdown("**Top 15 Patent Categories (USPC Classification)**")
fig, ax = plt.subplots(figsize=(14, 8))
bars = ax.barh(top_categories["short_title"][::-1], top_categories["patent_count"][::-1], color="#1a73e8", edgecolor="white", height=0.6)
for bar, val in zip(bars, top_categories["patent_count"][::-1]):
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2, f"{int(val):,}", va="center", fontsize=9, color="#5f6368")
ax.set_xlabel("Number of Patents", fontsize=11, color="#5f6368")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_facecolor("white")
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
fig.tight_layout()
st.pyplot(fig)
plt.close()

# Chart 2 — Category trends over time
st.markdown("**Top 5 Categories Over Time**")
top5 = top_categories["uspc_mainclass_id"].head(5).tolist()
top5_titles = dict(zip(top_categories["uspc_mainclass_id"].head(5), top_categories["short_title"].head(5)))
trend_df = (
    uspc_df[uspc_df["uspc_mainclass_id"].isin(top5)]
    .groupby(["year", "uspc_mainclass_id"])
    .size()
    .reset_index(name="count")
)
colors = ["#1a73e8", "#34a853", "#ea4335", "#fbbc04", "#ff6d00"]
fig, ax = plt.subplots(figsize=(14, 6))
for i, cat_id in enumerate(top5):
    cat_data = trend_df[trend_df["uspc_mainclass_id"] == cat_id]
    if len(cat_data) > 0:
        ax.plot(cat_data["year"], cat_data["count"], color=colors[i], linewidth=2, marker="o", markersize=3, label=top5_titles.get(cat_id, cat_id)[:30])
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
st.pyplot(fig)
plt.close()

# Interactive selector
st.markdown("**Explore a Specific Category**")
category_options = dict(zip(top_categories["short_title"], top_categories["uspc_mainclass_id"]))
selected = st.selectbox("Select a patent category:", list(category_options.keys()))
if selected:
    selected_id = category_options[selected]
    count = len(uspc_df[uspc_df["uspc_mainclass_id"] == selected_id])
    st.info(f"**{selected}** contains **{count:,}** patents in our database")

    conn = sqlite3.connect(DB_PATH)
    companies_df = pd.read_sql("""
        SELECT r.patent_id, c.name AS company_name
        FROM relationships r
        JOIN companies c ON c.company_id = r.company_id
        WHERE c.name IS NOT NULL
    """, conn)
    conn.close()

    cat_patents = uspc_df[uspc_df["uspc_mainclass_id"] == selected_id]["patent_id"]
    top_co = (
        companies_df[companies_df["patent_id"].isin(cat_patents)]
        .groupby("company_name").size()
        .reset_index(name="patent_count")
        .sort_values("patent_count", ascending=False)
        .head(10)
    )
    top_co["short_name"] = top_co["company_name"].apply(lambda x: x[:30] + "..." if len(str(x)) > 30 else x)

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.barh(top_co["short_name"][::-1], top_co["patent_count"][::-1], color="#34a853", edgecolor="white", height=0.6)
    for bar, val in zip(bars, top_co["patent_count"][::-1]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2, f"{int(val):,}", va="center", fontsize=9, color="#5f6368")
    ax.set_title(f"Top Companies in: {selected[:50]}", fontweight="bold")
    ax.set_xlabel("Patents", fontsize=10, color="#5f6368")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4, color="#dadce0")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()


# ── Search ──────────────────────────────────────────────────────
st.markdown("""<div class="section-header"><span class="material-icons">search</span><h2>Search Patents</h2></div>""", unsafe_allow_html=True)

search = st.text_input("", placeholder="Search patent titles e.g. artificial intelligence, battery, solar...")
if search:
    results = get_data(f"""
        SELECT patent_id, title, filing_date, year
        FROM patents WHERE title LIKE '%{search}%'
        LIMIT 50
    """)
    if len(results) == 0:
        st.warning("No patents found for this keyword.")
    else:
        st.success(f"Found {len(results)} patents matching '{search}'")
        st.dataframe(results, use_container_width=True, hide_index=True)


# ── Footer ──────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Global Patent Intelligence · Data source: PatentsView / USPTO Open Data Portal ·
    3,000,000 patents · 1976–2025
</div>
""", unsafe_allow_html=True)