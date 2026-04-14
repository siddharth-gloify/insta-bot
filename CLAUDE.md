# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the post generator (uses defaults: inpost.txt, image.png, logo.png → post.png)
venv/Scripts/python.exe make_post.py

# Override any input/output file
venv/Scripts/python.exe make_post.py --text inpost.txt --image image.png --logo logo.png --out post.png
```

## Architecture

This is a single-file script (`make_post.py`) that generates a 1080×1080 Instagram post image using Pillow.

**Pipeline**: `inpost.txt` + `image.png` + `logo.png` → `post.png`

1. Parses `inpost.txt` for three fields: `TAG`, `HEADLINE`, `SUBLINE`
2. Builds a canvas with a solid `BRAND_BLUE` background
3. Pastes the photo into the bottom ~48% of the canvas (cropped/scaled to fill width)
4. Overlays a gold pill badge (TAG), a logo (top-right, respects PNG alpha), headline text, and subline text
5. Saves the result as PNG

**Font loading** (`load_font`): tries `fonts/` subfolder first (drop `.ttf` files there for custom fonts), then falls back to system fonts on Windows/macOS/Linux. Poppins is preferred; Arial/Liberation Sans are fallbacks.

**Key constants** (all at the top of `make_post.py`): `CANVAS_SIZE`, `BRAND_BLUE`, `TAG_BG_COLOR`, `PHOTO_SPLIT`, `PADDING`, `LOGO_MAX_W` — edit these to restyle the layout.

## Custom Fonts

Place `.ttf` files in a `fonts/` subdirectory next to `make_post.py`. Expected names: `Poppins-Bold.ttf`, `Poppins-Medium.ttf`, `Poppins-Regular.ttf` (or `Inter-*` equivalents). Free download: https://fonts.google.com/specimen/Poppins
