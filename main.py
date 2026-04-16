"""
main.py — Full pipeline runner
================================
1. Reads order.json for the current article URL
2. Runs extractor  → tries to populate new_assets/
3. If image found  → runs make_post for EN + FR, increments index
4. If no image     → skips to next article, increments index, retries
   (gives up after MAX_ATTEMPTS consecutive failures)

Run source_generator.py first to populate order.json:
    python source_generator.py

Then run the pipeline:
    python main.py
"""

import os
import sys
import json
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

# ── paths ────────────────────────────────────────────────────────────────────

ROOT         = os.path.dirname(os.path.abspath(__file__))
NEW_ASSETS   = os.path.join(ROOT, "new_assets")
DUMP_DIR     = os.path.join(ROOT, "dump_outputs")
ORDER_FILE   = os.path.join(ROOT, "order.json")

TEXT_FILE    = os.path.join(NEW_ASSETS, "inpost.txt")
TEXT_FILE_FR = os.path.join(NEW_ASSETS, "inpost_fr.txt")
IMAGE_FILE   = os.path.join(NEW_ASSETS, "image.png")
LOGO_FILE    = os.path.join(ROOT, "assets", "logo.png")

MAX_ATTEMPTS = 5   # max consecutive articles to try before giving up

# ── load order.json ──────────────────────────────────────────────────────────

def load_order():
    if not os.path.exists(ORDER_FILE):
        print("order.json not found. Run: python source_generator.py")
        sys.exit(1)
    with open(ORDER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_order(data):
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── imports ──────────────────────────────────────────────────────────────────

sys.path.insert(0, ROOT)
from scraping.extractor import run as extract
from make_post import make_post

# ── pipeline ─────────────────────────────────────────────────────────────────

order   = load_order()
entries = order.get("entries", [])
total   = len(entries)

if total == 0:
    print("order.json has no entries. Run: python source_generator.py")
    sys.exit(1)

succeeded = False

for attempt in range(MAX_ATTEMPTS):
    current = order.get("current", 0) % total
    entry   = entries[current]
    url     = entry["link"]
    title   = entry.get("title", "")

    print()
    print("=" * 55)
    print(f"STEP 1 — Scraping  [{current + 1}/{total}]")
    print(f"  {title[:60]}")
    print("=" * 55)

    try:
        extract(url=url, title_hint=title)
    except SystemExit:
        # extractor calls sys.exit(1) when no image / no text found
        print(f"  Skipping → no usable content. Moving to next article.")
        order["current"] = (current + 1) % total
        save_order(order)
        continue

    # verify both asset files were created
    missing = [p for p in (TEXT_FILE, TEXT_FILE_FR, IMAGE_FILE) if not os.path.exists(p)]
    if missing:
        print(f"  Skipping → missing assets: {missing}")
        order["current"] = (current + 1) % total
        save_order(order)
        continue

    # ── STEP 2 ──────────────────────────────────────────────────────────────
    print()
    print("=" * 55)
    print("STEP 2 — Generating post images")
    print("=" * 55)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(DUMP_DIR, exist_ok=True)
    out_en = os.path.join(DUMP_DIR, f"{stamp}_post_en.png")
    out_fr = os.path.join(DUMP_DIR, f"{stamp}_post_fr.png")

    make_post(TEXT_FILE,    IMAGE_FILE, LOGO_FILE, out_en)
    make_post(TEXT_FILE_FR, IMAGE_FILE, LOGO_FILE, out_fr)

    # success — advance index
    order["current"] = (current + 1) % total
    save_order(order)

    print()
    print("Done!")
    print(f"  EN → {out_en}")
    print(f"  FR → {out_fr}")
    print(f"  Next run will use index {order['current']}  ({entries[order['current']]['title'][:50]}...)")
    succeeded = True
    break

if not succeeded:
    print(f"\nGave up after {MAX_ATTEMPTS} consecutive failures. Try: python source_generator.py --reset")
