#!/usr/bin/env python3
"""
erowid.py — Offline Erowid-style substance reference browser for Jarvis.
Arrow keys to navigate, Enter to read, search by name or category.
Usage:
  Jarvis erowid               — interactive browser
  Jarvis erowid psilocybin    — open substance directly
  Jarvis erowid list          — show all substances
"""
import sys
import os
import tty
import termios
import re
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
erowid_dir = base_dir / "erowid"

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
PURPLE = "\033[95m"
RESET  = "\033[0m"

CATEGORY_COLORS = {
    "Psychedelics":  CYAN,
    "Empathogens":   PURPLE,
    "Dissociatives": YELLOW,
    "Stimulants":    RED,
    "Depressants":   "\033[94m",  # blue
    "Opioids":       "\033[91m",  # red
    "Cannabinoids":  GREEN,
    "Other":         DIM,
}


# ── file loading ──────────────────────────────────────────────────────────────

def load_substances():
    """Load all .md files from the erowid/ directory and parse their metadata."""
    substances = []
    if not erowid_dir.exists():
        return substances

    for path in sorted(erowid_dir.glob("*.md")):
        name, tags, category = parse_header(path)
        if name:
            substances.append({
                "name":     name,
                "tags":     tags,
                "category": category,
                "path":     path,
                "file":     path.name,
            })

    # Sort by category then name
    cat_order = ["Psychedelics", "Empathogens", "Dissociatives", "Stimulants",
                 "Depressants", "Opioids", "Cannabinoids", "Other"]
    substances.sort(key=lambda s: (
        cat_order.index(s["category"]) if s["category"] in cat_order else 99,
        s["name"]
    ))
    return substances


def parse_header(path):
    """Extract name, tags, and category from the top of a substance file."""
    name = ""
    tags = []
    category = "Other"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines[:6]:
            line = line.strip()
            if line.startswith("# "):
                name = line[2:].strip()
            elif line.lower().startswith("tags:"):
                tags = [t.strip() for t in line[5:].split(",")]
            elif line.lower().startswith("category:"):
                category = line[9:].strip()
    except Exception:
        pass
    return name, tags, category


# ── terminal input ────────────────────────────────────────────────────────────

def getch():
    import select as _sel, os as _os
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = _sel.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", errors="replace")
                if rest and rest[0] == "O" and len(rest) > 1:
                    return "\x1b[" + rest[1]  # normalize \x1bOA \u2192 \x1b[A
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_with_esc(prompt_str):
    import select as _sel
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    import re as _re
    _vlen = len(_re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = os.read(fd, 1).decode("utf-8", "replace")
            if ch == "\x1b":
                r, _, _ = _sel.select([fd], [], [], 0.1)
                if r:
                    os.read(fd, 2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf.pop()
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = total // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
                    sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear():
    os.system("clear")


# ── rendering ─────────────────────────────────────────────────────────────────

def cat_color(category):
    return CATEGORY_COLORS.get(category, DIM)


def draw_list(substances, selected, view_top, search_term=""):
    clear()
    term_rows = os.get_terminal_size().lines - 8
    visible   = max(5, term_rows)

    print(f"{BOLD}{CYAN}{'━' * 72}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis Erowid  |  Offline Substance Reference{RESET}")
    print(f"{BOLD}{CYAN}{'━' * 72}{RESET}")
    print()

    for i in range(view_top, min(view_top + visible, len(substances))):
        s   = substances[i]
        num = f"{i + 1:>3}."
        col = cat_color(s["category"])
        cat = f"{DIM}[{s['category']}]{RESET}"
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {s['name']:<32}{RESET}  {col}{DIM}[{s['category']}]{RESET}")
        else:
            print(f"  {DIM}{num}    {s['name']:<32}  [{s['category']}]{RESET}")

    print()
    if search_term:
        print(f"  {YELLOW}Search: {search_term}{RESET}")
    print(f"  {DIM}↑↓ navigate  |  Enter open  |  / search  |  C categories  |  Q quit{RESET}")
    print()


def draw_categories(substances, selected_cat):
    clear()
    cats = ["All"] + sorted(set(s["category"] for s in substances))
    print(f"{BOLD}{CYAN}{'━' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis Erowid  |  Browse by Category{RESET}")
    print(f"{BOLD}{CYAN}{'━' * 60}{RESET}")
    print()
    for i, cat in enumerate(cats):
        count = len([s for s in substances if cat == "All" or s["category"] == cat])
        col   = cat_color(cat) if cat != "All" else CYAN
        if i == selected_cat:
            print(f"  {BOLD}{GREEN}▶ {cat:<20} {DIM}({count} substances){RESET}")
        else:
            print(f"  {col}{DIM}  {cat:<20} ({count} substances){RESET}")
    print()
    print(f"  {DIM}↑↓ navigate  |  Enter select  |  Q/ESC back{RESET}")
    print()
    return cats


# ── substance viewer ──────────────────────────────────────────────────────────

def render_markdown(text):
    """Apply basic terminal formatting to markdown content."""
    lines = text.splitlines()
    rendered = []
    in_table = False
    for line in lines:
        # Headers
        if line.startswith("## "):
            rendered.append(f"\n{BOLD}{CYAN}  {line[3:]}{RESET}")
            rendered.append(f"  {CYAN}{'─' * 50}{RESET}")
        elif line.startswith("# "):
            rendered.append(f"\n{BOLD}{CYAN}━━━ {line[2:]} ━━━{RESET}")
        # Table rows
        elif line.strip().startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if all(set(p) <= set("-: ") for p in parts):
                # Separator row — skip
                in_table = True
                continue
            row = "  "
            for j, p in enumerate(parts):
                if j == 0:
                    row += f"{BOLD}{p:<22}{RESET}  "
                else:
                    row += f"{p}  "
            rendered.append(row)
            in_table = True
        # Bold/italic inline (basic)
        elif line.strip().startswith("**") and line.strip().endswith("**") and len(line.strip()) > 4:
            txt = line.strip()[2:-2]
            rendered.append(f"\n  {BOLD}{txt}{RESET}")
        # Bullet points
        elif line.strip().startswith("- "):
            txt = line.strip()[2:]
            # Inline bold
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', txt)
            indent = "    " * (len(line) - len(line.lstrip()) + 1)
            rendered.append(f"  {YELLOW}•{RESET}  {txt}")
        # Numbered list
        elif re.match(r'^\d+\.', line.strip()):
            txt = re.sub(r'^\d+\.\s*', '', line.strip())
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', txt)
            num = re.match(r'^(\d+)\.', line.strip()).group(1)
            rendered.append(f"  {CYAN}{num}.{RESET}  {txt}")
        # Tags/category metadata line (skip)
        elif line.lower().startswith("tags:") or line.lower().startswith("category:"):
            continue
        # Regular text
        else:
            if in_table and not line.strip().startswith("|"):
                in_table = False
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', line)
            txt = re.sub(r'\*(.+?)\*', f'{DIM}\\1{RESET}', txt)
            rendered.append(f"  {txt}" if txt.strip() else "")
    return rendered


def view_substance(substance):
    """Display a substance page with paging."""
    try:
        text = substance["path"].read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error reading file: {e}")
        getch()
        return

    lines = render_markdown(text)
    term_rows = os.get_terminal_size().lines - 5
    page_size = max(10, term_rows)
    total_lines = len(lines)
    offset = 0

    while True:
        clear()
        col = cat_color(substance["category"])
        print(f"{BOLD}{CYAN}{'━' * 72}{RESET}")
        print(f"{BOLD}  {substance['name']}{RESET}  {col}{DIM}[{substance['category']}]{RESET}")
        print(f"{BOLD}{CYAN}{'━' * 72}{RESET}")

        end = min(offset + page_size, total_lines)
        for line in lines[offset:end]:
            print(line)

        print()
        pct = int((end / total_lines) * 100) if total_lines > 0 else 100
        bar_filled = int(pct / 5)
        bar = f"{CYAN}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end   = end >= total_lines
        at_start = offset == 0

        if at_end:
            print(f"  {bar}  {DIM}{pct}%  ── END ──  Q/ESC back  ↑ scroll up{RESET}")
        else:
            print(f"  {bar}  {DIM}{pct}%  Space/↓ next  ↑ scroll up  Q/ESC back{RESET}")

        key = getch()
        if key in ("q", "Q", "\x1b"):
            return
        elif key in (" ", "\x1b[B", "\r", "\n"):
            if not at_end:
                offset = min(offset + page_size, total_lines - page_size)
                offset = max(0, offset)
        elif key == "\x1b[A":
            offset = max(0, offset - page_size)
        elif key in ("g", "G"):
            offset = 0
        elif key in ("e", "E"):
            offset = max(0, total_lines - page_size)


# ── search ────────────────────────────────────────────────────────────────────

def search_substances(substances, query):
    """Fuzzy match substances by name or tag."""
    q = query.lower()
    results = []
    for s in substances:
        score = 0
        name_lower = s["name"].lower()
        if q == name_lower:
            score = 100
        elif name_lower.startswith(q):
            score = 80
        elif q in name_lower:
            score = 60
        elif any(q in t.lower() for t in s["tags"]):
            score = 40
        elif q in s["category"].lower():
            score = 20
        if score > 0:
            results.append((score, s))
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results]


def find_direct_match(substances, query):
    """Find best single match for a direct command-line query."""
    q = query.lower()
    # Exact match first
    for s in substances:
        if s["name"].lower() == q:
            return s
    # File name match
    for s in substances:
        fname = s["file"].replace(".md", "").lower()
        if fname == q.replace(" ", "-").replace("_", "-"):
            return s
    # Starts with match
    for s in substances:
        if s["name"].lower().startswith(q):
            return s
    # Substring match
    for s in substances:
        if q in s["name"].lower() or any(q in t.lower() for t in s["tags"]):
            return s
    return None


# ── main browser ──────────────────────────────────────────────────────────────

def browse(substances, start_filter=None):
    filtered   = substances if not start_filter else start_filter
    selected   = 0
    view_top   = 0
    search_str = ""

    while True:
        term_rows = os.get_terminal_size().lines - 8
        visible   = max(5, term_rows)

        draw_list(filtered, selected, view_top, search_str)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            return

        elif key in ("g",):
            selected = 0
            view_top = 0

        elif key == "\x1b[A":  # up
            selected = max(0, selected - 1)
            if selected < view_top:
                view_top = selected

        elif key == "\x1b[B":  # down
            selected = min(len(filtered) - 1, selected + 1)
            if selected >= view_top + visible:
                view_top = selected - visible + 1

        elif key in ("\r", "\n"):
            if filtered:
                view_substance(filtered[selected])

        elif key == "/":
            # Search mode
            q = input_with_esc(f"  {YELLOW}Search substance: {RESET}")
            if q is None:
                continue
            q = q.strip()
            if not q:
                filtered   = substances
                search_str = ""
                selected   = 0
                view_top   = 0
            else:
                results = search_substances(substances, q)
                if results:
                    filtered   = results
                    search_str = q
                    selected   = 0
                    view_top   = 0
                else:
                    clear()
                    print(f"\n  {RED}No results for: {q}{RESET}")
                    print(f"  {DIM}Press any key...{RESET}", flush=True)
                    getch()

        elif key in ("c", "C"):
            # Category browser
            cat_sel = 0
            while True:
                cats = draw_categories(substances, cat_sel)
                k = getch()
                if k in ("q", "Q", "\x1b"):
                    break
                elif k == "\x1b[A":
                    cat_sel = max(0, cat_sel - 1)
                elif k == "\x1b[B":
                    cat_sel = min(len(cats) - 1, cat_sel + 1)
                elif k in ("\r", "\n"):
                    chosen = cats[cat_sel]
                    if chosen == "All":
                        filtered   = substances
                        search_str = ""
                    else:
                        filtered   = [s for s in substances if s["category"] == chosen]
                        search_str = f"Category: {chosen}"
                    selected = 0
                    view_top = 0
                    break

        elif key.isdigit():
            # Number jump
            n = int(key)
            if 1 <= n <= len(filtered):
                selected = n - 1
                view_top = max(0, selected - visible // 2)


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    substances = load_substances()

    if not substances:
        print(f"\n{BOLD}{CYAN}Jarvis Erowid{RESET}")
        print(f"\n  {RED}No substance files found in: {erowid_dir}{RESET}")
        print(f"  {DIM}Expected .md files in the erowid/ directory.{RESET}\n")
        sys.exit(1)

    args = sys.argv[1:]

    if not args:
        # Interactive browser
        browse(substances)
        clear()
        return

    query = " ".join(args).lower()

    if query == "list":
        print(f"\n{BOLD}{CYAN}Jarvis Erowid — Substance Index{RESET}\n")
        current_cat = None
        for s in substances:
            if s["category"] != current_cat:
                current_cat = s["category"]
                col = cat_color(current_cat)
                print(f"\n  {col}{BOLD}{current_cat}{RESET}")
            print(f"    • {s['name']}")
        print()
        return

    # Try direct match
    match = find_direct_match(substances, query)
    if match:
        view_substance(match)
        clear()
        return

    # Fuzzy search results
    results = search_substances(substances, query)
    if not results:
        print(f"\n  {RED}No substance found matching: {query}{RESET}")
        print(f"  {DIM}Try: Jarvis erowid list{RESET}\n")
        sys.exit(1)

    if len(results) == 1:
        view_substance(results[0])
        clear()
        return

    # Multiple results — show filtered browser
    browse(substances, start_filter=results)
    clear()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
