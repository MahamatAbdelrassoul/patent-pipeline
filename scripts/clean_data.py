"""
clean_data.py
Reads the raw JSON, cleans it, and saves 4 tidy CSV files.
Run this second.
"""

import json
import os
import pandas as pd
import re

RAW_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "patents_raw.json")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def clean_text(text):
    """Remove extra spaces and weird characters from text."""
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text

def get_year(date_str):
    """Pull just the year from a date like 2023-05-12."""
    if not date_str:
        return None
    try:
        return int(str(date_str)[:4])
    except:
        return None

def build_patents(raw):
    rows = []
    for p in raw:
        rows.append({
            "patent_id":   clean_text(p.get("patent_id")),
            "title":       clean_text(p.get("patent_title")),
            "abstract":    clean_text(p.get("patent_abstract"))[:2000],
            "filing_date": clean_text(p.get("patent_date")),
            "year":        get_year(p.get("patent_date")),
        })
    df = pd.DataFrame(rows)
    df = df[df["patent_id"].str.len() > 0]   # remove rows with no ID
    df = df[df["title"].str.len() > 0]        # remove rows with no title
    df = df.drop_duplicates(subset="patent_id")
    return df

def build_inventors(raw):
    rows = []
    seen = set()
    for p in raw:
        for inv in (p.get("inventors") or []):
            inv_id = clean_text(inv.get("inventor_id"))
            if not inv_id or inv_id in seen:
                continue
            seen.add(inv_id)
            first = clean_text(inv.get("inventor_first_name"))
            last  = clean_text(inv.get("inventor_last_name"))
            rows.append({
                "inventor_id": inv_id,
                "name":        f"{first} {last}".strip() or "Unknown",
                "country":     (clean_text(inv.get("inventor_country")) or "Unknown").upper(),
            })
    return pd.DataFrame(rows)

def build_companies(raw):
    rows = []
    seen = set()
    for p in raw:
        for asg in (p.get("assignees") or []):
            co_id   = clean_text(asg.get("assignee_id"))
            co_name = clean_text(asg.get("assignee_organization"))
            if not co_id or co_id in seen or not co_name:
                continue
            seen.add(co_id)
            rows.append({"company_id": co_id, "name": co_name})
    return pd.DataFrame(rows)

def build_relationships(raw):
    rows = []
    for p in raw:
        patent_id = clean_text(p.get("patent_id"))
        if not patent_id:
            continue
        inv_ids = [clean_text(i.get("inventor_id")) for i in (p.get("inventors") or [])
                   if clean_text(i.get("inventor_id"))]
        co_ids  = [clean_text(a.get("assignee_id")) for a in (p.get("assignees") or [])
                   if clean_text(a.get("assignee_id"))]
        for inv_id in (inv_ids or [None]):
            for co_id in (co_ids or [None]):
                rows.append({"patent_id": patent_id,
                             "inventor_id": inv_id,
                             "company_id": co_id})
    df = pd.DataFrame(rows)
    return df.drop_duplicates()

def main():
    print("Loading raw data...")
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    print(f"  Loaded {len(raw)} records")

    print("Cleaning data...")
    patents       = build_patents(raw)
    inventors     = build_inventors(raw)
    companies     = build_companies(raw)
    relationships = build_relationships(raw)

    print("Saving cleaned CSV files...")
    patents.to_csv(      os.path.join(CLEAN_DIR, "clean_patents.csv"),       index=False)
    inventors.to_csv(    os.path.join(CLEAN_DIR, "clean_inventors.csv"),     index=False)
    companies.to_csv(    os.path.join(CLEAN_DIR, "clean_companies.csv"),     index=False)
    relationships.to_csv(os.path.join(CLEAN_DIR, "clean_relationships.csv"), index=False)

    print(f"\nDone!")
    print(f"  clean_patents.csv       → {len(patents)} rows")
    print(f"  clean_inventors.csv     → {len(inventors)} rows")
    print(f"  clean_companies.csv     → {len(companies)} rows")
    print(f"  clean_relationships.csv → {len(relationships)} rows")

if __name__ == "__main__":
    main()