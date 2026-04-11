#!/usr/bin/env python3
"""
download-general-content.py — Download general knowledge content for Jarvis archive.
Fetches Wikipedia articles on pop culture, science, history, sports, and more.
Usage: download-general-content.py [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "general")

TOPICS = {
    "movies": [
        "Film",
        "History of film",
        "Academy Awards",
        "Film genre",
        "Action film",
        "Comedy film",
        "Drama (film and television)",
        "Science fiction film",
        "Horror film",
        "Documentary film",
        "Animation",
        "Streaming service",
        "Box office",
        "Film director",
        "Cinematography",
    ],
    "music": [
        "Music genre",
        "Rock music",
        "Pop music",
        "Hip hop music",
        "Country music",
        "Jazz",
        "Blues",
        "Classical music",
        "Electronic music",
        "Rhythm and blues",
        "Music theory",
        "Musical instrument",
        "Music streaming",
        "Record label",
        "Music video",
    ],
    "tv": [
        "Television show",
        "Streaming television",
        "Reality television",
        "Situation comedy",
        "Drama series",
        "Animated series",
        "Television network",
        "Podcast",
        "YouTube",
        "Social media",
    ],
    "sports": [
        "American football",
        "National Football League",
        "Basketball",
        "National Basketball Association",
        "Baseball",
        "Major League Baseball",
        "Ice hockey",
        "National Hockey League",
        "Association football",
        "Major League Soccer",
        "Tennis",
        "Golf",
        "Mixed martial arts",
        "Olympic Games",
        "NASCAR",
        "Boxing",
        "Track and field",
        "Swimming (sport)",
    ],
    "science": [
        "Science",
        "Physics",
        "Chemistry",
        "Biology",
        "Astronomy",
        "Solar System",
        "Planet",
        "Black hole",
        "Human body",
        "DNA",
        "Evolution",
        "Climate",
        "Geology",
        "Mathematics",
        "Technology",
        "Artificial intelligence",
        "Internet",
        "Electricity",
        "Atom",
        "Periodic table",
    ],
    "history": [
        "History of the United States",
        "American Revolution",
        "American Civil War",
        "World War I",
        "World War II",
        "Cold War",
        "Space Race",
        "Industrial Revolution",
        "Ancient Rome",
        "Ancient Egypt",
        "Middle Ages",
        "Renaissance",
        "French Revolution",
        "Civil rights movement",
        "September 11 attacks",
    ],
    "cooking": [
        "Cooking",
        "Recipe",
        "Baking",
        "Grilling",
        "Nutrition",
        "Protein",
        "Vitamin",
        "Carbohydrate",
        "Fat",
        "Calorie",
        "Vegetarian cuisine",
        "Meat",
        "Seafood",
        "Vegetable",
        "Fruit",
        "Bread",
        "Pasta",
        "Rice",
        "Soup",
        "Dessert",
    ],
    "geography": [
        "United States",
        "Canada",
        "Mexico",
        "Europe",
        "Asia",
        "Africa",
        "South America",
        "Australia",
        "World ocean",
        "Mountain range",
        "River",
        "Desert",
        "Rainforest",
        "Capital city",
        "Time zone",
    ],
    "health": [
        "Health",
        "Exercise",
        "Sleep",
        "Mental health",
        "Stress (biology)",
        "Immune system",
        "Heart",
        "Lungs",
        "Digestive system",
        "Diabetes",
        "Hypertension",
        "Influenza",
        "Vaccine",
        "First aid",
        "Meditation",
    ],
    "everyday": [
        "Personal finance",
        "Budgeting",
        "Credit card",
        "Mortgage loan",
        "Renting",
        "Home repair",
        "Automobile",
        "Car maintenance",
        "Insurance",
        "Taxes",
        "Job interview",
        "Resume",
        "Parenting",
        "Pet",
        "Gardening",
    ],
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=5000):
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
        print(f"    warn: {title}: {e}")
        return None


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force = "--force" in sys.argv

    if target == "all":
        categories = list(TOPICS.keys())
    elif target in TOPICS:
        categories = [target]
    else:
        print(f"Unknown category: {target}")
        print(f"Available: {', '.join(TOPICS.keys())}, all")
        sys.exit(1)

    total = 0
    for category in categories:
        out_dir = os.path.join(OUTPUT_DIR, category)
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n[{category.upper()}] {len(TOPICS[category])} topics")

        for title in TOPICS[category]:
            slug = slugify(title)
            out_path = os.path.join(out_dir, f"{slug}.md")

            if os.path.exists(out_path) and not force:
                print(f"  skip: {title}")
                continue

            print(f"  fetching: {title}...")
            text = wiki_fetch(title)
            if text:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n{text}\n")
                total += 1
            else:
                print(f"  not found: {title}")
            time.sleep(0.5)

    print(f"\nDone. {total} files downloaded.")
    if total > 0:
        print("Run 'Jarvis rebuild-index' to update semantic search.")


if __name__ == "__main__":
    main()
