#!/usr/bin/env python3
"""
download-food-preservation.py — Download food preservation, canning, fermentation,
                                  smoking, drying, and storage content.

Run: Jarvis download-food-preservation [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "food-preservation")

TOPICS = {
    "canning": [
        "Canning",
        "Home canning",
        "Pressure canning",
        "Water bath canning",
        "Mason jar",
        "Ball Corporation (canning)",
        "Botulism",
        "Clostridium botulinum",
        "Food safety",
        "pH",
        "Acidity",
        "Sterilization (microbiology)",
        "Headspace (canning)",
        "Seal (mechanical)",
        "Lid (container)",
        "Pickling",
        "Brine",
        "Vinegar",
        "Salt",
        "Sugar",
        "Jam",
        "Jelly (fruit preserves)",
        "Marmalade",
        "Fruit preserves",
        "Pectin",
        "Tomato canning",
        "Salsa",
        "Chutney",
        "Applesauce",
        "Pressure cooker",
    ],
    "fermentation": [
        "Fermentation in food processing",
        "Lacto-fermentation",
        "Sauerkraut",
        "Kimchi",
        "Kombucha",
        "Kefir",
        "Yogurt",
        "Sourdough bread",
        "Sourdough starter",
        "Miso",
        "Tempeh",
        "Natto",
        "Vinegar",
        "Apple cider vinegar",
        "Fermented fish",
        "Kvass",
        "Tepache",
        "Jun (beverage)",
        "Ginger beer",
        "Water kefir",
        "Fermented vegetables",
        "Probiotics",
        "Gut microbiome",
        "Lactic acid bacteria",
        "Brine fermentation",
        "Wild fermentation",
        "Sandor Katz",
        "Crock (dishware)",
        "Fermentation crock",
        "Anaerobic fermentation",
    ],
    "smoking-curing": [
        "Smoking (cooking)",
        "Cold smoking",
        "Hot smoking",
        "Smoke house",
        "Curing (food preservation)",
        "Salt-curing",
        "Brining",
        "Jerky",
        "Pemmican",
        "Smoked salmon",
        "Lox",
        "Gravlax",
        "Bacon",
        "Ham",
        "Prosciutto",
        "Salami",
        "Sausage",
        "Nitrate",
        "Prague powder",
        "Smoke ring (cooking)",
        "Wood for smoking",
        "Hickory",
        "Apple wood",
        "Mesquite",
        "Alder",
        "Fish smoking",
        "Meat preservation",
        "Sugar-curing",
        "Corned beef",
        "Pastrami",
    ],
    "drying-dehydrating": [
        "Food drying",
        "Dehydration (food)",
        "Food dehydrator",
        "Sun drying",
        "Freeze drying",
        "Lyophilization",
        "Jerky",
        "Dried fruit",
        "Raisins",
        "Prunes",
        "Dried herbs",
        "Powdered milk",
        "Egg powder",
        "Hardtack",
        "Biltong",
        "Dried fish",
        "Stockfish",
        "Lutefisk",
        "Pemmican",
        "Trail mix",
        "Granola",
        "Dried beans",
        "Lentil",
        "Solar dryer",
        "Oven drying",
        "Moisture content",
        "Water activity",
        "Silica gel",
        "Oxygen absorber",
        "Mylar bag",
    ],
    "root-cellaring": [
        "Root cellar",
        "Cold storage",
        "Fruit storage",
        "Vegetable storage",
        "Potato storage",
        "Onion storage",
        "Garlic storage",
        "Apple storage",
        "Winter squash",
        "Turnip",
        "Beet",
        "Carrot storage",
        "Parsnip",
        "Humidity",
        "Temperature",
        "Ethylene",
        "Sprouting",
        "Rotting (food)",
        "Pantry",
        "Dry goods",
        "Food storage container",
        "Grain storage",
        "Flour storage",
        "Rice storage",
        "Long-term food storage",
        "FIFO (computing)",
        "Food rotation",
        "Canned goods shelf life",
        "MRE",
        "Freeze-dried food",
    ],
    "cooking-preservation": [
        "Confit",
        "Rendering (food processing)",
        "Lard",
        "Tallow",
        "Schmaltz",
        "Ghee",
        "Clarified butter",
        "Potted meat",
        "Rillettes",
        "Pâté",
        "Terrines",
        "Wax sealing",
        "Infused oil",
        "Herb vinegar",
        "Herb oil",
        "Pickled eggs",
        "Pickled vegetables",
        "Kimchi jjigae",
        "Fermented hot sauce",
        "Preserved lemon",
        "Salt fish",
        "Salt cod",
        "Corned beef",
        "Bully beef",
        "Potted shrimp",
        "Charcuterie",
        "Cured meat",
        "Dry-aged beef",
        "Wet aging",
        "Maillard reaction",
    ],
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=6000):
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
