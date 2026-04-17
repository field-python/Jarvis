#!/usr/bin/env python3
"""
download-holybooks.py — Download Torah (Sefaria JPS) and Kybalion (Gutenberg).
Run: ~/.jarvis-venv/bin/python scripts/download-holybooks.py
"""
import urllib.request
import json
import re
import sys
import time
from pathlib import Path

base_dir  = Path(__file__).parent.parent
out_dir   = base_dir / "notes" / "generated" / "sacred-texts"
out_dir.mkdir(parents=True, exist_ok=True)

BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
GOLD  = "\033[93m"
DIM   = "\033[2m"
RESET = "\033[0m"


def strip_html(text):
    """Remove HTML tags and decode common entities."""
    # Remove footnote markers and their content: <sup ...><i ...>...</i></sup>
    text = re.sub(r'<sup[^>]*>.*?</sup>', '', text, flags=re.DOTALL)
    text = re.sub(r'<i[^>]*>.*?</i>', '', text, flags=re.DOTALL)
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    return text.strip()


def fetch(url, retries=3, delay=1.5):
    for attempt in range(retries):
        try:
            req = urllib.request.urlopen(url, timeout=20)
            return req.read()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


# ── Torah via Sefaria ─────────────────────────────────────────────────────────

TORAH_BOOKS = [
    ("Genesis",     "Bereshit",  50),
    ("Exodus",      "Shemot",    40),
    ("Leviticus",   "Vayikra",   27),
    ("Numbers",     "Bamidbar",  36),
    ("Deuteronomy", "Devarim",   34),
]


def download_torah():
    print(f"\n{BOLD}{GOLD}Downloading Torah (JPS Translation via Sefaria)...{RESET}\n")
    out_file = out_dir / "torah-jps.md"

    lines = [
        "# Torah — The Five Books of Moses",
        "category: Judaism",
        "tags: Torah, Pentateuch, Hebrew Bible, JPS, Moses, Old Testament",
        "",
        "> Jewish Publication Society Translation (JPS), via Sefaria.",
        "> The five books of Moses: Genesis, Exodus, Leviticus, Numbers, Deuteronomy.",
        "",
    ]

    for book_en, book_he, num_chapters in TORAH_BOOKS:
        print(f"  {CYAN}Fetching {book_en} ({num_chapters} chapters)...{RESET}", flush=True)
        lines.append(f"\n## {book_en} ({book_he})\n")

        for ch in range(1, num_chapters + 1):
            url = f"https://www.sefaria.org/api/texts/{book_en}.{ch}?lang=en&context=0"
            try:
                raw  = fetch(url)
                data = json.loads(raw)
                text = data.get("text", [])
                if not isinstance(text, list):
                    text = [text]
                lines.append(f"\n### Chapter {ch}\n")
                for v_num, verse in enumerate(text, 1):
                    if isinstance(verse, list):
                        verse = " ".join(verse)
                    verse = strip_html(str(verse))
                    if verse:
                        lines.append(f"**{ch}:{v_num}** {verse}")
                time.sleep(0.3)
            except Exception as e:
                print(f"    {DIM}Warning: chapter {ch} failed — {e}{RESET}")
                lines.append(f"\n*[Chapter {ch} unavailable]*\n")

        print(f"  {GREEN}✓ {book_en} done{RESET}")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    size_mb = out_file.stat().st_size / 1_000_000
    print(f"\n{GREEN}Torah saved → {out_file.name}  ({size_mb:.1f} MB){RESET}")


# ── Kybalion via Project Gutenberg ───────────────────────────────────────────

def download_kybalion():
    print(f"\n{BOLD}{GOLD}Downloading The Kybalion (Gutenberg #14209)...{RESET}")
    out_file = out_dir / "kybalion.md"
    url      = "https://www.gutenberg.org/ebooks/14209.txt.utf-8"

    raw  = fetch(url).decode("utf-8", errors="replace")

    # Strip Gutenberg header/footer
    start = raw.find("*** START OF THE PROJECT GUTENBERG")
    end   = raw.find("*** END OF THE PROJECT GUTENBERG")
    if start != -1:
        raw = raw[raw.find("\n", start) + 1:]
    if end != -1:
        raw = raw[:end]

    # Convert to markdown-ish format
    converted = [
        "# The Kybalion",
        "category: Hermetic",
        "tags: Kybalion, Hermeticism, Hermetic philosophy, Three Initiates, occult, alchemy, ancient Egypt",
        "",
        "> *The Kybalion* (1908) by Three Initiates.",
        "> A study of the Hermetic Philosophy of Ancient Egypt and Greece.",
        "",
    ]

    for line in raw.splitlines():
        stripped = line.strip()
        # All-caps lines are likely chapter/section headers
        if stripped and stripped == stripped.upper() and len(stripped) > 4 and len(stripped) < 80:
            converted.append(f"\n## {stripped.title()}\n")
        elif stripped:
            converted.append(stripped)
        else:
            converted.append("")

    out_file.write_text("\n".join(converted), encoding="utf-8")
    size_kb = out_file.stat().st_size / 1000
    print(f"{GREEN}Kybalion saved → {out_file.name}  ({size_kb:.0f} KB){RESET}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or "torah" in args:
        download_torah()
    if not args or "kybalion" in args:
        download_kybalion()

    print(f"\n{BOLD}{GREEN}Done.{RESET}")
    print(f"{DIM}Run: Jarvis rebuild-index   (to add to semantic search){RESET}\n")


if __name__ == "__main__":
    main()
