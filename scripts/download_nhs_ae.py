#!/usr/bin/env python3
"""
download_nhs_ae.py

Downloads NHS England "Monthly A&E Attendances and Emergency Admissions"
trust-level CSV files from START_DATE to the latest release into data/raw/.

Source: https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/
Usage:  python3 scripts/download_nhs_ae.py
"""

import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------- Settings ----------
START_DATE = date(2021, 1, 1)      # earliest month to download
BASE = "https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project)"}

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]
MONTHS = {name: i for i, name in enumerate(MONTH_NAMES, start=1)}
MONTH_RE = re.compile(r"(" + "|".join(MONTH_NAMES) + r")\s+(\d{4})", re.IGNORECASE)


def fiscal_year_pages(start, today=None):
    """Build the NHS financial-year page URLs (April-March) from start up to today, newest first."""
    today = today or date.today()
    first_fy = start.year if start.month >= 4 else start.year - 1
    last_fy = today.year if today.month >= 4 else today.year - 1
    return [
        f"{BASE}ae-attendances-and-emergency-admissions-{fy}-{str(fy + 1)[-2:]}/"
        for fy in range(last_fy, first_fy - 1, -1)
    ]


def find_csv_links(page_url):
    """Return (month_date, link_text, file_url) for every monthly CSV link on a page."""
    resp = requests.get(page_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    found = []
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text().split())          # tidy up spaces/newlines
        lower = text.lower()
        href = a["href"].lower()

        # Match on reliable signals, not exact wording: NHS link text is typed by
        # people and can contain typos (e.g. July 2021 is "Monthly July 2021",
        # missing "A&E"). Require "monthly", a CSV file, and a readable month/year.
        is_monthly = "monthly" in lower
        is_csv = "csv" in lower or href.endswith(".csv")
        if not (is_monthly and is_csv):
            continue

        match = MONTH_RE.search(text)
        if not match:
            continue
        month_date = date(int(match.group(2)), MONTHS[match.group(1).lower()], 1)
        found.append((month_date, text, urljoin(page_url, a["href"])))
    return found


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Collect links from each financial year's page
    all_links = {}
    for page in fiscal_year_pages(START_DATE):
        print(f"Checking {page}")
        try:
            links = find_csv_links(page)
        except requests.RequestException as err:
            print(f"  Could not read page: {err}")
            continue
        print(f"  Found {len(links)} monthly CSV link(s)")
        for month_date, text, url in links:
            all_links.setdefault(month_date, (text, url))   # keep first if a month repeats
        time.sleep(1)                                        # be polite to the server

    # 2. Keep only months from START_DATE onwards, oldest first
    wanted = sorted((d, v) for d, v in all_links.items() if d >= START_DATE)
    if not wanted:
        print("No CSV links found. The page layout may have changed.")
        return
    print(f"\n{len(wanted)} month(s) available from {START_DATE:%B %Y}. Saving to {RAW_DIR}\n")

    # 3. Download each file with a consistent, sortable name
    downloaded = skipped = failed = 0
    for month_date, (text, url) in wanted:
        filename = f"{month_date:%Y-%m}_monthly_ae.csv"
        target = RAW_DIR / filename
        if target.exists():
            skipped += 1
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            target.write_bytes(resp.content)
            print(f"  Saved {filename} ({len(resp.content) / 1024:.0f} KB)  <- {text}")
            downloaded += 1
        except requests.RequestException as err:
            print(f"  FAILED {filename}: {err}")
            failed += 1
        time.sleep(1)

    # 4. Summary
    print(f"\nDone: {downloaded} downloaded, {skipped} already had, {failed} failed.")
    print(f"Range: {wanted[0][0]:%B %Y} to {wanted[-1][0]:%B %Y}")


if __name__ == "__main__":
    main()
