#!/usr/bin/env python3
"""
classics.py — Classic literature browser for Jarvis.
Usage:
  Jarvis classics                  — interactive browser
  Jarvis classics "dracula"        — open directly
  Jarvis classics list             — show full index
"""
import sys
import os
import tty
import termios
import re
import select as _sel
from pathlib import Path

script_dir  = Path(__file__).parent.resolve()
base_dir    = script_dir.parent
classics_dir = base_dir / "notes" / "generated" / "classics"

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
PURPLE = "\033[95m"
WHITE  = "\033[97m"
RESET  = "\033[0m"

GENRE_COLORS = {
    "Adventure":  GREEN,
    "Sci-Fi":     CYAN,
    "Mystery":    YELLOW,
    "Gothic":     PURPLE,
    "Romance":    "\033[95m",
    "Classic":    WHITE,
    "Historical": YELLOW,
    "Philosophy": CYAN,
    "Epic":       YELLOW,
    "Drama":      "\033[95m",
    "Other":      DIM,
}


def load_books():
    books = []
    if not classics_dir.exists():
        return books
    for path in sorted(classics_dir.glob("*.md")):
        meta = parse_meta(path)
        if meta:
            books.append(meta)
    books.sort(key=lambda b: (b["genre"], b["author"], b["title"]))
    return books


def parse_meta(path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        title = author = year = genre = ""
        for line in lines[:8]:
            l = line.strip()
            if l.startswith("# "):
                title = l[2:].strip()
            elif l.lower().startswith("author:"):
                author = l[7:].strip()
            elif l.lower().startswith("year:"):
                year = l[5:].strip()
            elif l.lower().startswith("genre:"):
                genre = l[6:].strip()
        if title:
            return {"title": title, "author": author, "year": year,
                    "genre": genre or "Classic", "path": path, "file": path.name}
    except Exception:
        pass
    return None


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
                if rest and rest[0] == "O" and len(rest) > 1:
                    return "\x1b[" + rest[1]  # normalize \x1bOA \u2192 \x1b[A
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_with_esc(prompt_str):
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        import tty as _tty
        _tty.setcbreak(fd)
        while True:
            ch = os.read(fd, 1).decode("utf-8", "replace")
            if ch == "\x1b":
                r, _, _ = _sel.select([fd], [], [], 0.1)
                if r:
                    os.read(fd, 2)
                    continue
                sys.stdout.write("\n"); sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n"); sys.stdout.flush()
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
                sys.stdout.write(ch); sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear():
    os.system("clear")


# ── rendering ─────────────────────────────────────────────────────────────────

def genre_color(genre):
    return GENRE_COLORS.get(genre, DIM)


def render_markdown(text):
    lines = text.splitlines()
    rendered = []
    skip_meta = True
    for line in lines:
        # Skip frontmatter-style lines at top
        if skip_meta and re.match(r'^(author|year|genre):', line.strip(), re.I):
            continue
        skip_meta = False
        if line.startswith("## "):
            rendered.append(f"\n{BOLD}{YELLOW}  {line[3:]}{RESET}")
            rendered.append(f"  {YELLOW}{'─' * 50}{RESET}")
        elif line.startswith("# "):
            rendered.append(f"\n{BOLD}{YELLOW}━━━ {line[2:]} ━━━{RESET}")
        elif line.startswith("### "):
            rendered.append(f"\n{BOLD}  {line[4:]}{RESET}")
        elif line.strip().startswith("- "):
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', line.strip()[2:])
            rendered.append(f"  {YELLOW}•{RESET}  {txt}")
        elif line.strip().startswith("> "):
            txt = line.strip()[2:]
            rendered.append(f"  {DIM}{YELLOW}│{RESET}  {DIM}{txt}{RESET}")
        else:
            txt = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', line)
            txt = re.sub(r'\*(.+?)\*',     f'{DIM}\\1{RESET}',   txt)
            rendered.append(f"  {txt}" if txt.strip() else "")
    return rendered


def build_toc(lines):
    """Find chapter/section headers and their line offsets."""
    toc = []
    ansi = re.compile(r'\033\[[0-9;]*m')
    for i, line in enumerate(lines):
        plain = ansi.sub('', line).strip()
        if plain and len(plain) < 80 and (
            plain.startswith("━━━") or
            plain.startswith("──") or
            plain.isupper() or
            plain.lower().startswith("chapter ") or
            plain.lower().startswith("book ") or
            plain.lower().startswith("part ") or
            plain.lower().startswith("volume ")
        ):
            label = plain.strip("━─ ").strip()
            if label and len(label) > 2:
                toc.append((label[:68], i))
    return toc


def toc_browser(toc, title, page_size):
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
        print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}")
        print(f"{BOLD}  {title}  |  Table of Contents{RESET}")
        print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}\n")
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
            return line_idx


def view_book(book):
    try:
        text = book["path"].read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Error: {e}"); getch(); return

    lines     = render_markdown(text)
    toc       = build_toc(lines)
    term_rows = os.get_terminal_size().lines - 5
    page_size = max(10, term_rows)
    total     = len(lines)
    offset    = 0

    while True:
        clear()
        col = genre_color(book["genre"])
        print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}")
        print(f"{BOLD}  {book['title']}{RESET}  {DIM}by {book['author']} ({book['year']}){RESET}  {col}{DIM}[{book['genre']}]{RESET}")
        print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}")

        end = min(offset + page_size, total)
        for line in lines[offset:end]:
            print(line)

        print()
        pct        = int((end / total) * 100) if total > 0 else 100
        bar_filled = int(pct / 5)
        bar        = f"{YELLOW}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end     = end >= total
        toc_hint   = f"  {YELLOW}[T]{RESET}{DIM} contents{RESET}" if toc else ""

        if at_end:
            print(f"  {bar}  {DIM}{pct}%  END  Q/ESC back  ↑ up{RESET}{toc_hint}")
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
            jump = toc_browser(toc, book["title"], page_size)
            if jump is not None:
                offset = min(jump, max(0, total - page_size))


# ── list browser ──────────────────────────────────────────────────────────────

def draw_list(books, selected, view_top, title="Classic Literature"):
    clear()
    term_rows = os.get_terminal_size().lines - 8
    visible   = max(5, term_rows)
    print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}")
    print(f"{BOLD}{YELLOW}  Jarvis Library  |  {title}{RESET}")
    print(f"{BOLD}{YELLOW}{'━' * 72}{RESET}")
    print()
    for i in range(view_top, min(view_top + visible, len(books))):
        b   = books[i]
        num = f"{i + 1:>3}."
        col = genre_color(b["genre"])
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {b['title']:<40}{RESET}  {DIM}by {b['author']}{RESET}")
        else:
            print(f"  {DIM}{num}    {col}{b['title']:<40}{RESET}  {DIM}by {b['author']}{RESET}")
    print()
    print(f"  {DIM}↑↓ navigate  |  Enter read  |  / search  |  G genre filter  |  Q quit{RESET}")
    print()


def browse(books, title="Classic Literature"):
    selected = 0
    view_top = 0
    while True:
        term_rows = os.get_terminal_size().lines - 8
        visible   = max(5, term_rows)
        draw_list(books, selected, view_top, title)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            return
        elif key == "\x1b[A":
            selected = max(0, selected - 1)
            if selected < view_top:
                view_top = selected
        elif key == "\x1b[B":
            selected = min(len(books) - 1, selected + 1)
            if selected >= view_top + visible:
                view_top = selected - visible + 1
        elif key in ("\r", "\n"):
            if books:
                view_book(books[selected])
        elif key == "/":
            q = input_with_esc(f"  {YELLOW}Search: {RESET}")
            if not q or not q.strip():
                continue
            q = q.strip().lower()
            results = [b for b in books if q in b["title"].lower()
                       or q in b["author"].lower() or q in b["genre"].lower()]
            if results:
                browse(results, title=f"Results: {q}")
            else:
                clear()
                print(f"\n  {RED}No results for: {q}{RESET}")
                print(f"  {DIM}Press any key...{RESET}", flush=True)
                getch()
        elif key in ("g", "G"):
            genres = sorted(set(b["genre"] for b in books))
            sel = 0
            while True:
                clear()
                print(f"{BOLD}{YELLOW}{'━' * 60}{RESET}")
                print(f"{BOLD}{YELLOW}  Filter by Genre{RESET}")
                print(f"{BOLD}{YELLOW}{'━' * 60}{RESET}\n")
                all_genres = ["All"] + genres
                for i, g in enumerate(all_genres):
                    col = genre_color(g)
                    cnt = len(books) if g == "All" else len([b for b in books if b["genre"] == g])
                    if i == sel:
                        print(f"  {BOLD}{GREEN}▶ {g:<20} {DIM}({cnt}){RESET}")
                    else:
                        print(f"  {col}  {g:<20} {DIM}({cnt}){RESET}")
                print(f"\n  {DIM}↑↓ navigate  |  Enter select  |  Q/ESC back{RESET}")
                k = getch()
                if k in ("q", "Q", "\x1b"):
                    break
                elif k == "\x1b[A":
                    sel = max(0, sel - 1)
                elif k == "\x1b[B":
                    sel = min(len(all_genres) - 1, sel + 1)
                elif k in ("\r", "\n"):
                    chosen = all_genres[sel]
                    filtered = books if chosen == "All" else [b for b in books if b["genre"] == chosen]
                    browse(filtered, title=f"Genre: {chosen}")
                    break


def find_direct(books, query):
    q = query.lower()
    for b in books:
        if b["title"].lower() == q:
            return b
    for b in books:
        slug = b["file"].replace(".md", "").lower()
        if slug == q.replace(" ", "-"):
            return b
    for b in books:
        if b["title"].lower().startswith(q):
            return b
    for b in books:
        if q in b["title"].lower() or q in b["author"].lower():
            return b
    return None


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    books = load_books()
    if not books:
        print(f"\n{BOLD}{YELLOW}Jarvis Library{RESET}")
        print(f"\n  No classic books found in: {classics_dir}")
        print(f"  Run: ~/.jarvis-venv/bin/python scripts/download-classics.py\n")
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        browse(books)
        clear()
        return

    query = " ".join(args).lower()

    if query == "list":
        current_genre = None
        print(f"\n{BOLD}{YELLOW}Jarvis Library — Classic Literature{RESET}\n")
        for b in books:
            if b["genre"] != current_genre:
                current_genre = b["genre"]
                col = genre_color(current_genre)
                print(f"\n  {col}{BOLD}{current_genre}{RESET}")
            print(f"    • {b['title']}  {DIM}— {b['author']} ({b['year']}){RESET}")
        print()
        return

    match = find_direct(books, query)
    if match:
        view_book(match)
        clear()
        return

    print(f"\n  No book found matching: {query}")
    print(f"  Try: Jarvis classics list\n")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
