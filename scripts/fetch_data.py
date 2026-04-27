import os, sqlite3
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "patents.db")
CHUNK_SIZE = 50000
MAX_PATENTS = 9999999

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS patents (patent_id TEXT PRIMARY KEY, title TEXT, abstract TEXT, filing_date TEXT, year INTEGER);
CREATE TABLE IF NOT EXISTS inventors (inventor_id TEXT PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE IF NOT EXISTS companies (company_id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS relationships (id INTEGER PRIMARY KEY AUTOINCREMENT, patent_id TEXT, inventor_id TEXT, company_id TEXT);
CREATE INDEX IF NOT EXISTS idx_rel_patent ON relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_rel_company ON relationships(company_id);
CREATE INDEX IF NOT EXISTS idx_pat_year ON patents(year);
"""

def get_year(date_str):
    try:
        return int(str(date_str)[:4])
    except:
        return None

def main():
    print("Removing old database...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    print("New database created!")

    print("Reading locations...")
    locations_df = pd.read_csv(os.path.join(RAW_DIR, "g_location_disambiguated.tsv"), sep="\t", usecols=["location_id","disambig_country"], dtype=str, on_bad_lines="skip")
    loc_index = locations_df.set_index("location_id")["disambig_country"].to_dict()
    print(f"  {len(loc_index):,} locations loaded")

    print("Reading abstracts...")
    abs_index = {}
    for chunk in pd.read_csv(os.path.join(RAW_DIR, "g_patent_abstract.tsv"), sep="\t", usecols=["patent_id","patent_abstract"], dtype=str, on_bad_lines="skip", chunksize=50000):
        for _, row in chunk.iterrows():
            pid = str(row.get("patent_id") or "").strip()
            if pid:
                abs_index[pid] = str(row.get("patent_abstract") or "").strip()[:2000]
    print(f"  {len(abs_index):,} abstracts loaded")

    print("Reading inventors...")
    inv_index = {}
    seen_inventors = set()
    for chunk in pd.read_csv(os.path.join(RAW_DIR, "g_inventor_disambiguated.tsv"), sep="\t", usecols=["patent_id","inventor_id","disambig_inventor_name_first","disambig_inventor_name_last","location_id"], dtype=str, on_bad_lines="skip", chunksize=50000):
        for _, row in chunk.iterrows():
            pid    = str(row.get("patent_id")   or "").strip()
            inv_id = str(row.get("inventor_id") or "").strip()
            if not pid or not inv_id:
                continue
            first   = str(row.get("disambig_inventor_name_first") or "").strip()
            last    = str(row.get("disambig_inventor_name_last")  or "").strip()
            loc_id  = str(row.get("location_id") or "").strip()
            country = str(loc_index.get(loc_id, "") or "").strip() or "Unknown"
            if pid not in inv_index:
                inv_index[pid] = []
            inv_index[pid].append({"inventor_id": inv_id, "name": f"{first} {last}".strip() or "Unknown", "country": country.upper()})
            seen_inventors.add(inv_id)
    print(f"  {len(seen_inventors):,} inventors loaded")

    print("Reading assignees...")
    asg_index = {}
    seen_companies = set()
    for chunk in pd.read_csv(os.path.join(RAW_DIR, "g_assignee_disambiguated.tsv"), sep="\t", usecols=["patent_id","assignee_id","disambig_assignee_organization","location_id"], dtype=str, on_bad_lines="skip", chunksize=50000):
        for _, row in chunk.iterrows():
            pid     = str(row.get("patent_id")    or "").strip()
            co_id   = str(row.get("assignee_id")  or "").strip()
            co_name = str(row.get("disambig_assignee_organization") or "").strip()
            if not pid or not co_id or not co_name:
                continue
            if pid not in asg_index:
                asg_index[pid] = []
            asg_index[pid].append({"company_id": co_id, "name": co_name})
            seen_companies.add(co_id)
    print(f"  {len(seen_companies):,} companies loaded")

    print("Processing patents and saving to database...")
    total_patents = 0
    total_relationships = 0
    seen_inv_db = set()
    seen_co_db  = set()

    for chunk_num, chunk in enumerate(pd.read_csv(
        os.path.join(RAW_DIR, "g_patent.tsv"),
        sep="\t",
        usecols=["patent_id","patent_title","patent_date","patent_type"],
        dtype=str,
        on_bad_lines="skip",
        chunksize=CHUNK_SIZE,
        nrows=MAX_PATENTS,
    )):
        patent_rows = []
        inventor_rows = []
        company_rows = []
        relationship_rows = []

        for _, row in chunk.iterrows():
            pid   = str(row.get("patent_id")    or "").strip()
            title = str(row.get("patent_title") or "").strip()
            date  = str(row.get("patent_date")  or "").strip()
            if not pid or not title:
                continue

            patent_rows.append((pid, title, abs_index.get(pid,""), date, get_year(date)))

            inv_list = inv_index.get(pid, [])
            co_list  = asg_index.get(pid, [])

            for inv in inv_list:
                if inv["inventor_id"] not in seen_inv_db:
                    inventor_rows.append((inv["inventor_id"], inv["name"], inv["country"]))
                    seen_inv_db.add(inv["inventor_id"])

            for co in co_list:
                if co["company_id"] not in seen_co_db:
                    company_rows.append((co["company_id"], co["name"]))
                    seen_co_db.add(co["company_id"])

            for inv in (inv_list or [{"inventor_id": None}]):
                for co in (co_list or [{"company_id": None}]):
                    relationship_rows.append((pid, inv.get("inventor_id"), co.get("company_id")))

        conn.executemany("INSERT OR IGNORE INTO patents VALUES (?,?,?,?,?)", patent_rows)
        conn.executemany("INSERT OR IGNORE INTO inventors VALUES (?,?,?)", inventor_rows)
        conn.executemany("INSERT OR IGNORE INTO companies VALUES (?,?)", company_rows)
        conn.executemany("INSERT OR IGNORE INTO relationships(patent_id,inventor_id,company_id) VALUES (?,?,?)", relationship_rows)
        conn.commit()

        total_patents += len(patent_rows)
        total_relationships += len(relationship_rows)
        print(f"  Chunk {chunk_num+1:>3} done — {total_patents:>9,} patents so far")

    conn.close()
    size_mb = os.path.getsize(DB_PATH) // (1024*1024)
    print(f"\nDONE! {total_patents:,} patents saved to database ({size_mb} MB)")
    print("Next: run clean_data.py")

if __name__ == "__main__":
    main()