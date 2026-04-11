#!/usr/bin/env python3
"""
download-culture-occult.py — Download 70s rock, occult, NASA, and rocket science content.
Fetches Wikipedia articles. Run: Jarvis download-culture
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated")

TOPICS = {
    "70s-rock-occult": {
        "dir": "culture",
        "pages": [
            "Aleister Crowley",
            "Thelema",
            "Hermetic Order of the Golden Dawn",
            "Ordo Templi Orientis",
            "The Book of the Law",
            "Jack Parsons",
            "Babalon Working",
            "Jimmy Page",
            "Led Zeppelin",
            "Boleskine House",
            "Black Sabbath",
            "Ozzy Osbourne",
            "David Bowie",
            "The Rolling Stones",
            "Sgt. Pepper's Lonely Hearts Club Band",
            "Occultism",
            "Satanism",
            "Church of Satan",
            "Anton LaVey",
            "Heavy metal music",
            "Hard rock",
            "Progressive rock",
            "Rock music in the United States",
            "Rock and roll",
            "Glam rock",
            "Psychedelic rock",
            "Classic rock",
            "1970s in music",
        ],
    },
    "nasa-rocketry": {
        "dir": "science",
        "pages": [
            "NASA",
            "Jet Propulsion Laboratory",
            "Jack Parsons",
            "Wernher von Braun",
            "Robert H. Goddard",
            "Saturn V",
            "Apollo program",
            "Project Mercury",
            "Project Gemini",
            "Space Shuttle",
            "V-2 rocket",
            "Solid-propellant rocket",
            "Liquid-propellant rocket",
            "Operation Paperclip",
            "Space Race",
            "International Space Station",
            "SpaceX",
            "Falcon 9",
            "Rocket engine",
            "Spacecraft propulsion",
            "Orbital mechanics",
            "Konstantin Tsiolkovsky",
            "Hermann Oberth",
            "Frank Malina",
            "JATO",
            "GALCIT",
            "Caltech",
        ],
    },
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=6000):
    params = urllib.parse.urlencode({
        "action":         "query",
        "titles":         title,
        "prop":           "extracts",
        "explaintext":    "1",
        "exsectionformat":"plain",
        "format":         "json",
        "redirects":      "1",
        "exchars":        str(max_chars),
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data  = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        if page.get("pageid", -1) == -1:
            return None
        text = page.get("extract", "").strip()
        return text if len(text) > 150 else None
    except Exception as e:
        print(f"    warn: {title}: {e}")
        return None


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force  = "--force" in sys.argv

    if target == "all":
        cats = list(TOPICS.keys())
    elif target in TOPICS:
        cats = [target]
    else:
        print(f"Unknown category: {target}")
        print(f"Available: {', '.join(TOPICS.keys())}, all")
        sys.exit(1)

    total = 0
    for cat in cats:
        info    = TOPICS[cat]
        out_dir = os.path.join(OUTPUT_DIR, info["dir"], cat)
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n[{cat.upper()}]  {len(info['pages'])} topics  →  {out_dir}")

        for title in info["pages"]:
            slug     = slugify(title)
            out_path = os.path.join(out_dir, f"{slug}.md")

            if os.path.exists(out_path) and not force:
                print(f"  skip  {title}")
                continue

            print(f"  fetch {title}...", end=" ", flush=True)
            text = wiki_fetch(title)
            if not text:
                print("not found")
                continue

            header = f"# {title}\n\n*Source: Wikipedia*\n\n"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(header + text + "\n")
            print(f"ok ({len(text):,} chars)")
            total += 1
            time.sleep(0.3)

    print(f"\nDone — {total} articles downloaded.")
    print("Run 'Jarvis rebuild-index' to make them searchable.")


if __name__ == "__main__":
    main()
