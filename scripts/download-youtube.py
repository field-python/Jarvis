#!/usr/bin/env python3
"""
download-youtube.py — Download YouTube culture, creators, and internet personalities.
Run: Jarvis download-youtube [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "youtube")

TOPICS = {
    "platform": [
        "YouTube",
        "YouTuber",
        "History of YouTube",
        "YouTube Premium",
        "YouTube Shorts",
        "YouTube Music",
        "YouTube Kids",
        "YouTube Live",
        "Vlog",
        "Let's Play (video gaming)",
        "Reaction video",
        "Unboxing video",
        "Haul video",
        "ASMR",
        "Content creator",
        "Influencer marketing",
        "Viral video",
        "Streaming media",
        "Twitch (service)",
        "Podcast",
    ],
    "creators-gaming": [
        "PewDiePie",
        "Markiplier",
        "Jacksepticeye",
        "Dream (YouTuber)",
        "Ninja (streamer)",
        "Pokimane",
        "Valkyrae",
        "Ludwig Ahgren",
        "TommyInnit",
        "Technoblade",
        "Sidemen",
        "Dude Perfect",
        "Vanoss Gaming",
        "Smosh",
    ],
    "creators-entertainment": [
        "MrBeast",
        "Logan Paul",
        "Jake Paul",
        "KSI",
        "David Dobrik",
        "Shane Dawson",
        "Jenna Mourey",
        "Trisha Paytas",
        "Tana Mongeau",
        "Nikocado Avocado",
        "Casey Neistat",
        "Ryan Higa",
        "Rhett and Link",
        "Lilly Singh",
        "James Charles",
        "Jeffree Star",
        "Charli D'Amelio",
        "Addison Rae",
        "Sneako",
        "Andrew Tate",
    ],
    "creators-education": [
        "Vsauce",
        "CGP Grey",
        "Kurzgesagt",
        "Veritasium",
        "SmarterEveryDay",
        "Mark Rober",
        "Wendover Productions",
        "Tom Scott",
        "NileRed",
        "Linus Tech Tips",
        "Marques Brownlee",
        "Unbox Therapy",
        "Primitive Technology",
        "Babish Culinary Universe",
        "Good Mythical Morning",
        "CrashCourse",
        "TED (conference)",
        "Khan Academy",
        "Numberphile",
        "3Blue1Brown",
    ],
    "creators-commentary": [
        "H3H3Productions",
        "Philip DeFranco",
        "iDubbbzTV",
        "Keemstar",
        "HasanAbi",
        "Steven Crowder",
        "Tim Pool",
        "Jordan Peterson",
        "Joe Rogan",
        "Destiny (political commentator)",
        "Charlie Kirk",
        "Ben Shapiro",
        "Candace Owens",
        "Vaush",
        "ContraPoints",
        "Natalie Wynn",
    ],
    "controversies": [
        "Elsagate",
        "YouTube Rewind",
        "Adpocalypse",
        "PewDiePie vs T-Series",
        "Deplatforming",
        "Cancel culture",
        "YouTube ban",
        "Logan Paul Aokigahara forest controversy",
        "Dream (YouTuber) speedrunning controversy",
        "Faze Clan",
        "Boxing event on YouTube",
        "Creator economy",
    ],
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=5000):
    params = urllib.parse.urlencode({
        "action":          "query",
        "titles":          title,
        "prop":            "extracts",
        "explaintext":     "1",
        "exsectionformat": "plain",
        "format":          "json",
        "redirects":       "1",
        "exchars":         str(max_chars),
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

    grand_total = 0
    for cat in cats:
        out_dir = os.path.join(OUTPUT_DIR, cat)
        os.makedirs(out_dir, exist_ok=True)
        pages = TOPICS[cat]
        print(f"\n[{cat.upper()}]  {len(pages)} topics  →  {out_dir}")

        for title in pages:
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

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Source: Wikipedia*\n\n{text}\n")
            print(f"ok ({len(text):,} chars)")
            grand_total += 1
            time.sleep(0.3)

    print(f"\nDone — {grand_total} articles downloaded.")
    print("Run 'Jarvis rebuild-index' to make them searchable.")


if __name__ == "__main__":
    main()
