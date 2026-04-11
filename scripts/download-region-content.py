#!/usr/bin/env python3
"""
download-region-content.py — Download Wikipedia content for US states and Canadian provinces/territories.
Saves to jarvis/notes/regions/ as markdown for offline use by Jarvis.

Usage:
  python3 download-region-content.py all       # all states + provinces
  python3 download-region-content.py states    # US states only
  python3 download-region-content.py canada    # Canadian provinces/territories only
  python3 download-region-content.py "Alaska"  # single region by name
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]

CANADIAN = [
    "Alberta", "British Columbia", "Manitoba", "New Brunswick",
    "Newfoundland and Labrador", "Northwest Territories", "Nova Scotia",
    "Nunavut", "Ontario", "Prince Edward Island", "Quebec",
    "Saskatchewan", "Yukon",
]

# Additional focused Wikipedia articles per region type
STATE_EXTRA_ARTICLES = [
    "{name} geography",
    "Climate of {name}",
    "Wildlife of {name}",
    "Flora of {name}",
    "Natural disasters in {name}",
]

PROVINCE_EXTRA_ARTICLES = [
    "Geography of {name}",
    "Wildlife of {name}",
    "Climate of {name}",
    "Flora of {name}",
]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=7000):
    """Fetch plain-text extract from Wikipedia. Returns None on failure."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "format": "json",
        "redirects": "1",
        "exchars": str(max_chars),
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        if page.get("pageid", -1) == -1:
            return None
        text = page.get("extract", "").strip()
        return text if len(text) > 150 else None
    except Exception as e:
        print(f"    warn: could not fetch '{title}': {e}")
        return None


def build_region_doc(name, extra_templates, is_priority=False):
    """Download main article + extras, return combined markdown string."""
    sections = []

    print(f"  [{name}] main article...", flush=True)
    main_text = wiki_fetch(name, max_chars=8000 if is_priority else 6000)
    if main_text:
        sections.append(f"# {name}\n\n{main_text}")
    else:
        sections.append(f"# {name}\n\n(No Wikipedia article found.)")
    time.sleep(0.8)

    for template in extra_templates:
        article_title = template.format(name=name)
        print(f"  [{name}] {article_title}...", flush=True)
        text = wiki_fetch(article_title, max_chars=4000)
        if text:
            sections.append(f"\n\n---\n\n## {article_title}\n\n{text}")
        time.sleep(0.8)

    return "\n".join(sections)


def download_region(name, output_dir, extra_templates, is_priority=False, force=False):
    slug = slugify(name)
    out_path = os.path.join(output_dir, f"{slug}.md")

    if os.path.exists(out_path) and not force:
        size_kb = os.path.getsize(out_path) // 1024
        print(f"  skip (exists, {size_kb}KB): {name}")
        return False

    content = build_region_doc(name, extra_templates, is_priority)
    os.makedirs(output_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = len(content) // 1024
    print(f"  saved ({size_kb}KB): {out_path}", flush=True)
    return True


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force = "--force" in sys.argv

    states_dir = os.path.join(BASE_DIR, "notes", "regions", "states")
    provinces_dir = os.path.join(BASE_DIR, "notes", "regions", "provinces")

    # Single region by name
    if target not in ("all", "states", "canada"):
        name = target
        if name in US_STATES:
            download_region(name, states_dir, STATE_EXTRA_ARTICLES, is_priority=True, force=force)
        elif name in CANADIAN:
            download_region(name, provinces_dir, PROVINCE_EXTRA_ARTICLES, is_priority=True, force=force)
        else:
            print(f"Unknown region: {name}")
            print("Try: all, states, canada, or a specific state/province name in quotes.")
            sys.exit(1)
        print("\nDone. Run 'Jarvis rebuild-index' to update semantic search.")
        return

    downloaded = 0

    if target in ("all", "states"):
        print(f"\nDownloading {len(US_STATES)} US states...")
        os.makedirs(states_dir, exist_ok=True)
        for state in US_STATES:
            result = download_region(
                state,
                states_dir,
                STATE_EXTRA_ARTICLES,
                is_priority=True,
                force=force,
            )
            if result:
                downloaded += 1

    if target in ("all", "canada"):
        print(f"\nDownloading {len(CANADIAN)} Canadian provinces/territories...")
        os.makedirs(provinces_dir, exist_ok=True)
        for province in CANADIAN:
            result = download_region(
                province,
                provinces_dir,
                PROVINCE_EXTRA_ARTICLES,
                is_priority=False,
                force=force,
            )
            if result:
                downloaded += 1

    print(f"\nComplete. {downloaded} new files downloaded.")
    if downloaded > 0:
        print("Run 'Jarvis rebuild-index' to update semantic search with new content.")


if __name__ == "__main__":
    main()
