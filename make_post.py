"""
make_post.py — Instagram Post Generator
========================================
Reads inpost.txt, image.png, logo.png
Outputs post.png (1080x1080)

inpost.txt format:
------------------
TAG: THE VALORISIMO VIEW
HEADLINE: Will a Ceasefire Boost Dubai Real Estate?
SUBLINE: Ceasefire Impact — Will Dubai Real Estate Rebound Instantly?

Usage:
    python make_post.py

Optional — override input files:
    python make_post.py --text inpost.txt --image image.png --logo logo.png --out post.png
"""

import sys
import os
import argparse
from PIL import Image, ImageDraw, ImageFont

# ── SETTINGS ────────────────────────────────────────────────────────────────

CANVAS_SIZE   = (1080, 1580)
BRAND_BLUE    = (30, 100, 220)       # main background colour
TAG_BG_COLOR  = (180, 140, 60)       # gold/bronze pill
TAG_TXT_COLOR = (255, 255, 255)
HEADLINE_COLOR= (255, 255, 255)
SUBLINE_COLOR = (210, 228, 255)      # slightly tinted white

PHOTO_SPLIT   = 0.52                 # photo starts this far down (0–1)
PADDING       = 64                   # left/right margin in px
TAG_RADIUS    = 22                   # pill corner radius
LOGO_MAX_W    = 130                  # logo is resized to fit this width

# Poppins ships with most Linux/Mac systems via google-fonts package.
# If you see a font error, swap these paths for any Bold/Medium/Regular .ttf you have.
def load_font(name, size):
    """
    Load a font by style name ("Bold", "Medium", "Regular").
    Search order:
      1. fonts/ subfolder next to this script  ← easiest way to add custom fonts
      2. Windows system fonts (Arial)
      3. macOS system fonts (Helvetica Neue)
      4. Linux system fonts (Liberation Sans / Poppins)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Local fonts/ folder — drop any .ttf here to use it
    local_map = {
        "Bold":    ["Poppins-Bold.ttf",    "Inter-Bold.ttf",    "ArialBold.ttf"],
        "Medium":  ["Poppins-Medium.ttf",  "Inter-Medium.ttf",  "ArialMedium.ttf"],
        "Regular": ["Poppins-Regular.ttf", "Inter-Regular.ttf", "Arial.ttf"],
    }
    fonts_folder = os.path.join(script_dir, "fonts")
    for filename in local_map.get(name, []):
        path = os.path.join(fonts_folder, filename)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    # 2. Windows — Arial is always present
    windows_map = {
        "Bold":    [r"C:\Windows\Fonts\arialbd.ttf",  r"C:\Windows\Fonts\calibrib.ttf"],
        "Medium":  [r"C:\Windows\Fonts\arialbd.ttf",  r"C:\Windows\Fonts\calibrib.ttf"],
        "Regular": [r"C:\Windows\Fonts\arial.ttf",    r"C:\Windows\Fonts\calibri.ttf"],
    }
    for path in windows_map.get(name, []):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    # 3. macOS
    mac_map = {
        "Bold":    ["/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"],
        "Medium":  ["/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"],
        "Regular": ["/Library/Fonts/Arial.ttf",      "/System/Library/Fonts/Helvetica.ttc"],
    }
    for path in mac_map.get(name, []):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    # 4. Linux
    linux_map = {
        "Bold":    ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
        "Medium":  ["/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
        "Regular": ["/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
    }
    for path in linux_map.get(name, []):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    raise FileNotFoundError(
        f"Could not find a '{name}' font.\n"
        "Fix: create a 'fonts/' folder next to make_post.py and drop Poppins .ttf files in it.\n"
        "Download free: https://fonts.google.com/specimen/Poppins"
    )

# ── TEXT UTILITIES ───────────────────────────────────────────────────────────

def wrap_text(text, font, max_width, draw):
    """Break text into lines that fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_text_block(draw, lines, font, color, x, y, line_spacing=1.2):
    """Draw a list of lines and return the y position after the last line."""
    line_h = font.size * line_spacing
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, font=font, fill=color)
    return y + len(lines) * line_h

# ── PARSE inpost.txt ─────────────────────────────────────────────────────────

def parse_text_file(path):
    """
    Reads TAG, HEADLINE, SUBLINE from inpost.txt.
    Format is flexible: key: value pairs, case-insensitive.
    """
    data = {"tag": "", "headline": "", "subline": ""}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if key in data:
                    data[key] = value
    return data

# ── MAIN ─────────────────────────────────────────────────────────────────────

def make_post(text_file, image_file, logo_file, output_file):
    W, H = CANVAS_SIZE

    # 1. Parse text
    text = parse_text_file(text_file)
    tag_text      = text.get("tag", "").upper()
    headline_text = text.get("headline", "")
    subline_text  = text.get("subline", "")

    # 2. Load fonts
    font_tag      = load_font("Bold",    26)
    font_headline = load_font("Bold",    72)
    font_subline  = load_font("Medium",  36)

    # 3. Create canvas
    canvas = Image.new("RGB", (W, H), BRAND_BLUE)
    draw   = ImageDraw.Draw(canvas)

    # 4. Paste photo into bottom portion
    photo_y = int(H * PHOTO_SPLIT)
    photo_h = H - photo_y

    photo = Image.open(image_file).convert("RGB")
    # Scale photo to fill the width, then crop to height needed
    aspect = photo.width / photo.height
    target_w = W
    target_h = max(photo_h, int(W / aspect))
    photo = photo.resize((target_w, target_h), Image.LANCZOS)
    # Centre-crop vertically
    crop_top = (target_h - photo_h) // 2
    photo = photo.crop((0, crop_top, target_w, crop_top + photo_h))
    canvas.paste(photo, (0, photo_y))

    # 5. Tag pill (top-left)
    tag_pad_x, tag_pad_y = 22, 10
    bbox  = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = bbox[2] - bbox[0] + tag_pad_x * 2
    tag_h = bbox[3] - bbox[1] + tag_pad_y * 2
    tag_x, tag_y = PADDING, PADDING

    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
        radius=TAG_RADIUS, fill=TAG_BG_COLOR
    )
    draw.text(
        (tag_x + tag_pad_x, tag_y + tag_pad_y - bbox[1]),
        tag_text, font=font_tag, fill=TAG_TXT_COLOR
    )

    # 6. Logo (top-right, respects transparency)
    logo = Image.open(logo_file).convert("RGBA")
    # Resize to fit within LOGO_MAX_W
    logo_ratio = LOGO_MAX_W / logo.width
    logo_w = LOGO_MAX_W
    logo_h = int(logo.height * logo_ratio)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    logo_x = W - PADDING - logo_w
    logo_y = PADDING
    canvas.paste(logo, (logo_x, logo_y), mask=logo.split()[3])  # alpha mask

    # 7. Headline
    headline_y  = tag_y + tag_h + 52
    max_text_w  = W - PADDING * 2
    h_lines     = wrap_text(headline_text, font_headline, max_text_w, draw)
    after_headline = draw_text_block(
        draw, h_lines, font_headline, HEADLINE_COLOR, PADDING, headline_y, line_spacing=1.12
    )

    # 8. Subline
    subline_y = after_headline + 36
    s_lines   = wrap_text(subline_text, font_subline, max_text_w, draw)
    draw_text_block(
        draw, s_lines, font_subline, SUBLINE_COLOR, PADDING, subline_y, line_spacing=1.3
    )

    # 9. Save
    canvas = canvas.convert("RGB")
    canvas.save(output_file, "PNG", quality=95)
    print(f"✓ Saved → {output_file}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an Instagram post image.")
    parser.add_argument("--text",  default="inpost.txt",  help="Path to text file")
    parser.add_argument("--image", default="image.png",   help="Path to source photo")
    parser.add_argument("--logo",  default="logo.png",    help="Path to logo PNG")
    parser.add_argument("--out",   default="post.png",    help="Output filename")
    args = parser.parse_args()

    for f, label in [(args.text, "text file"), (args.image, "image"), (args.logo, "logo")]:
        if not os.path.exists(f):
            print(f"✗ Missing {label}: '{f}'")
            sys.exit(1)

    make_post(args.text, args.image, args.logo, args.out)