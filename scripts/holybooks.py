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
YELLOW = "\033[93m"
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
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    import re as _re
    _vlen = len(_re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
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


# ── Bible reference lookup ────────────────────────────────────────────────────

# Maps common names/abbreviations → substring to find in the KJV file's book headers
BIBLE_BOOKS = {
    # Old Testament
    "genesis":"Genesis","gen":"Genesis","gn":"Genesis",
    "exodus":"Exodus","exo":"Exodus","ex":"Exodus",
    "leviticus":"Leviticus","lev":"Leviticus","lv":"Leviticus",
    "numbers":"Numbers","num":"Numbers","nm":"Numbers",
    "deuteronomy":"Deuteronomy","deut":"Deuteronomy","dt":"Deuteronomy",
    "joshua":"Joshua","josh":"Joshua","jos":"Joshua",
    "judges":"Judges","judg":"Judges","jdg":"Judges",
    "ruth":"Ruth","rut":"Ruth",
    "1 samuel":"First Book of Samuel","1sam":"First Book of Samuel","1 sam":"First Book of Samuel",
    "2 samuel":"Second Book of Samuel","2sam":"Second Book of Samuel","2 sam":"Second Book of Samuel",
    "1 kings":"First Book of the Kings","1kings":"First Book of the Kings","1 kgs":"First Book of the Kings",
    "2 kings":"Second Book of the Kings","2kings":"Second Book of the Kings","2 kgs":"Second Book of the Kings",
    "1 chronicles":"First Book of the Chronicles","1chr":"First Book of the Chronicles","1 chr":"First Book of the Chronicles",
    "2 chronicles":"Second Book of the Chronicles","2chr":"Second Book of the Chronicles","2 chr":"Second Book of the Chronicles",
    "ezra":"Ezra","ezr":"Ezra",
    "nehemiah":"Nehemiah","neh":"Nehemiah",
    "esther":"Esther","est":"Esther",
    "job":"Book of Job","jb":"Book of Job",
    "psalms":"Book of Psalms","psalm":"Book of Psalms","ps":"Book of Psalms","psa":"Book of Psalms",
    "proverbs":"Proverbs","prov":"Proverbs","prv":"Proverbs",
    "ecclesiastes":"Ecclesiastes","eccl":"Ecclesiastes","ecc":"Ecclesiastes",
    "song of solomon":"Song of Solomon","song":"Song of Solomon","sos":"Song of Solomon",
    "isaiah":"Isaiah","isa":"Isaiah",
    "jeremiah":"Jeremiah","jer":"Jeremiah",
    "lamentations":"Lamentations","lam":"Lamentations",
    "ezekiel":"Ezekiel","ezek":"Ezekiel","eze":"Ezekiel",
    "daniel":"Daniel","dan":"Daniel","dn":"Daniel",
    "hosea":"Hosea","hos":"Hosea",
    "joel":"Joel","jl":"Joel",
    "amos":"Amos","am":"Amos",
    "obadiah":"Obadiah","obad":"Obadiah",
    "jonah":"Jonah","jon":"Jonah",
    "micah":"Micah","mic":"Micah",
    "nahum":"Nahum","nah":"Nahum",
    "habakkuk":"Habakkuk","hab":"Habakkuk",
    "zephaniah":"Zephaniah","zeph":"Zephaniah","zep":"Zephaniah",
    "haggai":"Haggai","hag":"Haggai",
    "zechariah":"Zechariah","zech":"Zechariah","zec":"Zechariah",
    "malachi":"Malachi","mal":"Malachi",
    # New Testament
    "matthew":"Gospel According to Saint Matthew","matt":"Gospel According to Saint Matthew","mt":"Gospel According to Saint Matthew",
    "mark":"Gospel According to Saint Mark","mk":"Gospel According to Saint Mark","mar":"Gospel According to Saint Mark",
    "luke":"Gospel According to Saint Luke","luk":"Gospel According to Saint Luke","lk":"Gospel According to Saint Luke",
    "john":"Gospel According to Saint John","jhn":"Gospel According to Saint John","jn":"Gospel According to Saint John",
    "acts":"Acts of the Apostles","act":"Acts of the Apostles",
    "romans":"Epistle of Paul the Apostle to the Romans","rom":"Epistle of Paul the Apostle to the Romans","rm":"Epistle of Paul the Apostle to the Romans",
    "1 corinthians":"First Epistle of Paul the Apostle to the Corinthians","1cor":"First Epistle of Paul the Apostle to the Corinthians","1 cor":"First Epistle of Paul the Apostle to the Corinthians",
    "2 corinthians":"Second Epistle of Paul the Apostle to the Corinthians","2cor":"Second Epistle of Paul the Apostle to the Corinthians","2 cor":"Second Epistle of Paul the Apostle to the Corinthians",
    "galatians":"Galatians","gal":"Galatians",
    "ephesians":"Ephesians","eph":"Ephesians",
    "philippians":"Philippians","phil":"Philippians","php":"Philippians",
    "colossians":"Colossians","col":"Colossians",
    "1 thessalonians":"First Epistle of Paul the Apostle to the Thessalonians","1thess":"First Epistle of Paul the Apostle to the Thessalonians","1 thess":"First Epistle of Paul the Apostle to the Thessalonians",
    "2 thessalonians":"Second Epistle of Paul the Apostle to the Thessalonians","2thess":"Second Epistle of Paul the Apostle to the Thessalonians","2 thess":"Second Epistle of Paul the Apostle to the Thessalonians",
    "1 timothy":"First Epistle of Paul the Apostle to Timothy","1tim":"First Epistle of Paul the Apostle to Timothy","1 tim":"First Epistle of Paul the Apostle to Timothy",
    "2 timothy":"Second Epistle of Paul the Apostle to Timothy","2tim":"Second Epistle of Paul the Apostle to Timothy","2 tim":"Second Epistle of Paul the Apostle to Timothy",
    "titus":"Titus","tit":"Titus",
    "philemon":"Philemon","phlm":"Philemon",
    "hebrews":"Hebrews","heb":"Hebrews",
    "james":"General Epistle of James","jas":"General Epistle of James","jm":"General Epistle of James",
    "1 peter":"First Epistle General of Peter","1pet":"First Epistle General of Peter","1 pet":"First Epistle General of Peter",
    "2 peter":"Second General Epistle of Peter","2pet":"Second General Epistle of Peter","2 pet":"Second General Epistle of Peter",
    "1 john":"First Epistle General of John","1jn":"First Epistle General of John","1 jn":"First Epistle General of John",
    "2 john":"Second Epistle General of John","2jn":"Second Epistle General of John","2 jn":"Second Epistle General of John",
    "3 john":"Third Epistle General of John","3jn":"Third Epistle General of John","3 jn":"Third Epistle General of John",
    "jude":"General Epistle of Jude","jud":"General Epistle of Jude",
    "revelation":"Revelation of Saint John","rev":"Revelation of Saint John","revelations":"Revelation of Saint John",
}

def parse_bible_ref(ref):
    """
    Parse references like 'Luke 2', 'Rev 21:1-8', 'John 3:16', '1 Cor 13'.
    Returns (book_key, chapter, v_start, v_end) or None.
    """
    ref = ref.strip()
    m = re.match(r'^(\d\s+\w+|\w+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$', ref, re.IGNORECASE)
    if not m:
        return None
    book_raw  = m.group(1).strip().lower()
    chapter   = int(m.group(2))
    v_start   = int(m.group(3)) if m.group(3) else None
    v_end     = int(m.group(4)) if m.group(4) else v_start
    book_key  = BIBLE_BOOKS.get(book_raw)
    if not book_key:
        return None
    return book_key, chapter, v_start, v_end


def extract_bible_passage(raw_text, book_key, chapter, v_start=None, v_end=None):
    """
    Extract a chapter or verse range from the KJV Bible raw text.
    Returns (list_of_lines, ref_label) or (None, error_msg).
    """
    lines = raw_text.splitlines()

    # Find the book content start — collect all matches, take the last one.
    # The actual book section always comes after the TOC, so last = real content.
    book_start = -1
    candidates = []
    for i, line in enumerate(lines):
        if book_key.lower() in line.lower() and len(line.strip()) < 100:
            for j in range(i + 1, min(i + 25, len(lines))):
                if re.match(r'^1:\d+', lines[j].strip()):
                    candidates.append(i)
                    break
    if candidates:
        book_start = candidates[-1]

    if book_start == -1:
        return None, f"Could not locate book in text"

    # Extract lines belonging to the requested chapter
    chapter_prefix = f"{chapter}:"
    result         = []
    in_chapter     = False
    continuation   = False   # a line with no verse number continuing previous verse

    for i in range(book_start + 1, len(lines)):
        line    = lines[i]
        stripped = line.strip()

        # Detect start of a different chapter — stop
        verse_m = re.match(r'^(\d+):(\d+)', stripped)
        if verse_m:
            c = int(verse_m.group(1))
            v = int(verse_m.group(2))
            if c == chapter:
                in_chapter  = True
                continuation = True
                if v_start is None:
                    result.append(line)
                elif v_start <= v <= (v_end if v_end else 99999):
                    result.append(line)
                elif v_end and v > v_end:
                    break
                else:
                    continuation = False
            elif in_chapter:
                break   # left the chapter
        elif in_chapter and continuation and stripped:
            # Continuation line (no verse number) — include if we're capturing
            if result:
                result.append(line)
        elif in_chapter and not stripped:
            if result:
                result.append("")  # preserve blank lines between sections

    if not result:
        label = f"{book_key.split()[-1]} {chapter}"
        if v_start:
            label += f":{v_start}" + (f"-{v_end}" if v_end and v_end != v_start else "")
        return None, f"No content found for {label}"

    # Build readable label
    book_display = book_key.split(":")[-1].strip() if ":" in book_key else book_key
    label = f"{book_display}  Chapter {chapter}"
    if v_start:
        label += f"  verses {v_start}" + (f"–{v_end}" if v_end and v_end != v_start else "")

    return result, label


def strip_ansi(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)


def find_matches(lines, term):
    """Return list of line indices (in rendered lines) that contain term."""
    t = term.lower()
    return [i for i, l in enumerate(lines) if t in strip_ansi(l).lower()]


def highlight_line(line, term):
    """Wrap matching text in reverse-video highlight."""
    plain = strip_ansi(line)
    idx   = plain.lower().find(term.lower())
    if idx == -1:
        return line
    return f"\033[7m{plain}\033[0m"


def _show_passage(raw_lines, label, tradition):
    """
    Display extracted Bible passage (list of raw text lines) in a paged viewer.
    Q/ESC returns to the book viewer.
    """
    # Render nicely: bold chapter:verse numbers, normal text
    rendered = []
    for line in raw_lines:
        if not line.strip():
            rendered.append("")
            continue
        m = re.match(r'^(\d+:\d+)\s+(.*)', line.strip())
        if m:
            rendered.append(f"  {BOLD}{GOLD}{m.group(1)}{RESET}  {m.group(2)}")
        else:
            rendered.append(f"       {line.strip()}")

    col       = trad_color(tradition)
    total     = len(rendered)
    offset    = 0

    while True:
        try:
            term_rows = os.get_terminal_size().lines - 5
        except OSError:
            term_rows = 20
        page_size = max(8, term_rows)

        clear()
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")
        print(f"{BOLD}  {label}{RESET}  {col}{DIM}[{tradition}]{RESET}")
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")

        end    = min(offset + page_size, total)
        at_end = end >= total

        for line in rendered[offset:end]:
            print(line)

        print()
        pct        = int((end / total) * 100) if total > 0 else 100
        bar_filled = int(pct / 5)
        bar        = f"{GOLD}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"

        if at_end:
            print(f"  {bar}  {DIM}{pct}%  ── END ──  Q/ESC back{RESET}")
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

    search_term    = ""
    search_matches = []   # list of line indices with a match
    search_idx     = 0    # which match we're currently at

    while True:
        clear()
        col = trad_color(book["tradition"])
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")
        print(f"{BOLD}  {book['name']}{RESET}  {col}{DIM}[{book['tradition']}]{RESET}")
        print(f"{BOLD}{GOLD}{'━' * 72}{RESET}")

        end = min(offset + page_size, total)
        for i, line in enumerate(lines[offset:end], start=offset):
            if search_term and i in search_matches:
                print(highlight_line(line, search_term))
            else:
                print(line)

        print()
        pct        = int((end / total) * 100) if total > 0 else 100
        bar_filled = int(pct / 5)
        bar        = f"{GOLD}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end     = end >= total
        toc_hint   = f"  {YELLOW}[T]{RESET}{DIM} contents{RESET}" if toc else ""

        if search_term and search_matches:
            match_info = f"  {GREEN}🔍 \"{search_term}\"  {search_idx+1}/{len(search_matches)}  n/N next/prev{RESET}"
        elif search_term:
            match_info = f"  {DIM}🔍 \"{search_term}\" — no matches{RESET}"
        else:
            match_info = ""

        nav = f"  {DIM}/ search  "
        if at_end:
            nav += f"Q/ESC back  ↑ up{RESET}"
        else:
            nav += f"Space/↓ next  ↑ up  Q/ESC back{RESET}"

        print(f"  {bar}  {DIM}{pct}%{RESET}{toc_hint}")
        print(f"{nav}{match_info}")

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
        elif key == "/":
            is_bible = "bible" in book["file"].lower() or "kjv" in book["file"].lower()
            prompt   = f"  {GOLD}Lookup (e.g. Luke 2, Rev 21:1-8) or keyword: {RESET}" if is_bible else f"  {GOLD}Search: {RESET}"
            q = input_with_esc(prompt)
            if q and q.strip():
                # Try Bible reference lookup first
                parsed = parse_bible_ref(q.strip()) if is_bible else None
                if parsed:
                    book_key, chapter, v_start, v_end = parsed
                    raw_text = book["path"].read_text(encoding="utf-8")
                    passage, label = extract_bible_passage(raw_text, book_key, chapter, v_start, v_end)
                    if passage:
                        _show_passage(passage, label, book["tradition"])
                    else:
                        # show error briefly then fall through to text search
                        search_term    = q.strip()
                        search_matches = find_matches(lines, search_term)
                        search_idx     = 0
                        if search_matches:
                            offset = max(0, min(search_matches[0] - page_size // 3, total - page_size))
                else:
                    search_term    = q.strip()
                    search_matches = find_matches(lines, search_term)
                    search_idx     = 0
                    if search_matches:
                        # jump to first match
                        offset = max(0, min(search_matches[0] - page_size // 3,
                                            total - page_size))
        elif key in ("n", "N") and search_matches:
            if key == "n":
                search_idx = (search_idx + 1) % len(search_matches)
            else:
                search_idx = (search_idx - 1) % len(search_matches)
            offset = max(0, min(search_matches[search_idx] - page_size // 3,
                                total - page_size))


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
