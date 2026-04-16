"""
nano-banana.py
==============
Alternative pipeline — uses Gemini for text + Pexels real estate / skyline
images (different every run) instead of scraping article pages.

Reads current article title from order.json, generates EN + FR post copy
with Gemini, fetches a fresh real estate or skyline image from Pexels,
and saves timestamped posts to dump_outputs/.

Usage:
    python nano-banana.py
"""

import os
import sys
import io
import json
import random
from datetime import datetime

import requests
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

# ── CONFIG ───────────────────────────────────────────────────────────────────

ROOT       = os.path.dirname(os.path.abspath(__file__))
ORDER_FILE = os.path.join(ROOT, "order.json")
NEW_ASSETS = os.path.join(ROOT, "new_assets")
DUMP_DIR   = os.path.join(ROOT, "dump_outputs")
LOGO_FILE  = os.path.join(ROOT, "assets", "logo.png")

# Rotate through varied real estate / skyline search terms for image variety
IMAGE_QUERIES = [
    "Dubai skyline night",
    "Dubai skyscrapers aerial",
    "luxury real estate Dubai",
    "Dubai Marina buildings",
    "Dubai downtown architecture",
    "Burj Khalifa cityscape",
    "Dubai city aerial view",
    "modern glass skyscraper",
    "luxury apartment building facade",
    "real estate tower sunset",
    "Dubai Palm Jumeirah aerial",
    "futuristic city buildings",
]

# ── GEMINI VIA OPENROUTER ────────────────────────────────────────────────────

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY2"),
    base_url="https://openrouter.ai/api/v1",
)

# ── HELPERS ──────────────────────────────────────────────────────────────────

def load_order():
    if not os.path.exists(ORDER_FILE):
        print("order.json not found. Run: python source_generator.py")
        sys.exit(1)
    with open(ORDER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_order(data):
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def gemini_summarise(title):
    """Call Gemini to generate TAG / HEADLINE / SUBLINE in EN + FR."""
    prompt = f"""You are a social media content writer for an Instagram page called "THE VALORISIMO VIEW".

Given this news headline, write exactly 6 lines — English first, then French.

English:
TAG: THE VALORISIMO VIEW
HEADLINE: <punchy question or statement, max 10 words>
SUBLINE: <one spicy clarifying sentence, max 15 words>

French:
TAG: THE VALORISIMO VIEW
HEADLINE: <same headline in French>
SUBLINE: <same subline in French>

Rules:
- TAG is always: THE VALORISIMO VIEW
- No extra lines, no labels, no markdown

Headline: {title}
"""
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw   = response.choices[0].message.content.strip()
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    def to_block(trio):
        keys = ["TAG", "HEADLINE", "SUBLINE"]
        result = []
        for key, line in zip(keys, trio):
            for prefix in [f"{key}:", f"{key} :"]:
                if line.upper().startswith(prefix.upper()):
                    line = line[len(prefix):].strip()
                    break
            result.append(f"{key}: {line}")
        return "\n".join(result)

    return to_block(lines[:3]), to_block(lines[3:6])

def pexels_image(save_path):
    """Pick a random query from IMAGE_QUERIES, fetch a random Pexels photo."""
    api_key = os.getenv("PEXELS_API_KEY")
    query   = random.choice(IMAGE_QUERIES)
    print(f"  Pexels query: '{query}'")

    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": 15, "orientation": "landscape"},
        timeout=15,
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        raise RuntimeError(f"No Pexels results for '{query}'")

    photo   = random.choice(photos)
    img_url = photo["src"].get("original") or photo["src"]["large2x"]
    raw     = requests.get(img_url, timeout=30).content

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.save(save_path, "PNG")
    print(f"  Image [{img.width}x{img.height}] id:{photo['id']} saved")

# ── MAIN ─────────────────────────────────────────────────────────────────────

def run():
    os.makedirs(NEW_ASSETS, exist_ok=True)
    os.makedirs(DUMP_DIR,   exist_ok=True)

    # 1. Get current article title from order.json
    order   = load_order()
    entries = order.get("entries", [])
    total   = len(entries)
    if not total:
        print("No entries in order.json. Run: python source_generator.py")
        sys.exit(1)

    current = order.get("current", 0) % total
    entry   = entries[current]
    title   = entry.get("title", "Dubai real estate news")

    print("=" * 55)
    print(f"nano-banana  [{current + 1}/{total}]")
    print(f"  {title[:65]}")
    print("=" * 55)

    # 2. Gemini -> EN + FR copy
    print("  Calling Gemini...")
    en_block, fr_block = gemini_summarise(title)
    print(f"\n[EN]\n{en_block}\n\n[FR]\n{fr_block}\n")

    # 3. Write inpost files
    en_path = os.path.join(NEW_ASSETS, "inpost.txt")
    fr_path = os.path.join(NEW_ASSETS, "inpost_fr.txt")
    open(en_path, "w", encoding="utf-8").write(en_block + "\n")
    open(fr_path, "w", encoding="utf-8").write(fr_block + "\n")

    # 4. Pexels real estate / skyline image
    img_path = os.path.join(NEW_ASSETS, "image.png")
    pexels_image(img_path)

    # 5. Compose posts
    print()
    print("  Composing posts...")
    sys.path.insert(0, ROOT)
    from make_post import make_post

    stamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_en = os.path.join(DUMP_DIR, f"{stamp}_nb_en.png")
    out_fr = os.path.join(DUMP_DIR, f"{stamp}_nb_fr.png")

    make_post(en_path, img_path, LOGO_FILE, out_en)
    make_post(fr_path, img_path, LOGO_FILE, out_fr)

    # 6. Advance order index
    order["current"] = (current + 1) % total
    save_order(order)

    print()
    print("Done!")
    print(f"  EN -> {out_en}")
    print(f"  FR -> {out_fr}")

if __name__ == "__main__":
    run()
