"""
extractor.py - Scrape a webpage and prep assets for make_post.py
=================================================================
- Downloads the first usable image -> new_assets/image.png
- Extracts a few paragraphs of text, summarises via LLM
- Writes TAG / HEADLINE / SUBLINE   -> new_assets/inpost.txt

Output format:
    TAG: THE VALORISIMO VIEW
    HEADLINE: Will a Ceasefire Boost Dubai Real Estate?
    SUBLINE: Ceasefire Impact - Will Dubai Real Estate Rebound Instantly?

Usage:
    python scraping/extractor.py
"""

import os
import sys
import io
import requests
from bs4 import BeautifulSoup
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

# -- CONFIG -------------------------------------------------------------------
   # <- change this

TARGET_URL = "https://news.google.com/rss/articles/CBMiyAFBVV95cUxPTndxbWZINm1IMFRGM216TnJqR1FKekFsbXplUGVqcGlROWFtWDdLVXktN3RFQkpqNlhNTFBGcWhrempmVGQ2UGxZeldSZ2E4Z1lJTi00b0M5VGlCX1dIUXZKdzNxcWdMa2lfTGVNdUlrNnpsdG1rcWlCUnJrUFNhc2hhNFJTRFdFUGppMmNuel8zMnpCZXkzYjJSNS1mWVo1WmpNejdMUDQzY0Zva3F4MGsyQVRuaUpkaFRDUlZSQjdiRmpTZS1rbdIBzgFBVV95cUxOSGJhZnBwX3gwS1VGV2wybV9GRkFDTjEzaEJON3pLNDkzREdMaENzRDhYR0JyME1iQmVqU2p3aFdBQnRid3Bod0lVZ1BXWlhoUDZYa29pWmNvZXFrN05vU1pNTXJHTkdqM2trZHcyUVJYLVZGSUYyZnNqcDM0WFhjMWdPZFJxNVBydWV5c00ya0JLTzhndFozSjU3VU1BRW5rU1A5S29GeUVHQTl5ZlNCZXBXYmZ5My11UHFwLTRCZHlDQUlPUmlOSU1zbmlSdw?oc=5"
TAG        = "THE VALORISIMO VIEW"   # static brand tag
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "new_assets")

# -- SETUP --------------------------------------------------------------------

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# -- HELPERS ------------------------------------------------------------------

def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def extract_text(soup, max_paragraphs=5):
    """Return up to max_paragraphs of body text."""
    paragraphs = []
    for tag in soup.find_all(["p", "h1", "h2"]):
        text = tag.get_text(strip=True)
        if len(text) > 40:
            paragraphs.append(text)
        if len(paragraphs) >= max_paragraphs:
            break
    return "\n\n".join(paragraphs)

def fetch_pexels_image(query, save_path):
    """
    Search Pexels for `query`, pick a random photo from the results.
    Returns True on success, False on failure.
    """
    import random

    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("  PEXELS_API_KEY not set in .env")
        return False

    try:
        # fetch 15 results and pick one at random so each run gets a fresh image
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            timeout=15,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            print(f"  Pexels: no results for '{query}'")
            return False

        photo   = random.choice(photos)
        img_url = photo["src"].get("original") or photo["src"]["large2x"]
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()

        img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
        img.save(save_path, "PNG")
        print(f"  Pexels image [{img.width}x{img.height}] (id:{photo['id']}) -> {save_path}")
        return True

    except Exception as e:
        print(f"  Pexels fetch failed: {e}")
        return False

def summarise(text):
    """
    Ask the LLM to return both EN and FR versions in one call.
    Returns (english_block, french_block) as strings.
    """
    prompt = f"""You are a social media content writer for an Instagram page called "THE VALORISIMO VIEW".

Given the article text below, write exactly 6 lines — first the English version, then the French version.

English:
TAG: THE VALORISIMO VIEW
HEADLINE: <one punchy question or statement, max 10 words>
SUBLINE: <one clarifying sentence, max 15 words, can be spicy>

French:
TAG: THE VALORISIMO VIEW
HEADLINE: <same headline translated into French>
SUBLINE: <same subline translated into French>

Rules:
- TAG is always: THE VALORISIMO VIEW  (same in both languages)
- HEADLINE hooks the reader (question or bold claim)
- SUBLINE expands on the headline
- Output exactly 6 lines, no blank lines, no labels, no markdown

Article:
{text}
"""
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    def to_block(trio):
        """Ensure lines have TAG/HEADLINE/SUBLINE prefixes for make_post parser."""
        keys = ["TAG", "HEADLINE", "SUBLINE"]
        result = []
        for key, line in zip(keys, trio):
            # strip any existing prefix the LLM may or may not have included
            for prefix in [f"{key}:", f"{key} :"]:
                if line.upper().startswith(prefix.upper()):
                    line = line[len(prefix):].strip()
                    break
            result.append(f"{key}: {line}")
        return "\n".join(result)

    en_block = to_block(lines[:3])
    fr_block  = to_block(lines[3:6])
    return en_block, fr_block

# -- MAIN ---------------------------------------------------------------------

def run(url=None, title_hint=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    target = url or TARGET_URL
    print(f"Fetching: {target}")
    soup = fetch_page(target)

    # 1. Text — scrape page or fall back to RSS title
    text = extract_text(soup, max_paragraphs=5)
    if not text.strip():
        if title_hint:
            text = title_hint
            print(f"  No page text — using RSS title as context.")
        else:
            print("No usable text found — skipping.")
            sys.exit(1)
    print(f"  Text: {text[:80].strip()}...")

    # 2. Image — fetch from Pexels using article headline as search query
    image_path = os.path.join(OUTPUT_DIR, "image.png")
    search_query = " ".join(text.split()[:6])
    if not fetch_pexels_image(search_query, image_path):
        print("No image — skipping.")
        sys.exit(1)

    # 3. Summarise (single LLM call → EN + FR)
    print("  Calling LLM...")
    en_block, fr_block = summarise(text)
    print(f"\n[EN]\n{en_block}\n\n[FR]\n{fr_block}\n")

    # 4. Write inpost.txt (English)
    inpost_path = os.path.join(OUTPUT_DIR, "inpost.txt")
    with open(inpost_path, "w", encoding="utf-8") as f:
        f.write(en_block + "\n")
    print(f"  inpost.txt    saved -> {inpost_path}")

    # 5. Write inpost_fr.txt (French)
    inpost_fr_path = os.path.join(OUTPUT_DIR, "inpost_fr.txt")
    with open(inpost_fr_path, "w", encoding="utf-8") as f:
        f.write(fr_block + "\n")
    print(f"  inpost_fr.txt saved -> {inpost_fr_path}")

if __name__ == "__main__":
    run()
