#!/usr/bin/env python3
"""
download-sacred-texts.py — Download major world religious texts for Jarvis archive.

Sources: Project Gutenberg (public domain) and sacred-texts.com
Texts: Bible (KJV), Quran (Pickthall), Bhagavad Gita, Dhammapada, Tao Te Ching,
       Analects of Confucius, Book of Mormon, Upanishads (13 Principal),
       Guru Granth Sahib (excerpts), Avesta (Zoroastrian)

Usage: python3 download-sacred-texts.py [all | bible | quran | gita | dhammapada |
                                          tao | analects | mormon | upanishads]
       --force   re-download even if file exists
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent
OUTPUT_DIR  = BASE_DIR / "notes" / "generated" / "sacred-texts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
}


def fetch(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    return raw.decode("latin-1")
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries}: {e}")
                time.sleep(delay)
            else:
                raise


def strip_gutenberg(text):
    """Remove Project Gutenberg header and footer boilerplate."""
    # Remove header — everything before the actual text starts
    start_markers = [
        "*** START OF THE PROJECT GUTENBERG",
        "***START OF THE PROJECT GUTENBERG",
        "*** START OF THIS PROJECT GUTENBERG",
        "END OF HEADER",
    ]
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            newline = text.find("\n", idx)
            if newline != -1:
                text = text[newline + 1:]
                break

    # Remove footer
    end_markers = [
        "*** END OF THE PROJECT GUTENBERG",
        "***END OF THE PROJECT GUTENBERG",
        "*** END OF THIS PROJECT GUTENBERG",
        "End of the Project Gutenberg",
        "End of Project Gutenberg",
    ]
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break

    return text.strip()


def save(filename, content, description=""):
    path = OUTPUT_DIR / filename
    if path.exists() and not FORCE:
        print(f"  [skip] {filename} already exists (use --force to re-download)")
        return
    path.write_text(content, encoding="utf-8")
    size_kb = len(content.encode("utf-8")) // 1024
    print(f"  [saved] {filename} ({size_kb} KB){' — ' + description if description else ''}")


# ── Individual text downloaders ────────────────────────────────────────────────

def download_bible():
    print("\n=== Bible (King James Version) ===")
    # Gutenberg #10 — complete KJV Bible
    url = "https://www.gutenberg.org/cache/epub/10/pg10.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("bible-kjv.md", f"# The Holy Bible (King James Version)\n\nSource: Project Gutenberg #10\n\n{text}")
        print("  Note: Contains Old and New Testaments — Genesis through Revelation")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_quran():
    print("\n=== Quran (Pickthall Translation) ===")
    # Gutenberg #3434 — The Meaning of the Glorious Koran by Pickthall
    url = "https://www.gutenberg.org/cache/epub/3434/pg3434.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("quran-pickthall.md", f"# The Quran (Pickthall Translation)\n\nTranslator: Marmaduke Pickthall\nSource: Project Gutenberg #3434\n\n{text}")
        print("  Note: 114 Suras — Pickthall translation considered most literal English version")
    except Exception as e:
        print(f"  ERROR: {e}")
        # Fallback: try Gutenberg mirror
        try:
            url2 = "https://gutenberg.org/files/3434/3434-0.txt"
            text = fetch(url2)
            text = strip_gutenberg(text)
            save("quran-pickthall.md", f"# The Quran (Pickthall Translation)\n\nSource: Project Gutenberg\n\n{text}")
        except Exception as e2:
            print(f"  Fallback also failed: {e2}")


def download_bhagavad_gita():
    print("\n=== Bhagavad Gita ===")
    # Gutenberg #2388 — Bhagavad Gita (Edwin Arnold translation)
    url = "https://www.gutenberg.org/cache/epub/2388/pg2388.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("bhagavad-gita.md", f"# The Bhagavad Gita\n\nTranslator: Sir Edwin Arnold (\"The Song Celestial\")\nSource: Project Gutenberg #2388\n18 Chapters — Conversation between Arjuna and Lord Krishna on the battlefield of Kurukshetra\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")
        # Fallback to Gutenberg #2654 (different translation)
        try:
            url2 = "https://www.gutenberg.org/cache/epub/2654/pg2654.txt"
            text = fetch(url2)
            text = strip_gutenberg(text)
            save("bhagavad-gita.md", f"# The Bhagavad Gita\n\nSource: Project Gutenberg\n\n{text}")
            print("  Note: Used alternate Gutenberg edition")
        except Exception as e2:
            print(f"  Fallback also failed: {e2}")


def download_dhammapada():
    print("\n=== Dhammapada (Buddhist) ===")
    # Gutenberg #2017 — The Dhammapada
    url = "https://www.gutenberg.org/cache/epub/2017/pg2017.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("dhammapada.md", f"# The Dhammapada\n\nTranslator: F. Max Müller\nSource: Project Gutenberg #2017\n423 verses in 26 chapters — core Buddhist wisdom text\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_tao_te_ching():
    print("\n=== Tao Te Ching (Taoist) ===")
    # Gutenberg #216 — Tao Te Ching
    url = "https://www.gutenberg.org/cache/epub/216/pg216.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("tao-te-ching.md", f"# Tao Te Ching\n\nAuthor: Laozi (Lao-Tse)\nTranslator: James Legge\nSource: Project Gutenberg #216\n81 chapters — foundational text of Taoism, ~5,000 Chinese characters\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_analects():
    print("\n=== Analects of Confucius ===")
    # Gutenberg #4094 — The Analects of Confucius
    url = "https://www.gutenberg.org/cache/epub/4094/pg4094.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("analects-confucius.md", f"# The Analects of Confucius\n\nTranslator: James Legge\nSource: Project Gutenberg #4094\nCore ethical and philosophical sayings of Confucius (551–479 BCE)\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_book_of_mormon():
    print("\n=== Book of Mormon (LDS) ===")
    # Gutenberg #17 — Book of Mormon
    url = "https://www.gutenberg.org/cache/epub/17/pg17.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("book-of-mormon.md", f"# The Book of Mormon\n\nSource: Project Gutenberg #17\nLDS scripture — \"Another Testament of Jesus Christ\" (Joseph Smith, 1830)\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")
        try:
            url2 = "https://gutenberg.org/files/17/17-0.txt"
            text = fetch(url2)
            text = strip_gutenberg(text)
            save("book-of-mormon.md", f"# The Book of Mormon\n\nSource: Project Gutenberg\n\n{text}")
        except Exception as e2:
            print(f"  Fallback also failed: {e2}")


def download_upanishads():
    print("\n=== Upanishads (Hindu philosophical texts) ===")
    # Gutenberg #3283 — The Upanishads (Parts 1 and 2)
    urls = [
        ("https://www.gutenberg.org/cache/epub/3283/pg3283.txt", "Part 1"),
        ("https://www.gutenberg.org/cache/epub/3284/pg3284.txt", "Part 2"),
    ]
    combined = "# The Upanishads\n\nTranslator: F. Max Müller\nSource: Project Gutenberg #3283, #3284\nPhilosophical core of Vedic thought — concepts of Brahman, Atman, moksha\n\n"
    success = False
    for url, label in urls:
        try:
            text = fetch(url)
            text = strip_gutenberg(text)
            combined += f"\n\n## {label}\n\n{text}"
            success = True
            print(f"  Downloaded {label}")
            time.sleep(1)
        except Exception as e:
            print(f"  ERROR ({label}): {e}")
    if success:
        save("upanishads.md", combined)


def download_rigveda():
    print("\n=== Rig Veda ===")
    # Gutenberg #12220 — Rig Veda (Ralph Griffith translation)
    url = "https://www.gutenberg.org/cache/epub/12220/pg12220.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("rig-veda.md", f"# Rig Veda\n\nTranslator: Ralph T.H. Griffith\nSource: Project Gutenberg #12220\nOldest known religious text still in use — 1,028 hymns in 10 books\nComposed ~1500–1200 BCE in northwest India\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_avesta():
    print("\n=== Avesta (Zoroastrian) ===")
    # Gutenberg #1135 — Avesta: The Religious Books of the Parsees
    url = "https://www.gutenberg.org/cache/epub/1135/pg1135.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        save("avesta-zoroastrian.md", f"# The Avesta — Zoroastrian Sacred Texts\n\nTranslator: Arthur Henry Bleeck\nSource: Project Gutenberg #1135\nScriptures of Zoroastrianism — oldest surviving Indo-European religious texts\nFoundation that influenced Judaism, Christianity, and Islam\n\n{text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def download_gospel_of_thomas():
    print("\n=== Gospel of Thomas (Gnostic/Apocryphal) ===")
    # This isn't on Gutenberg but worth having — 114 sayings of Jesus not in canonical Gospels
    # Write a concise reference version
    content = """# Gospel of Thomas

Source: Nag Hammadi Library (discovered 1945, Egypt)
Status: Gnostic text; not in the canonical Bible; considered apocryphal by most Christians
Date: ~150 CE (possibly earlier oral tradition)
Contents: 114 sayings attributed to Jesus, no narrative — just quotes
Significance: Oldest collection of Jesus sayings; predates or parallels synoptic Gospels

## Context
The Gospel of Thomas was found among the Nag Hammadi codices in Egypt in 1945.
It is a Coptic translation of what scholars believe was a Greek original.
Unlike the canonical Gospels, it contains no birth narrative, no miracles, no crucifixion story
— only 114 sayings attributed to Jesus, presented as secret wisdom.

## Selected Sayings

**Saying 1:** "Whoever discovers the interpretation of these sayings will not taste death."

**Saying 3:** "If your leaders say to you, 'Look, the kingdom is in the sky,' then the birds of the sky will precede you. If they say to you, 'It is in the sea,' then the fish will precede you. Rather, the kingdom is within you and it is outside you."

**Saying 5:** "Know what is in front of your face, and what is hidden from you will be disclosed to you."

**Saying 14:** "If you fast, you will bring sin upon yourselves, and if you pray, you will be condemned, and if you give to charity, you will harm your spirits."

**Saying 22:** Jesus said, "When you make the two into one, and when you make the inner like the outer and the outer like the inner... then you will enter the kingdom."

**Saying 77:** "I am the light that is over all things. I am all: from me all came forth, and to me all attained. Split a piece of wood; I am there. Lift up the stone, and you will find me there."

**Saying 113:** His disciples said to him, "When will the kingdom come?" "It will not come by watching for it. It will not be said, 'Look, here!' or 'Look, there!' Rather, the Father's kingdom is spread out upon the earth, and people don't see it."

## Scholarly Significance
The Gospel of Thomas is the subject of intense academic debate:
- Some scholars (Jesus Seminar) believe it preserves authentic sayings of Jesus
- Others believe it is a 2nd-century Gnostic composition
- It is not considered scripture by Catholics, Protestants, or Eastern Orthodox
- It is studied as a historical document about early Christianity
"""
    save("gospel-of-thomas.md", content, "Gnostic text from Nag Hammadi")


def download_dead_sea_scrolls_overview():
    print("\n=== Dead Sea Scrolls Overview ===")
    content = """# Dead Sea Scrolls

## Discovery
Found 1947–1956 in 11 caves near Qumran, Dead Sea, Jordan (then-Jordan, now West Bank)
Discovered by a Bedouin shepherd boy who threw a rock into a cave and heard pottery break
~900 manuscripts, mostly in Hebrew and Aramaic, dating from 3rd century BCE to 1st century CE

## Significance
- Oldest known manuscripts of the Hebrew Bible — 1,000 years older than previous oldest copies
- Confirmed remarkable accuracy of later copies of the Old Testament
- Revealed existence of a Jewish sect (likely Essenes) living ascetically near the Dead Sea
- Contain previously unknown religious texts

## Contents
- **Biblical texts**: Every book of the Hebrew Bible except Esther
- **Isaiah Scroll**: Complete book of Isaiah — 1,000 years older than previous oldest copy; nearly identical to modern text
- **Copper Scroll**: Describes hidden treasures at 64 locations (never found)
- **Community Rule (Manual of Discipline)**: Rules for a Jewish communal sect — foreshadows monastic traditions
- **War Scroll**: Describes a 40-year apocalyptic war between "Sons of Light" and "Sons of Darkness"
- **Temple Scroll**: Longest Dead Sea Scroll (~8m); describes an idealized Temple and its laws
- **Damascus Document**: Rules for a Jewish community "in the land of Damascus"

## The Essene Theory
Most scholars believe the scrolls belonged to the Essenes — a Jewish sect that:
- Rejected the Temple establishment in Jerusalem
- Lived communally and celibately
- Practiced ritual purity and communal meals
- Expected an imminent apocalypse
- Some scholars see parallels to early Christianity

## Status Today
- Housed at the Shrine of the Book, Israel Museum, Jerusalem
- High-resolution digital images available online since 2012
- Israel Antiquities Authority digitized entire collection
- Jordan and Palestinians dispute Israeli custody

## Impact on Biblical Scholarship
The scrolls largely confirmed that the Bible we have today was faithfully transmitted.
Minor variations exist but no major theological differences.
The scrolls also showed that Judaism in the 1st century BCE was far more diverse than previously thought.
"""
    save("dead-sea-scrolls.md", content, "Historical overview of the Dead Sea Scrolls")


# ── Dispatch ──────────────────────────────────────────────────────────────────

ALL_TEXTS = {
    "bible":        download_bible,
    "quran":        download_quran,
    "gita":         download_bhagavad_gita,
    "dhammapada":   download_dhammapada,
    "tao":          download_tao_te_ching,
    "analects":     download_analects,
    "mormon":       download_book_of_mormon,
    "upanishads":   download_upanishads,
    "rigveda":      download_rigveda,
    "avesta":       download_avesta,
    "thomas":       download_gospel_of_thomas,
    "deadseascrolls": download_dead_sea_scrolls_overview,
}

# Filter out flags and known args
args = [a for a in sys.argv[1:] if not a.startswith("--")]
targets = args if args else ["all"]

if "all" in targets:
    targets = list(ALL_TEXTS.keys())

print(f"Sacred Texts Downloader — {len(targets)} text(s) to process")
print(f"Output: {OUTPUT_DIR}")

for target in targets:
    if target in ALL_TEXTS:
        try:
            ALL_TEXTS[target]()
            time.sleep(1.5)  # be polite to Gutenberg servers
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(0)
    else:
        print(f"Unknown target: {target}. Options: {', '.join(ALL_TEXTS.keys())} or 'all'")

print(f"\nDone. Files saved to: {OUTPUT_DIR}")
print("Run 'rebuild index' in Jarvis chat to make texts searchable.")
