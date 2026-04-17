#!/usr/bin/env python3
"""
download-survival.py — Download wilderness survival, bushcraft, navigation,
                        trapping, foraging, hunting, and emergency preparedness content.

Run: Jarvis download-survival [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "survival")

TOPICS = {
    "wilderness-survival": [
        "Wilderness survival",
        "Survival skills",
        "Survival kit",
        "Bug-out bag",
        "Shelter (building)",
        "Debris hut",
        "Lean-to",
        "Emergency bivouac",
        "Hypothermia",
        "Hyperthermia",
        "Frostbite",
        "Trench foot",
        "Dehydration",
        "Water purification",
        "Boiling",
        "Water filtration",
        "Solar still",
        "Dew collection",
        "Fire making",
        "Friction fire",
        "Bow drill",
        "Hand drill",
        "Flint and steel",
        "Tinder (fire starting)",
        "Fire triangle",
        "Signal fire",
        "Survival signaling",
        "Signal mirror",
        "Whistle",
        "Rule of threes (survival)",
        "SOS",
        "Emergency position-indicating radiobeacon station",
        "Personal locator beacon",
    ],
    "navigation": [
        "Navigation",
        "Dead reckoning",
        "Celestial navigation",
        "Orienteering",
        "Compass",
        "Magnetic declination",
        "Topographic map",
        "Contour line",
        "Map reading",
        "True north",
        "Magnetic north",
        "North Star",
        "Ursa Minor",
        "Sun compass",
        "Stick shadow method",
        "Pace counting",
        "Triangulation",
        "Resection (orientation)",
        "Land navigation",
        "Terrain association",
        "Trail blazing",
        "Landmark navigation",
        "Global Positioning System",
        "Coordinate system",
        "Latitude",
        "Longitude",
        "UTM coordinate system",
        "Survival trail",
    ],
    "foraging": [
        "Foraging",
        "Edible plant",
        "Wild food",
        "Wildcraft",
        "Dandelion",
        "Cattail",
        "Wild garlic",
        "Purslane",
        "Lamb's quarters",
        "Wood sorrel",
        "Stinging nettle",
        "Clover",
        "Plantain (plant)",
        "Elderberry",
        "Serviceberry",
        "Wild strawberry",
        "Rosehip",
        "Pine nut",
        "Acorn",
        "Hickory nut",
        "Black walnut",
        "Morel mushroom",
        "Chanterelle",
        "Chicken of the woods",
        "Hen of the woods",
        "Puffball (fungus)",
        "Mushroom poisoning",
        "Amanita phalloides",
        "Wild ginger",
        "Yarrow",
        "St. John's wort",
        "Fireweed",
        "Spruce tips",
        "Seaweed",
    ],
    "trapping-hunting": [
        "Trapping",
        "Animal trapping",
        "Snare (device)",
        "Deadfall trap",
        "Pit trap",
        "Spring snare",
        "Wire snare",
        "Foothold trap",
        "Conibear trap",
        "Skinning",
        "Field dressing",
        "Game (hunting)",
        "Hunting",
        "Bow hunting",
        "Rifle hunting",
        "Subsistence hunting",
        "Tracking (hunting)",
        "Animal track",
        "Scat",
        "Deer hunting",
        "Rabbit hunting",
        "Squirrel hunting",
        "Waterfowl hunting",
        "Grouse",
        "Ptarmigan",
        "Moose",
        "Caribou",
        "Brown bear",
        "Black bear",
        "Fishing",
        "Ice fishing",
        "Fish trap",
        "Gigging",
        "Spearfishing",
    ],
    "emergency-preparedness": [
        "Emergency management",
        "Emergency preparedness",
        "Disaster kit",
        "FEMA",
        "Shelter in place",
        "Evacuation",
        "Emergency food storage",
        "Water storage",
        "Power outage",
        "Generator",
        "Solar panel",
        "Portable battery",
        "Faraday cage",
        "Electromagnetic pulse",
        "Nuclear fallout",
        "Fallout shelter",
        "Civil defense",
        "Pandemic preparedness",
        "Natural disaster",
        "Earthquake preparedness",
        "Hurricane preparedness",
        "Tornado preparedness",
        "Wildfire",
        "Flood",
        "Avalanche",
        "Winter storm",
        "Blizzard",
        "Ice storm",
        "Community emergency response team",
        "Red Cross",
        "CERT (preparedness)",
    ],
    "alaska-wilderness": [
        "Alaska",
        "Interior Alaska",
        "Bush Alaska",
        "Alaska Range",
        "Denali",
        "Brooks Range",
        "Arctic National Wildlife Refuge",
        "Kenai Peninsula",
        "Kodiak Island",
        "Permafrost",
        "Tundra",
        "Taiga",
        "Boreal forest",
        "Midnight sun",
        "Polar night",
        "Aurora borealis",
        "Iditarod Trail Sled Dog Race",
        "Yukon Quest",
        "Dog mushing",
        "Snowmobile",
        "Snow machine",
        "Bush plane",
        "Float plane",
        "Glacier travel",
        "Crevasse",
        "River crossing",
        "Spring breakup",
        "Ice road",
        "Subsistence lifestyle",
        "Alaska Native",
        "Inuit",
        "Athabascan peoples",
        "Yupik people",
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
