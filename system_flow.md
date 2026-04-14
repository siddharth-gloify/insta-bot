# System Flow

```mermaid
flowchart TD
    URL["TARGET_URL\n(hardcoded in extractor.py)"]

    subgraph STEP1["STEP 1 — scraping/extractor.py"]
        FETCH["Fetch page\nrequests + BeautifulSoup"]
        IMG["Download first\nusable image\nPillow → PNG"]
        TEXT["Extract top 5\nparagraphs"]
        LLM["Claude Sonnet 4.6\nvia OpenRouter\nGenerate TAG / HEADLINE / SUBLINE"]
    end

    subgraph NEW["new_assets/  (gitignored)"]
        IMGOUT["image.png"]
        INPOST["inpost.txt"]
    end

    subgraph STATIC["assets/  (tracked in git)"]
        LOGO["logo.png"]
    end

    subgraph STEP2["STEP 2 — make_post.py"]
        CANVAS["1080x1080 canvas\nBrand blue background"]
        COMPOSE["Compose layers\n① photo (bottom 48%)\n② tag pill\n③ logo\n④ headline\n⑤ subline"]
    end

    subgraph OUT["output/  (gitignored)"]
        POST["post.png"]
    end

    ENV[".env\nOPENROUTER_API_KEY"]

    URL --> FETCH
    FETCH --> IMG --> IMGOUT
    FETCH --> TEXT --> LLM
    ENV --> LLM
    LLM --> INPOST

    IMGOUT --> COMPOSE
    INPOST --> COMPOSE
    LOGO  --> COMPOSE
    CANVAS --> COMPOSE
    COMPOSE --> POST
```

## Entry point

```
python main.py
```

calls `extractor.run()` → then `make_post()` in sequence.

## Data flow summary

| Stage | Input | Output |
|---|---|---|
| Scrape | `TARGET_URL` | `new_assets/image.png` |
| Summarise | page paragraphs + LLM | `new_assets/inpost.txt` |
| Compose | image + inpost + logo | `output/post.png` |
