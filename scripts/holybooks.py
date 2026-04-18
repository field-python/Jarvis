#!/usr/bin/env python3
"""
holybooks.py — Offline Holy Books browser for Jarvis.
Arrow keys to navigate, Enter to read, page through any sacred text.
Usage:
  Jarvis holybooks               — interactive browser
  Jarvis holybooks bible         — open a book directly
  Jarvis holybooks list          — show all books
"""
import sys
import os
import tty
import termios
import re
import select as _sel
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
texts_dir  = base_dir / "notes" / "generated" / "sacred-texts"

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GOLD   = "\033[93m"
GREEN  = "\033[92m"
WHITE  = "\033[97m"
RESET  = "\033[0m"

# ── book registry ─────────────────────────────────────────────────────────────
# (display_name, filename, tradition, group)
# group: "main" = top 10, "other" = Other Books
BOOKS = [
    ("Bible (KJV)",              "bible-kjv.md",                   "Christianity",    "main"),
    ("Torah (JPS)",              "torah-jps.md",                   "Judaism",         "main"),
    ("Quran",                    "quran-pickthall.md",              "Islam",           "main"),
    ("Book of Mormon",           "book-of-mormon.md",              "LDS",             "main"),
    ("Bhagavad Gita",            "bhagavad-gita.md",               "Hinduism",        "main"),
    ("Tao Te Ching",             "tao-te-ching.md",                "Taoism",          "main"),
    ("Talmud / Mishnah",         "talmud-mishnah-key-tractates.md","Judaism",         "main"),
    ("Rig Veda",                 "rig-veda.md",                    "Hinduism",        "main"),
    ("Upanishads",               "upanishads.md",                  "Hinduism",        "main"),
    ("Dhammapada",               "dhammapada.md",                  "Buddhism",        "main"),
    ("Analects of Confucius",    "analects-confucius.md",          "Confucianism",    "main"),
    ("The Kybalion",             "kybalion.md",                    "Hermetic",        "other"),
    ("Avesta (Zoroastrian)",     "avesta-zoroastrian.md",          "Zoroastrianism",  "other"),
    ("Book of Enoch",            "book-of-enoch.md",               "Apocrypha",       "other"),
    ("Book of Jubilees",         "book-of-jubilees.md",            "Apocrypha",       "other"),
    ("Dead Sea Scrolls",         "dead-sea-scrolls.md",            "Apocrypha",       "other"),
    ("Ethiopian Bible Overview", "ethiopian-bible-overview.md",    "Christianity",    "other"),
    ("Gospel of Thomas",         "gospel-of-thomas.md",            "Gnostic",         "other"),
    ("Guru Granth Sahib",        "guru-granth-sahib.md",           "Sikhism",         "other"),
    ("Pirkei Avot",              "pirkei-avot-ethics-of-fathers.md","Judaism",        "other"),
]

TRADITION_COLORS = {
    "Christianity":   GOLD,
    "Islam":          GREEN,
    "Judaism":        GOLD,
    "LDS":            CYAN,
    "Hinduism":       "\033[91m",  # red-orange
    "Buddhism":       "\033[94m",  # blue
    "Taoism":         CYAN,
    "Confucianism":   GREEN,
    "Zoroastrianism": GOLD,
    "Apocrypha":      DIM,
    "Gnostic":        "\033[95m",  # purple
    "Sikhism":        "\033[92m",  # green
    "Hermetic":       "\033[95m",  # purple
}


def load_books(group=None):
    """Return book entries that have an existing file, filtered by group."""
    result = []
    for name, fname, tradition, grp in BOOKS:
        if group and grp != group:
            continue
        path = texts_dir / fname
        if path.exists():
            result.append({"name": name, "tradition": tradition,
                            "group": grp, "path": path, "file": fname})
    return result


# ── terminal helpers ──────────────────────────────────────────────────────────

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        import tty as _tty, os as _os
        _tty.setraw(fd)
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


def input_with_esc(prompt_str):
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    import re as _re
    _vlen = len(_re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        import tty as _tty
        _tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = _sel.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
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

def trad_color(tradition):
    return TRADITION_COLORS.get(tradition, DIM)


def render_markdown(text):
    lines = text.splitlines()
    rendered = []
    for line in lines:
        if line.startswith("## "):
            rendered.append(f"\n{BOLD}{GOLD}  {line[3:]}{RESET}")
            rendered.append(f"  {GOLD}{'─' * 50}{RESET}")
        elif line.startswith("# "):
            rendered.append(f"\n{BOLD}{GOLD}━━━ {line[2:]} ━━━{RESET}")
        elif line.startswith("### "):
            rendered.append(f"\n{BOLD}  {line[4:]}{RESET}")
        elif line.strip().startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if all(set(p) <= set("-: ") for p in parts):
                continue
            row = "  "
            for j, p in enumerate(parts):
                row += f"{BOLD}{p:<22}{RESET}  " if j == 0 else f"{p}  "
            rendered.append(row)
        elif line.strip().startswith("- "):
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', line.strip()[2:])
            rendered.append(f"  {GOLD}•{RESET}  {txt}")
        elif re.match(r'^\d+\.', line.strip()):
            txt = re.sub(r'^\d+\.\s*', '', line.strip())
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', txt)
            num = re.match(r'^(\d+)\.', line.strip()).group(1)
            rendered.append(f"  {GOLD}{num}.{RESET}  {txt}")
        else:
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', line)
            txt = re.sub(r'\*(.+?)\*',     f'{DIM}\\1{RESET}',   txt)
            rendered.append(f"  {txt}" if txt.strip() else "")
    return rendered


def build_toc(lines):
    """Find all section headers and their line offsets."""
    toc = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match rendered headers (lines starting with bold/colored markers or plain caps)
        if stripped.startswith("  ") and "━" in stripped:
            continue
        if stripped.startswith("\033["):
            # strip ANSI to detect headers
            import re as _re
            plain = _re.sub(r"\033\[[0-9;]*m", "", stripped).strip()
        else:
            plain = stripped
        # Detect section headers: short lines, mostly non-blank
        if plain and len(plain) < 80 and (
            plain.isupper() or
            plain.startswith("##") or
            plain.startswith("Book ") or
            plain.startswith("Chapter ") or
            plain.startswith("CHAPTER") or
            plain.startswith("Surah") or
            plain.startswith("Sura ") or
            plain.startswith("Psalm") or
            plain.startswith("The Book") or
            plain.startswith("The First") or
            plain.startswith("The Second") or
            plain.startswith("The Third") or
            plain.startswith("The Fourth") or
            plain.startswith("The Fifth") or
            plain.startswith("Gospel") or
            plain.startswith("Acts ") or
            plain.startswith("Revelation") or
            plain.startswith("Tractate") or
            plain.startswith("Part ")
        ):
            label = plain.lstrip("# ").strip()
            if label and len(label) > 2:
                toc.append((label[:70], i))
    return toc


def toc_browser(toc, book_name, page_size):
    """Arrow-key TOC selector. Returns line offset or None."""
    selected = 0
    view_top = 0

    while True:
        clear()
        try:
            rows = os.get_terminal_size().lines - 6
        except OSError:
            rows = 20
        visible = max(5, rows)

        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")
        print(f"{BOLD}  {book_name}  |  Table of Contents{RESET}")
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}\n")

        for i in range(view_top, min(view_top + visible, len(toc))):
            label, _ = toc[i]
            if i == selected:
                print(f"  {BOLD}{GREEN}▶  {label}{RESET}")
            else:
                print(f"  {DIM}   {label}{RESET}")

        print(f"\n  {DIM}↑↓ navigate  |  Enter jump  |  Q back{RESET}")

        key = getch()
        if key in ("q", "Q", "\x1b"):
            return None
        elif key == "\x1b[A":
            selected = max(0, selected - 1)
            if selected < view_top:
                view_top = selected
        elif key == "\x1b[B":
            selected = min(len(toc) - 1, selected + 1)
            if selected >= view_top + visible:
                view_top = selected - visible + 1
        elif key in ("\r", "\n"):
            _, line_idx = toc[selected]
            return max(0, line_idx - 1)


def view_book(book):
    try:
        text = book["path"].read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error reading file: {e}")
        getch()
        return

    lines     = render_markdown(text)
    term_rows = os.get_terminal_size().lines - 5
    page_size = max(10, term_rows)
    total     = len(lines)
    offset    = 0
    toc       = build_toc(lines)

    while True:
        clear()
        col = trad_color(book["tradition"])
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")
        print(f"{BOLD}  {book['name']}{RESET}  {col}{DIM}[{book['tradition']}]{RESET}")
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")

        end = min(offset + page_size, total)
        for line in lines[offset:end]:
            print(line)

        print()
        pct        = int((end / total) * 100) if total > 0 else 100
        bar_filled = int(pct / 5)
        bar        = f"{GOLD}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end     = end >= total
        toc_hint   = f"  {YELLOW}[T]{RESET}{DIM} contents{RESET}" if toc else ""

        if at_end:
            print(f"  {bar}  {DIM}{pct}%  ── END ──  Q/ESC back  ↑ up{RESET}{toc_hint}")
        else:
            print(f"  {bar}  {DIM}{pct}%  Space/↓ next  ↑ up  Q/ESC back{RESET}{toc_hint}")

        key = getch()
        if key in ("q", "Q", "\x1b"):
            return
        elif key in (" ", "\x1b[B", "\r", "\n"):
            if not at_end:
                offset = max(0, min(offset + page_size, total - page_size))
        elif key == "\x1b[A":
            offset = max(0, offset - page_size)
        elif key in ("g", "G"):
            offset = 0
        elif key in ("e", "E"):
            offset = max(0, total - page_size)
        elif key in ("t", "T") and toc:
            jump = toc_browser(toc, book["name"], page_size)
            if jump is not None:
                offset = min(jump, max(0, total - page_size))


# ── list browser ──────────────────────────────────────────────────────────────

def draw_list(books, selected, view_top, title="Holy Books"):
    clear()
    term_rows = os.get_terminal_size().lines - 8
    visible   = max(5, term_rows)
    HR = "━" * 72

    print(f"{BOLD}{GOLD}{HR}{RESET}")
    print(f"{BOLD}{GOLD}  Jarvis  |  {title}{RESET}")
    print(f"{BOLD}{GOLD}{HR}{RESET}")
    print()

    for i in range(view_top, min(view_top + visible, len(books))):
        b   = books[i]
        num = f"{i + 1:>3}."
        col = trad_color(b["tradition"])
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {b['name']:<36}{RESET}  {col}{DIM}[{b['tradition']}]{RESET}")
        else:
            print(f"  {DIM}{num}    {b['name']:<36}  [{b['tradition']}]{RESET}")

    print()
    print(f"  {DIM}↑↓ navigate  |  Enter open  |  / search  |  Q quit{RESET}")
    print()


def browse(books, title="Holy Books"):
    selected = 0
    view_top = 0

    while True:
        term_rows = os.get_terminal_size().lines - 8
        visible   = max(5, term_rows)
        draw_list(books, selected, view_top, title)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            return

        elif key == "\x1b[A":  # up
            selected = max(0, selected - 1)
            if selected < view_top:
                view_top = selected

        elif key == "\x1b[B":  # down
            selected = min(len(books) - 1, selected + 1)
            if selected >= view_top + visible:
                view_top = selected - visible + 1

        elif key in ("\r", "\n"):
            if books:
                view_book(books[selected])

        elif key == "/":
            q = input_with_esc(f"  {GOLD}Search: {RESET}")
            if not q or not q.strip():
                continue
            q = q.strip().lower()
            results = [b for b in books
                       if q in b["name"].lower() or q in b["tradition"].lower()]
            if results:
                browse(results, title=f"Results: {q}")
            else:
                clear()
                print(f"\n  {GOLD}No results for: {q}{RESET}")
                print(f"  {DIM}Press any key...{RESET}", flush=True)
                getch()

        elif key.isdigit():
            n = int(key)
            if 1 <= n <= len(books):
                selected  = n - 1
                view_top  = max(0, selected - visible // 2)


def find_direct(books, query):
    q = query.lower()
    for b in books:
        if b["name"].lower() == q:
            return b
    for b in books:
        slug = b["file"].replace(".md", "").lower()
        if slug == q.replace(" ", "-"):
            return b
    for b in books:
        if b["name"].lower().startswith(q):
            return b
    for b in books:
        if q in b["name"].lower() or q in b["tradition"].lower():
            return b
    return None


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    all_books  = load_books()
    main_books = [b for b in all_books if b["group"] == "main"]
    all_sorted = main_books + [b for b in all_books if b["group"] == "other"]

    if not all_books:
        print(f"\n{BOLD}{GOLD}Jarvis Holy Books{RESET}")
        print(f"\n  No text files found in: {texts_dir}\n")
        sys.exit(1)

    args = sys.argv[1:]

    if not args:
        browse(all_sorted, "Holy Books")
        clear()
        return

    query = " ".join(args).lower()

    if query == "list":
        print(f"\n{BOLD}{GOLD}Jarvis Holy Books — Index{RESET}\n")
        current_grp = None
        for b in all_sorted:
            grp_label = "Top Books" if b["group"] == "main" else "Other Books"
            if grp_label != current_grp:
                current_grp = grp_label
                print(f"\n  {GOLD}{BOLD}{current_grp}{RESET}")
            col = trad_color(b["tradition"])
            print(f"    {col}•{RESET}  {b['name']}  {DIM}[{b['tradition']}]{RESET}")
        print()
        return

    if query == "other":
        other = [b for b in all_books if b["group"] == "other"]
        browse(other, "Other Books")
        clear()
        return

    match = find_direct(all_books, query)
    if match:
        view_book(match)
        clear()
        return

    print(f"\n  No book found matching: {query}")
    print(f"  Try: Jarvis holybooks list\n")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
