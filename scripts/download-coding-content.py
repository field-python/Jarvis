#!/usr/bin/env python3
"""
download-coding-content.py — Download coding reference content for Jarvis archive.
Fetches Wikipedia articles on programming concepts, languages, and tools.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "coding")

TOPICS = {
    "python": [
        "Python (programming language)",
        "Python syntax and semantics",
        "List comprehension",
        "Python (programming language) library",
        "Exception handling",
        "Object-oriented programming",
        "Function (computer programming)",
        "Variable (computer science)",
        "Data type",
        "String (computer science)",
        "Array data structure",
        "Dictionary (data structure)",
        "Recursion (computer science)",
        "Debugging",
    ],
    "bash": [
        "Bash (Unix shell)",
        "Shell script",
        "Unix filesystem",
        "Pipeline (Unix)",
        "Standard streams",
        "Regular expression",
        "Cron",
        "Environment variable",
    ],
    "git": [
        "Git",
        "Version control",
        "Branch (version control)",
        "Merge (version control)",
    ],
    "linux": [
        "Linux",
        "Linux command-line interface",
        "File system permissions",
        "Package manager",
        "Process (computing)",
        "Secure Shell",
        "Text editor",
    ],
    "concepts": [
        "Algorithm",
        "Data structure",
        "Computer program",
        "Source code",
        "Compiler",
        "Interpreted language",
        "Application programming interface",
        "Library (computing)",
        "Software bug",
        "Comment (computer programming)",
        "Conditional (computer programming)",
        "For loop",
        "While loop",
        "Boolean data type",
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

    categories = TOPICS.keys() if target == "all" else [target]

    total = 0
    for category in categories:
        if category not in TOPICS:
            print(f"Unknown category: {category}")
            print(f"Available: {', '.join(TOPICS.keys())}, all")
            continue

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
            time.sleep(0.6)

    print(f"\nDone. {total} files downloaded.")
    if total > 0:
        print("Run 'Jarvis rebuild-index' to update semantic search.")


if __name__ == "__main__":
    main()
