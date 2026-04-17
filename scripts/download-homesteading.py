#!/usr/bin/env python3
"""
download-homesteading.py — Download homesteading, farming, animal husbandry,
                            gardening, and off-grid living content.

Run: Jarvis download-homesteading [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "homesteading")

TOPICS = {
    "farming-basics": [
        "Subsistence agriculture",
        "Homesteading (United States)",
        "Market garden",
        "Raised-bed gardening",
        "Crop rotation",
        "Companion planting",
        "Cover crop",
        "Green manure",
        "Soil health",
        "Composting",
        "Vermicomposting",
        "Mulching",
        "Irrigation",
        "Drip irrigation",
        "Rainwater harvesting",
        "Permaculture",
        "No-dig gardening",
        "Hügelkultur",
        "Biodynamic agriculture",
        "Organic farming",
        "Seed saving",
        "Heirloom plant",
        "Open-pollinated",
        "Grafting",
        "Plant propagation",
        "Cold frame",
        "Greenhouse",
        "Season extension",
        "Row cover",
        "Frost date",
        "Growing season",
        "USDA hardiness zone",
    ],
    "animal-husbandry": [
        "Animal husbandry",
        "Livestock",
        "Chicken",
        "Chicken coop",
        "Egg production",
        "Broiler",
        "Laying hen",
        "Goat",
        "Dairy goat",
        "Milk",
        "Milking",
        "Pig",
        "Pig farming",
        "Cattle",
        "Beef cattle",
        "Dairy cattle",
        "Sheep",
        "Wool",
        "Shearing",
        "Rabbit",
        "Rabbit farming",
        "Duck",
        "Geese",
        "Turkey (bird)",
        "Beekeeping",
        "Honeybee",
        "Honey",
        "Beeswax",
        "Farriery",
        "Veterinary medicine",
        "Pasture management",
        "Rotational grazing",
        "Fodder",
        "Hay",
        "Silage",
    ],
    "gardening": [
        "Vegetable garden",
        "Potato",
        "Carrot",
        "Cabbage",
        "Broccoli",
        "Onion",
        "Garlic",
        "Tomato",
        "Squash (plant)",
        "Zucchini",
        "Pumpkin",
        "Corn",
        "Bean",
        "Pea",
        "Lettuce",
        "Spinach",
        "Kale",
        "Swiss chard",
        "Radish",
        "Turnip",
        "Beet",
        "Parsnip",
        "Leek",
        "Herbs",
        "Basil",
        "Parsley",
        "Thyme",
        "Rosemary",
        "Mint",
        "Dill",
        "Cilantro",
        "Fruit tree",
        "Apple",
        "Blueberry",
    ],
    "off-grid-systems": [
        "Off-the-grid",
        "Solar power",
        "Photovoltaic system",
        "Wind power",
        "Small wind turbine",
        "Micro-hydropower",
        "Battery storage",
        "Lead–acid battery",
        "Lithium-ion battery",
        "Inverter (electrical)",
        "Charge controller",
        "Generator",
        "Diesel generator",
        "Propane",
        "Natural gas",
        "Wood stove",
        "Rocket stove",
        "Masonry heater",
        "Passive solar building design",
        "Earthship",
        "Straw bale construction",
        "Cob (material)",
        "Adobe",
        "Log cabin",
        "Tiny house movement",
        "Container house",
        "Composting toilet",
        "Greywater",
        "Septic tank",
        "Well",
        "Water well",
        "Hand pump",
        "Gravity-fed water system",
    ],
    "tools-crafts": [
        "Hand tool",
        "Axe",
        "Splitting maul",
        "Chainsaw",
        "Crosscut saw",
        "Drawknife",
        "Froe",
        "Adze",
        "Chisel",
        "Plane (tool)",
        "Blacksmithing",
        "Forge",
        "Anvil",
        "Welding",
        "Leatherworking",
        "Tanning",
        "Spinning (textiles)",
        "Weaving",
        "Knitting",
        "Sewing",
        "Mending",
        "Candle making",
        "Soap making",
        "Lye",
        "Rope making",
        "Basket weaving",
        "Pottery",
        "Woodworking",
        "Timber framing",
        "Cordwood construction",
        "Dovetail joint",
        "Mortise and tenon",
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
