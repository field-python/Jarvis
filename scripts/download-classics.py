#!/usr/bin/env python3
"""
download-classics.py — Download classic literature from Project Gutenberg.
Run: ~/.jarvis-venv/bin/python scripts/download-classics.py
"""
import urllib.request
import re
import sys
import time
from pathlib import Path

base_dir = Path(__file__).parent.parent
out_dir  = base_dir / "notes" / "generated" / "classics"
out_dir.mkdir(parents=True, exist_ok=True)

BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
GOLD  = "\033[93m"
RED   = "\033[91m"
DIM   = "\033[2m"
RESET = "\033[0m"

# (display_name, author, year, genre, gutenberg_id, filename)
BOOKS = [
    # Jules Verne
    ("The Mysterious Island",             "Jules Verne",          1875, "Adventure",  1268,  "mysterious-island.md"),
    ("Twenty Thousand Leagues Under the Sea", "Jules Verne",      1870, "Adventure",  164,   "20000-leagues.md"),
    ("Journey to the Center of the Earth","Jules Verne",          1864, "Adventure",  3748,  "journey-center-earth.md"),
    ("Around the World in Eighty Days",   "Jules Verne",          1872, "Adventure",  103,   "around-world-80-days.md"),
    # H.G. Wells
    ("The Time Machine",                  "H.G. Wells",           1895, "Sci-Fi",     35,    "time-machine.md"),
    ("The War of the Worlds",             "H.G. Wells",           1898, "Sci-Fi",     36,    "war-of-the-worlds.md"),
    ("The Invisible Man",                 "H.G. Wells",           1897, "Sci-Fi",     5230,  "invisible-man-wells.md"),
    # Arthur Conan Doyle
    ("The Adventures of Sherlock Holmes", "Arthur Conan Doyle",   1892, "Mystery",    1661,  "sherlock-holmes-adventures.md"),
    ("The Hound of the Baskervilles",     "Arthur Conan Doyle",   1902, "Mystery",    2852,  "hound-of-baskervilles.md"),
    # Mark Twain
    ("Adventures of Huckleberry Finn",    "Mark Twain",           1884, "Adventure",  76,    "huckleberry-finn.md"),
    ("The Adventures of Tom Sawyer",      "Mark Twain",           1876, "Adventure",  74,    "tom-sawyer.md"),
    # Jack London
    ("The Call of the Wild",              "Jack London",          1903, "Adventure",  215,   "call-of-the-wild.md"),
    ("White Fang",                        "Jack London",          1906, "Adventure",  910,   "white-fang.md"),
    # Gothic / Horror
    ("Frankenstein",                      "Mary Shelley",         1818, "Gothic",     84,    "frankenstein.md"),
    ("Dracula",                           "Bram Stoker",          1897, "Gothic",     345,   "dracula.md"),
    ("The Picture of Dorian Gray",        "Oscar Wilde",          1890, "Gothic",     174,   "dorian-gray.md"),
    ("Strange Case of Dr Jekyll and Mr Hyde", "R.L. Stevenson",   1886, "Gothic",     43,    "jekyll-and-hyde.md"),
    # Robert Louis Stevenson
    ("Treasure Island",                   "R.L. Stevenson",       1883, "Adventure",  120,   "treasure-island.md"),
    # Charles Dickens
    ("A Tale of Two Cities",              "Charles Dickens",      1859, "Historical", 98,    "tale-of-two-cities.md"),
    ("Great Expectations",                "Charles Dickens",      1861, "Classic",    1400,  "great-expectations.md"),
    # Jane Austen
    ("Pride and Prejudice",               "Jane Austen",          1813, "Romance",    1342,  "pride-and-prejudice.md"),
    # Herman Melville
    ("Moby-Dick",                         "Herman Melville",      1851, "Adventure",  2701,  "moby-dick.md"),
    # Joseph Conrad
    ("Heart of Darkness",                 "Joseph Conrad",        1899, "Classic",    219,   "heart-of-darkness.md"),
    # Edgar Allan Poe
    ("The Works of Edgar Allan Poe Vol 1","Edgar Allan Poe",      1845, "Gothic",     2147,  "poe-works-vol1.md"),
    # Alexandre Dumas
    ("The Count of Monte Cristo",         "Alexandre Dumas",      1844, "Adventure",  1184,  "count-of-monte-cristo.md"),
    # Daniel Defoe
    ("Robinson Crusoe",                   "Daniel Defoe",         1719, "Adventure",  521,   "robinson-crusoe.md"),
    # Philosophy / Strategy
    ("The Art of War",                    "Sun Tzu",              500,  "Philosophy", 132,   "art-of-war.md"),
    ("The Prince",                        "Niccolò Machiavelli",  1532, "Philosophy", 1232,  "the-prince.md"),
    # Epic / Poetry
    ("The Odyssey",                       "Homer",                800,  "Epic",       1727,  "odyssey.md"),
    ("The Iliad",                         "Homer",                762,  "Epic",       6130,  "iliad.md"),
    # Dostoevsky
    ("Crime and Punishment",              "Fyodor Dostoevsky",    1866, "Classic",    2554,  "crime-and-punishment.md"),
    # Shakespeare
    ("Hamlet",                            "William Shakespeare",  1603, "Drama",      1524,  "hamlet.md"),
    ("Romeo and Juliet",                  "William Shakespeare",  1597, "Drama",      1513,  "romeo-and-juliet.md"),
]


def fetch(pg_id):
    """Try common Gutenberg URL patterns, return raw text or None."""
    patterns = [
        f"https://www.gutenberg.org/files/{pg_id}/{pg_id}-0.txt",
        f"https://www.gutenberg.org/files/{pg_id}/{pg_id}.txt",
        f"https://www.gutenberg.org/ebooks/{pg_id}.txt.utf-8",
    ]
    for url in patterns:
        try:
            req = urllib.request.urlopen(url, timeout=25)
            return req.read().decode("utf-8", errors="replace")
        except Exception:
            continue
    return None


def strip_gutenberg(text):
    """Remove Gutenberg header and footer boilerplate."""
    start_markers = ["*** START OF THE PROJECT GUTENBERG", "***START OF THE PROJECT GUTENBERG",
                     "** START OF THIS PROJECT GUTENBERG"]
    end_markers   = ["*** END OF THE PROJECT GUTENBERG", "***END OF THE PROJECT GUTENBERG",
                     "** END OF THIS PROJECT GUTENBERG"]
    for m in start_markers:
        idx = text.find(m)
        if idx != -1:
            text = text[text.find("\n", idx) + 1:]
            break
    for m in end_markers:
        idx = text.find(m)
        if idx != -1:
            text = text[:idx]
            break
    return text.strip()


def to_markdown(text, title, author, year, genre):
    """Convert plain Gutenberg text to a clean .md file."""
    lines = [
        f"# {title}",
        f"author: {author}",
        f"year: {year}",
        f"genre: {genre}",
        "",
        f"> *{title}* by {author} ({year})",
        "",
    ]
    for line in text.splitlines():
        s = line.strip()
        # ALL CAPS short lines → section headers
        if s and s == s.upper() and 3 < len(s) < 72 and not s.startswith("_"):
            lines.append(f"\n## {s.title()}\n")
        elif s:
            lines.append(s)
        else:
            lines.append("")
    return "\n".join(lines)


def main():
    targets = sys.argv[1:]  # optional: filter by filename slug

    ok, fail = 0, 0
    for title, author, year, genre, pg_id, fname in BOOKS:
        if targets and not any(t in fname for t in targets):
            continue
        out_file = out_dir / fname
        if out_file.exists():
            print(f"  {DIM}skip (exists): {title}{RESET}")
            ok += 1
            continue

        print(f"  {CYAN}Fetching [{pg_id}] {title}...{RESET}", end=" ", flush=True)
        raw = fetch(pg_id)
        if not raw:
            print(f"{RED}FAILED{RESET}")
            fail += 1
            continue

        clean = strip_gutenberg(raw)
        md    = to_markdown(clean, title, author, year, genre)
        out_file.write_text(md, encoding="utf-8")
        size  = out_file.stat().st_size // 1000
        print(f"{GREEN}✓  ({size} KB){RESET}")
        ok += 1
        time.sleep(0.4)

    print(f"\n{BOLD}{GREEN}Done — {ok} books saved, {fail} failed.{RESET}")
    print(f"{DIM}Run: Jarvis rebuild-index   to add to semantic search{RESET}\n")


if __name__ == "__main__":
    main()
