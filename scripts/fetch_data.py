"""
fetch_data.py
Downloads patent data from PatentsView API and saves it as raw JSON.
Run this first.
"""

import requests
import json
import time
import os

# Where to save the downloaded data
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# The website we are downloading from
BASE_URL = "https://api.patentsview.org/patents/query"

# Which fields (columns) we want from the data
FIELDS = [
    "patent_id",
    "patent_title",
    "patent_abstract",
    "patent_date",
    "inventors.inventor_id",
    "inventors.inventor_first_name",
    "inventors.inventor_last_name",
    "inventors.inventor_country",
    "assignees.assignee_id",
    "assignees.assignee_organization",
]

def fetch_page(page, per_page=500):
    """Download one page of patents from the API."""
    params = {
        "q": {"_gte": {"patent_date": "2015-01-01"}},
        "f": FIELDS,
        "o": {"page": page, "per_page": per_page},
        "s": [{"patent_date": "desc"}],
    }
    try:
        response = requests.post(BASE_URL, json=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error on page {page}: {e}")
        return None

def fetch_all(pages=10):
    """Download multiple pages and save them all."""
    all_patents = []
    print(f"Starting download: {pages} pages x 500 patents each...")

    for page in range(1, pages + 1):
        print(f"  Downloading page {page} of {pages}...", end=" ")
        data = fetch_page(page)

        if data is None:
            print("FAILED - skipping")
            continue

        patents = data.get("patents") or []
        print(f"Got {len(patents)} patents")
        all_patents.extend(patents)

        if len(patents) < 500:
            print("  No more data available.")
            break

        time.sleep(0.5)  # be polite, don't overload the server

    # Save everything to one file
    out_path = os.path.join(RAW_DIR, "patents_raw.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_patents, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Saved {len(all_patents)} patents to {out_path}")

# This runs when you execute the file
if __name__ == "__main__":
    fetch_all(pages=10)