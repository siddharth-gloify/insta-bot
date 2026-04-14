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

TARGET_URL = "https://valorisimo.com/price-per-m2-in-abu-dhabi/"
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

SKIP_WORDS = [".svg", "icon", "logo", "avatar", "pixel", "1x1", "flag", "emoji", "facebook.com"]

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

def download_image(soup, base_url, save_path):
    """Find the first large enough image, convert to PNG and save."""
    from urllib.parse import urlparse

    for img in soup.find_all("img"):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src:
            continue

        # Normalise URL
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            parsed = urlparse(base_url)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"
        elif not src.startswith("http"):
            continue

        if any(w in src.lower() for w in SKIP_WORDS):
            continue

        try:
            img_resp = requests.get(src, headers=HEADERS, timeout=15)
            img_resp.raise_for_status()
            if "image" not in img_resp.headers.get("Content-Type", ""):
                continue
            if len(img_resp.content) < 5_000:
                continue

            # Convert any format (jpg, webp, ...) to PNG via Pillow
            image = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
            image.save(save_path, "PNG")
            print(f"  Image saved -> {save_path}")
            return True
        except Exception:
            continue

    return False

def summarise(text):
    """Ask the LLM to return TAG / HEADLINE / SUBLINE."""
    prompt = f"""You are a social media content writer for an Instagram page called "THE VALORISIMO VIEW".

Given the article text below, write exactly 3 lines:
TAG: THE VALORISIMO VIEW
HEADLINE: <one punchy question or statement, max 10 words>
SUBLINE: <one clarifying sentence, max 15 words>

Rules:
- TAG must always be: THE VALORISIMO VIEW
- HEADLINE should hook the reader (use a question or bold claim)
- SUBLINE expands slightly on the headline can be spicy 
- No extra lines, no explanation, no markdown

Article:
{text}
"""
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# -- MAIN ---------------------------------------------------------------------

def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Fetching: {TARGET_URL}")
    soup = fetch_page(TARGET_URL)

    # 1. Image
    image_path = os.path.join(OUTPUT_DIR, "image.png")
    if not download_image(soup, TARGET_URL, image_path):
        print("No suitable image found on page.")
        sys.exit(1)

    # 2. Text
    text = extract_text(soup, max_paragraphs=5)
    if not text.strip():
        print("No usable text found on page.")
        sys.exit(1)
    print(f"  Extracted {len(text)} chars of text.")

    # 3. Summarise
    print("  Calling LLM...")
    summary = summarise(text)
    print(f"\n{summary}\n")

    # 4. Write inpost.txt
    inpost_path = os.path.join(OUTPUT_DIR, "inpost.txt")
    with open(inpost_path, "w", encoding="utf-8") as f:
        f.write(summary + "\n")
    print(f"  inpost.txt saved -> {inpost_path}")

if __name__ == "__main__":
    run()
