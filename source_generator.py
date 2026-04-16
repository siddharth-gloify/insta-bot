"""
source_generator.py — Build order.json from Google News RSS
=============================================================
Fetches the RSS feed, pulls every <link> + <title>, saves them
in order.json with a current index that the pipeline advances.

Usage:
    python source_generator.py            # refresh, keep current index
    python source_generator.py --reset    # refresh, reset index to 0
"""

import sys
import json
import argparse
import requests
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

RSS_URL    = "https://news.google.com/rss/search?q=Dubai+real+estate&hl=en-US&gl=US&ceid=US:en"
ORDER_FILE = "order.json"
HEADERS    = {"User-Agent": "Mozilla/5.0"}

def fetch_entries(rss_url):
    resp = requests.get(rss_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    entries = []
    for item in root.findall(".//item"):
        link  = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        if link:
            entries.append({"link": link, "title": title})
    return entries

def load_order():
    try:
        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current": 0, "entries": []}

def save_order(data):
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run(reset=False):
    print(f"Fetching: {RSS_URL}")
    entries = fetch_entries(RSS_URL)
    print(f"  Found {len(entries)} articles.")

    existing = load_order()
    current  = 0 if reset else existing.get("current", 0)

    save_order({"current": current, "entries": entries})
    print(f"  order.json updated  (starting at index {current})")
    print()
    for i, e in enumerate(entries[:8]):
        marker = " <-- next" if i == current else ""
        print(f"  [{i:02d}]{marker}  {e['title'][:65]}")
    if len(entries) > 8:
        print(f"  ... and {len(entries) - 8} more")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset index to 0")
    args = parser.parse_args()
    run(reset=args.reset)
