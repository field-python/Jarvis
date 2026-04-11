#!/usr/bin/env python3
"""recipe.py — search, view, add, and get recipe suggestions from Jarvis"""
import sys
import os
import readline
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
recipes_dir     = base_dir / "notes" / "recipes"

now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

CATEGORIES = {
    "depression-era": "Depression Era",
    "survival":       "Survival & Emergency",
    "wilderness":     "Wilderness & Foraging",
    "preservation":   "Food Preservation",
    "homestead":      "Homestead & Farm",
    "north-american": "North American Classics",
    "wild-game":      "Wild Game",
    "breakfast":      "Breakfast",
    "soups":          "Soups & Stews",
    "bread":          "Breads",
    "camp-cooking":   "Camp Cooking",
    "comfort-food":   "Comfort Food",
    "gourmet":        "Gourmet",
}


def all_recipe_files():
    return sorted(recipes_dir.rglob("*.md"))


def get_category(filepath):
    for part in filepath.parts:
        if part in CATEGORIES:
            return part
    return "other"


def display_recipe(filepath):
    text = filepath.read_text(encoding="utf-8")
    cat  = get_category(filepath)
    label = CATEGORIES.get(cat, cat.title())
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Recipe  |  {label}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(text.strip())
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def list_recipes(category_filter=None):
    files = all_recipe_files()
    if category_filter:
        files = [f for f in files if get_category(f) == category_filter]

    if not files:
        if category_filter:
            print(f"No recipes found in category: {category_filter}")
            print(f"Available: {', '.join(CATEGORIES.keys())}")
        else:
            print("No recipes saved yet.")
        return

    # Group by category
    grouped = {}
    for f in files:
        cat = get_category(f)
        grouped.setdefault(cat, []).append(f)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Jarvis Recipes")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for cat, cat_files in grouped.items():
        label = CATEGORIES.get(cat, cat.title())
        print(f"\n  [{label}]")
        for f in cat_files:
            # Get the title from first line of file
            first_line = f.read_text(encoding="utf-8").splitlines()[0]
            title = first_line.lstrip("#").strip()
            print(f"    {title}")

    print()
    total = len(files)
    print(f"  {total} recipe{'s' if total != 1 else ''} total")
    print()
    print("  Jarvis recipe \"search term\"   — find a recipe")
    print("  Jarvis recipe add             — add your own")
    print("  Jarvis recipe suggest \"...\"   — suggest from ingredients")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def search_recipes(query):
    query_lower = query.lower()
    words       = query_lower.split()
    matches     = []

    for f in all_recipe_files():
        text = f.read_text(encoding="utf-8").lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            first_line = f.read_text(encoding="utf-8").splitlines()[0]
            title = first_line.lstrip("#").strip()
            matches.append((score, title, f))

    matches.sort(reverse=True, key=lambda x: x[0])

    if not matches:
        print(f"\n  No recipes found matching '{query}'.")
        print("  Try: Jarvis recipe list")
        return

    if len(matches) == 1:
        display_recipe(matches[0][2])
        return

    # Multiple matches — show top result if it's clearly best, otherwise list all
    if matches[0][0] > matches[1][0] * 2:
        display_recipe(matches[0][2])
        return

    # Show list of matches
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Recipes matching '{query}':")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for _, title, filepath in matches[:8]:
        cat   = get_category(filepath)
        label = CATEGORIES.get(cat, cat.title())
        print(f"  [{label}] {title}")
    print()
    print(f"  Be more specific to view a single recipe.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def add_recipe():
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Add Recipe")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("  Categories:")
    for key, label in CATEGORIES.items():
        print(f"    {key} — {label}")
    print()

    try:
        cat = input("  Category: ").strip().lower()
        if cat not in CATEGORIES:
            cat = "homestead"
        name = input("  Recipe name: ").strip()
        if not name:
            print("  Cancelled.")
            return
    except (KeyboardInterrupt, EOFError):
        print("\n  Cancelled.")
        return

    slug     = name.lower().replace(" ", "-").replace("/", "-")
    save_dir = recipes_dir / cat
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / f"{slug}.md"

    template = (
        f"# {name}\n\n"
        f"**Category:** {cat}\n"
        f"**Serves:** \n"
        f"**Cook Time:** \n"
        f"**Difficulty:** \n\n"
        f"## Description\n\n\n"
        f"## Ingredients\n- \n\n"
        f"## Instructions\n1. \n\n"
        f"## Notes\n\n"
    )

    filepath.write_text(template, encoding="utf-8")

    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(filepath)])
    print(f"\n  Recipe saved: {filepath.name}")


def suggest_recipe(ingredients):
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Recipe Suggestion")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # Check if any saved recipes match the ingredients
    archive_recipes = ""
    words = ingredients.lower().split()
    matches = []
    for f in all_recipe_files():
        text  = f.read_text(encoding="utf-8").lower()
        score = sum(1 for w in words if w in text)
        if score >= 2:
            first_line = f.read_text(encoding="utf-8").splitlines()[0]
            title = first_line.lstrip("#").strip()
            matches.append((score, title))
    matches.sort(reverse=True)
    if matches:
        archive_recipes = "Recipes already in the archive that may use these ingredients:\n"
        for _, title in matches[:5]:
            archive_recipes += f"- {title}\n"

    prompt = (
        f"You are Jarvis, a practical cooking assistant. Today is {current_date}.\n\n"
        f"The user has these ingredients available: {ingredients}\n\n"
        f"Suggest 2-3 practical meals or dishes they can make right now. "
        f"For each suggestion, give:\n"
        f"- Name of the dish\n"
        f"- Why it works with these ingredients\n"
        f"- Any critical missing ingredient (if any)\n"
        f"- One key cooking tip\n\n"
        f"Prioritize simple, filling meals. Think Depression-era practicality — "
        f"stretch ingredients, waste nothing, feed people.\n\n"
        f"{archive_recipes}"
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-recipe-", delete=False
    )
    tmp.write(prompt)
    tmp.close()

    subprocess.run([sys.executable, generate_script, model, host, tmp.name])
    os.unlink(tmp.name)
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def browse_interactive(category_filter=None):
    """Show recipe list then let the user search/view without going back to menu."""
    while True:
        os.system("clear")
        list_recipes(category_filter)
        print()
        print("  ────────────────────────────────────────")
        try:
            query = input("  Search recipes (or Enter to exit): ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not query:
            return

        os.system("clear")
        search_recipes(query)
        print()
        try:
            input("  Press Enter to go back to the list...")
        except (EOFError, KeyboardInterrupt):
            return


# ── main ──────────────────────────────────────────────────────────────────────
arg = sys.argv[1].lower().strip() if len(sys.argv) > 1 else ""

if not arg or arg == "list":
    browse_interactive()

elif arg in CATEGORIES:
    list_recipes(category_filter=arg)

elif arg == "add":
    add_recipe()

elif arg == "suggest":
    if len(sys.argv) < 3:
        print("Usage: Jarvis recipe suggest \"eggs flour salt\"")
        sys.exit(1)
    suggest_recipe(" ".join(sys.argv[2:]))

else:
    # Treat as a search query
    search_recipes(" ".join(sys.argv[1:]))
