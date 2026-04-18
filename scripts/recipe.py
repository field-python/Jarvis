#!/usr/bin/env python3
"""recipe.py — search, view, add, and get recipe suggestions from Jarvis"""
import sys
import os
import readline
import subprocess
import tempfile
import tty
import termios
from pathlib import Path
from datetime import datetime

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def getch():
    import select as _sel
    import os as _os
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = _sel.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", errors="replace")
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

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


def browse_recipes(category_filter=None):
    """Arrow-key recipe browser — select a recipe and view ingredients/directions."""
    files = all_recipe_files()
    if category_filter:
        files = [f for f in files if get_category(f) == category_filter]

    if not files:
        print("No recipes saved yet." if not category_filter
              else f"No recipes in category: {category_filter}")
        return

    # Build flat list of (title, category_label, filepath)
    items = []
    for f in files:
        first_line = f.read_text(encoding="utf-8").splitlines()[0]
        title = first_line.lstrip("#").strip()
        cat   = get_category(f)
        label = CATEGORIES.get(cat, cat.title())
        items.append((title, label, f))

    selected = 0
    view_top = 0

    import termios as _termios, select as _select, time as _time

    def get_visible():
        try:
            rows, _ = os.get_terminal_size()
        except OSError:
            rows = 24
        return max(4, rows - 8)

    def redraw():
        visible = get_visible()
        # Keep selected in view
        if selected < view_top:
            view_top_new = selected
        elif selected >= view_top + visible:
            view_top_new = selected - visible + 1
        else:
            view_top_new = view_top
        # \033[H = cursor to home, \033[J = clear from cursor down
        # This overwrites content from top without scrolling viewport
        buf  = "\033[H\033[J"
        buf += f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
        buf += f"{BOLD}{CYAN}  Jarvis Recipes  |  {len(items)} recipes{RESET}\n"
        buf += f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n\n"
        for i in range(view_top_new, min(view_top_new + visible, len(items))):
            title, cat_label, _ = items[i]
            if i == selected:
                buf += f"  {BOLD}{GREEN}▶  {title:<40}{RESET}  {GREEN}{DIM}[{cat_label}]{RESET}\n"
            else:
                buf += f"  {DIM}   {title:<40}  [{cat_label}]{RESET}\n"
        buf += "\n"
        if len(items) > visible:
            buf += f"  {DIM}({view_top_new+1}-{min(view_top_new+visible,len(items))} of {len(items)})  "
        else:
            buf += "  "
        buf += f"↑↓ navigate  |  Enter view  |  / search  |  Q/ESC exit{RESET}\n"
        sys.stdout.write(buf)
        sys.stdout.flush()
        return view_top_new

    def flush_input():
        """Drain any buffered input before reading."""
        _termios.tcflush(sys.stdin.fileno(), _termios.TCIFLUSH)
        _time.sleep(0.05)
        while _select.select([sys.stdin], [], [], 0)[0]:
            try:
                os.read(sys.stdin.fileno(), 64)
            except Exception:
                break

    # Enter alternate screen so list always starts at top
    sys.stdout.write("\033[?1049h\033[H\033[J")
    sys.stdout.flush()

    flush_input()
    view_top = redraw()

    try:
        while True:
            key = getch()

            if key in ("q", "Q", "\x03", "\x1b") or (key.startswith("\x1b") and key not in ("\x1b[A", "\x1b[B", "\x1b[C", "\x1b[D")):
                break

            elif key == "\x1b[A":   # up
                selected = (selected - 1) % len(items)
                view_top = redraw()

            elif key == "\x1b[B":   # down
                selected = (selected + 1) % len(items)
                view_top = redraw()

            elif key in ("/", "s", "S"):
                sys.stdout.write("\033[H\033[J")
                sys.stdout.flush()
                try:
                    query = input("  Search recipes: ").strip()
                except (EOFError, KeyboardInterrupt):
                    view_top = redraw()
                    continue
                if query:
                    results = []
                    words = query.lower().split()
                    for title, label, filepath in items:
                        text = filepath.read_text(encoding="utf-8").lower()
                        if any(w in text for w in words):
                            results.append((title, label, filepath))
                    if results:
                        items[:] = results
                        selected = 0
                        view_top = 0
                    else:
                        print(f"  No results for '{query}'. Press any key...")
                        getch()
                view_top = redraw()

            elif key in ("\r", "\n"):
                # Leave alt screen to show recipe in normal terminal
                sys.stdout.write("\033[?1049l")
                sys.stdout.flush()
                display_recipe(items[selected][2])
                print()
                print(f"  {DIM}Press any key to return to list...{RESET}", end="", flush=True)
                try:
                    getch()
                except KeyboardInterrupt:
                    return
                # Re-enter alt screen for browser
                sys.stdout.write("\033[?1049h\033[H\033[J")
                sys.stdout.flush()
                flush_input()
                view_top = redraw()
    finally:
        # Always restore normal screen on exit
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()


def list_recipes(category_filter=None):
    """Alias that opens the interactive browser."""
    browse_recipes(category_filter)


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


# ── main ──────────────────────────────────────────────────────────────────────
arg = sys.argv[1].lower().strip() if len(sys.argv) > 1 else ""

if not arg or arg == "list":
    browse_recipes()

elif arg == "--list":
    list_recipes()

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
