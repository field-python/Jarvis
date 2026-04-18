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


def render_recipe(text):
    """Convert markdown to colored terminal lines."""
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            lines.append(f"\n{BOLD}{CYAN}  {line[3:]}{RESET}")
            lines.append(f"  {CYAN}{'─' * 36}{RESET}")
        elif line.startswith("# "):
            lines.append(f"\n{BOLD}{YELLOW}  {line[2:]}{RESET}")
        elif line.startswith("### "):
            lines.append(f"\n{BOLD}  {line[4:]}{RESET}")
        elif line.strip().startswith("- "):
            lines.append(f"  {CYAN}•{RESET}  {line.strip()[2:]}")
        elif line.strip() and line.strip()[0].isdigit() and ". " in line:
            lines.append(f"  {YELLOW}{line.strip()}{RESET}")
        elif line.strip().startswith("**") and line.strip().endswith("**"):
            lines.append(f"  {BOLD}{line.strip().strip('*')}{RESET}")
        else:
            lines.append(f"  {line}" if line.strip() else "")
    return lines


def display_recipe(filepath):
    """Paged recipe viewer — starts at top, arrow keys scroll, Q/ESC exits."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error reading recipe: {e}")
        getch()
        return

    cat   = get_category(filepath)
    label = CATEGORIES.get(cat, cat.title())
    lines = render_recipe(text)

    offset = 0
    while True:
        try:
            term_rows = os.get_terminal_size().lines - 5
        except OSError:
            term_rows = 20
        page_size = max(8, term_rows)
        total     = len(lines)

        os.system("clear")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}  Jarvis Recipe  |  {label}{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

        end = min(offset + page_size, total)
        for line in lines[offset:end]:
            print(line)

        print()
        pct        = int((end / total) * 100) if total > 0 else 100
        bar_filled = int(pct / 5)
        bar        = f"{YELLOW}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end     = end >= total

        if at_end:
            print(f"  {bar}  {DIM}{pct}%  ── END ──  Q/ESC back  ↑ up{RESET}")
        else:
            print(f"  {bar}  {DIM}{pct}%  Space/↓ next  ↑ up  Q/ESC back{RESET}")

        key = getch()
        if key in ("q", "Q", "\x1b"):
            return
        elif key in (" ", "\x1b[B", "\r", "\n"):
            if not at_end:
                offset = min(offset + page_size, total - page_size)
        elif key == "\x1b[A":
            offset = max(0, offset - page_size)
        elif key in ("g", "G"):
            offset = 0
        elif key in ("e", "E"):
            offset = max(0, total - page_size)


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

    import termios as _termios, select as _sel, time as _time

    def draw_list(sel, top):
        try:
            rows = os.get_terminal_size().lines
        except OSError:
            rows = 24
        visible = max(4, rows - 8)
        os.system("clear")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}{CYAN}  Jarvis Recipes  |  {len(items)} recipes{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print()
        for i in range(top, min(top + visible, len(items))):
            title, cat_label, _ = items[i]
            if i == sel:
                print(f"  {BOLD}{GREEN}▶  {title:<40}{RESET}  {GREEN}{DIM}[{cat_label}]{RESET}")
            else:
                print(f"  {DIM}   {title:<40}  [{cat_label}]{RESET}")
        print()
        if len(items) > visible:
            sys.stdout.write(f"  {DIM}({top+1}-{min(top+visible,len(items))} of {len(items)})  ")
        else:
            sys.stdout.write("  ")
        print(f"↑↓ navigate  |  Enter view  |  / search  |  Q/ESC exit{RESET}")
        return visible

    # Drain buffered keypresses (Enter from menu etc.)
    _termios.tcflush(sys.stdin.fileno(), _termios.TCIFLUSH)
    _time.sleep(0.05)
    while _sel.select([sys.stdin], [], [], 0)[0]:
        try:
            os.read(sys.stdin.fileno(), 64)
        except Exception:
            break

    visible = draw_list(selected, view_top)

    while True:
        key = getch()

        if key in ("q", "Q", "\x03", "\x1b") or (key.startswith("\x1b") and key not in ("\x1b[A", "\x1b[B", "\x1b[C", "\x1b[D")):
            os.system("clear")
            return

        elif key == "\x1b[A":   # up — no wrap
            if selected > 0:
                selected -= 1
                if selected < view_top:
                    view_top = selected
            visible = draw_list(selected, view_top)

        elif key == "\x1b[B":   # down — no wrap
            if selected < len(items) - 1:
                selected += 1
                if selected >= view_top + visible:
                    view_top = selected - visible + 1
            visible = draw_list(selected, view_top)

        elif key in ("/", "s", "S"):
            os.system("clear")
            try:
                query = input("  Search recipes: ").strip()
            except (EOFError, KeyboardInterrupt):
                visible = draw_list(selected, view_top)
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
            visible = draw_list(selected, view_top)

        elif key in ("\r", "\n"):
            display_recipe(items[selected][2])
            _termios.tcflush(sys.stdin.fileno(), _termios.TCIFLUSH)
            visible = draw_list(selected, view_top)


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
