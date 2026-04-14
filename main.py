"""
main.py — Full pipeline runner
================================
1. Runs extractor  → populates new_assets/image.png + new_assets/inpost.txt
2. Runs make_post  → reads new_assets/, writes output/post.png

Usage:
    python main.py
"""

import os
import sys
sys.stdout.reconfigure(encoding="utf-8")

# ── paths ────────────────────────────────────────────────────────────────────

ROOT       = os.path.dirname(os.path.abspath(__file__))
NEW_ASSETS = os.path.join(ROOT, "new_assets")
OUTPUT_DIR = os.path.join(ROOT, "output")

TEXT_FILE  = os.path.join(NEW_ASSETS, "inpost.txt")
IMAGE_FILE = os.path.join(NEW_ASSETS, "image.png")
LOGO_FILE  = os.path.join(ROOT, "assets", "logo.png")
OUTPUT_FILE= os.path.join(OUTPUT_DIR, "post.png")

# ── step 1: scrape ───────────────────────────────────────────────────────────

print("=" * 50)
print("STEP 1 — Scraping article")
print("=" * 50)

sys.path.insert(0, ROOT)
from scraping.extractor import run as extract
extract()

# verify outputs exist
for path, label in [(TEXT_FILE, "inpost.txt"), (IMAGE_FILE, "image.png")]:
    if not os.path.exists(path):
        print(f"✗ Extractor did not produce {label}. Aborting.")
        sys.exit(1)

# ── step 2: generate post ────────────────────────────────────────────────────

print()
print("=" * 50)
print("STEP 2 — Generating post image")
print("=" * 50)

os.makedirs(OUTPUT_DIR, exist_ok=True)

from make_post import make_post
make_post(TEXT_FILE, IMAGE_FILE, LOGO_FILE, OUTPUT_FILE)

print()
print(f"Done!  →  {OUTPUT_FILE}")
