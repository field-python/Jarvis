#!/usr/bin/env python3
"""
download-sacred-texts-extended.py — Ethiopian Bible, Babylonian Talmud, Guru Granth Sahib

Sources:
  - Project Gutenberg (Book of Enoch, Jubilees, Guru Granth Sahib)
  - Sefaria.org API (Babylonian Talmud tractates — free, clean JSON)

Usage: python3 download-sacred-texts-extended.py [all | enoch | jubilees | granth | talmud]
       --force   re-download even if file exists
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "notes" / "generated" / "sacred-texts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"}


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
                time.sleep(delay)
            else:
                raise


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise


def strip_gutenberg(text):
    for marker in ["*** START OF THE PROJECT GUTENBERG", "***START OF THE PROJECT GUTENBERG",
                   "*** START OF THIS PROJECT GUTENBERG", "END OF HEADER"]:
        idx = text.find(marker)
        if idx != -1:
            nl = text.find("\n", idx)
            if nl != -1:
                text = text[nl + 1:]
                break
    for marker in ["*** END OF THE PROJECT GUTENBERG", "***END OF THE PROJECT GUTENBERG",
                   "*** END OF THIS PROJECT GUTENBERG", "End of the Project Gutenberg",
                   "End of Project Gutenberg"]:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    return text.strip()


def save(filename, content):
    path = OUTPUT_DIR / filename
    if path.exists() and not FORCE:
        print(f"  [skip] {filename} (use --force to re-download)")
        return
    path.write_text(content, encoding="utf-8")
    size_kb = len(content.encode("utf-8")) // 1024
    print(f"  [saved] {filename} ({size_kb} KB)")


# ── Book of Enoch ──────────────────────────────────────────────────────────────

def download_book_of_enoch():
    print("\n=== Book of Enoch (Ethiopian Canon) ===")
    print("  The Book of Enoch is in the Ethiopian Orthodox Bible but not in Western canons.")
    print("  It is quoted in the New Testament (Jude 1:14-15) and was hugely influential.")
    url = "https://www.gutenberg.org/cache/epub/1948/pg1948.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        header = """# The Book of Enoch (1 Enoch)

## Status
- Canonical in: Ethiopian Orthodox Tewahedo Church, Eritrean Orthodox Church
- Not canonical in: Catholic, Protestant, Eastern Orthodox churches
- Found among: Dead Sea Scrolls (fragments of all sections)
- Quoted in the New Testament: Jude 1:14-15 directly quotes Enoch 1:9

## Significance
The Book of Enoch is one of the most important Jewish texts outside the Hebrew Bible.
It describes the Watchers (fallen angels) who mated with human women to produce giants (Nephilim),
Enoch's heavenly journey and vision of God, astronomical and calendar teachings,
the coming of a Messiah ("Son of Man"), and final judgment.
It was hugely influential on early Christianity and Second Temple Judaism.
The complete Ethiopic text was unknown in Europe until James Bruce brought manuscripts from Ethiopia in 1773.

## Contents
- **Book of the Watchers** (ch. 1-36): Angels fall, mate with women, produce Nephilim
- **Book of Parables** (ch. 37-71): Messianic "Son of Man" — possible influence on Jesus's self-title
- **Astronomical Book** (ch. 72-82): Solar/lunar calendar; 364-day year
- **Book of Dream Visions** (ch. 83-90): History of Israel as animal allegory
- **Epistle of Enoch** (ch. 91-108): Judgment of sinners, blessings for righteous

## Translator
R.H. Charles (1906) — standard scholarly English translation

---

"""
        save("book-of-enoch.md", header + text)
    except Exception as e:
        print(f"  ERROR: {e}")


# ── Book of Jubilees ───────────────────────────────────────────────────────────

def download_book_of_jubilees():
    print("\n=== Book of Jubilees (Ethiopian Canon) ===")
    url = "https://www.gutenberg.org/cache/epub/8077/pg8077.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        header = """# The Book of Jubilees

## Status
- Canonical in: Ethiopian Orthodox Tewahedo Church
- Not canonical in: Catholic, Protestant, Eastern Orthodox churches
- Also known as: "The Little Genesis" or "The Apocalypse of Moses"
- Found among: Dead Sea Scrolls (15+ fragments)

## Significance
Jubilees retells Genesis and part of Exodus with additional details not in the Bible.
It organizes history into 49-year "jubilee" periods.
It explains the origin of many religious laws and provides dates for biblical events.
It is one of the most important texts for understanding Second Temple Judaism.

## Contents
- Retelling of Creation through the Exodus
- Additional stories about patriarchs (Adam, Noah, Abraham, Jacob)
- Origin of demonic beings (Mastema/Satan)
- Strict solar calendar (364 days) — same as Dead Sea Scrolls community
- Explanation of Jewish festivals and their heavenly origins
- Angels writing down human deeds

---

"""
        save("book-of-jubilees.md", header + text)
    except Exception as e:
        print(f"  ERROR: {e}")


# ── Guru Granth Sahib ──────────────────────────────────────────────────────────

def download_guru_granth_sahib():
    print("\n=== Guru Granth Sahib (Sikh Scripture) ===")
    url = "https://www.gutenberg.org/cache/epub/58069/pg58069.txt"
    try:
        text = fetch(url)
        text = strip_gutenberg(text)
        header = """# Sri Guru Granth Sahib

## Status
- Primary scripture and eternal living Guru of Sikhism
- 1,430 pages; 5,894 hymns (shabads)
- Written in Gurmukhi script; composed in multiple languages (Punjabi, Hindi, Sanskrit, Persian, Arabic)

## Significance
The Guru Granth Sahib was declared the eternal Guru of the Sikhs in 1708 by the 10th human Guru,
Gobind Singh, who said there would be no more human Gurus — the scripture itself would be the Guru.
It contains writings by 6 of the 10 Sikh Gurus, plus hymns by Hindu and Muslim saints,
reflecting Sikhism's core belief that God's truth is not limited to one religion.

## Contributors
- Guru Nanak Dev Ji (founder) — ~974 hymns
- Guru Angad Dev Ji, Guru Amar Das Ji, Guru Ram Das Ji, Guru Arjan Dev Ji, Guru Tegh Bahadur Ji
- Hindu bhakti saints: Kabir, Ravidas, Namdev, and others
- Muslim Sufi saints: Sheikh Farid
Total: 36 contributors

## Structure
Organized by musical measure (raga) rather than chronologically.
Each section specifies the raga in which it should be sung.
Begins with the Mul Mantar (Root Mantra) — fundamental statement of belief:
"Ik Onkar" (There is one God) — the first words of the scripture.

## Key Teachings
- One God (Ik Onkar) — formless, eternal, without fear or enmity
- Equality of all humans — no caste, no gender hierarchy
- Service to community (seva) as spiritual practice
- Honest work, sharing with others, remembering God
- Rejection of empty ritual, idol worship, caste discrimination

## Source
Project Gutenberg #58069 — English translation

---

"""
        save("guru-granth-sahib.md", header + text)
    except Exception as e:
        print(f"  ERROR: {e}")


# ── Babylonian Talmud via Sefaria API ──────────────────────────────────────────

# Key tractates — most important and widely referenced
TALMUD_TRACTATES = [
    # Tractate name (Sefaria ref), English name, category
    ("Pirkei_Avot",          "Pirkei Avot (Ethics of the Fathers)",   "Ethics — most widely read; wisdom sayings of the rabbis"),
    ("Mishnah_Berakhot",     "Berakhot (Blessings)",                  "Daily prayers and blessings — first tractate of the Mishnah"),
    ("Mishnah_Shabbat",      "Shabbat (Sabbath)",                     "Sabbath laws — 39 prohibited categories of work"),
    ("Mishnah_Sanhedrin",    "Sanhedrin (Court)",                     "Criminal law, capital punishment, messianic era"),
    ("Mishnah_Avodah_Zarah", "Avodah Zarah (Idolatry)",              "Laws about non-Jewish worship and commerce"),
    ("Mishnah_Kiddushin",    "Kiddushin (Betrothal)",                 "Marriage laws and conversion"),
    ("Mishnah_Bava_Kamma",   "Bava Kamma (First Gate)",              "Civil damages — property law, torts"),
    ("Mishnah_Bava_Metzia",  "Bava Metzia (Middle Gate)",            "Civil law — lost property, wages, interest"),
    ("Mishnah_Bava_Batra",   "Bava Batra (Last Gate)",               "Property rights, inheritance, commerce"),
    ("Mishnah_Pesachim",     "Pesachim (Passover)",                  "Passover laws and the Seder"),
    ("Mishnah_Yoma",         "Yoma (The Day)",                       "Yom Kippur / Day of Atonement rituals"),
    ("Mishnah_Rosh_Hashanah","Rosh Hashanah (New Year)",             "Jewish New Year laws and the shofar"),
    ("Mishnah_Megillah",     "Megillah (Scroll)",                    "Purim, public Torah reading, synagogue laws"),
    ("Mishnah_Sotah",        "Sotah (Wayward Wife)",                 "Suspected adultery ordeal; also includes famous passages on humility"),
    ("Mishnah_Gittin",       "Gittin (Divorce Documents)",           "Divorce law; includes story of Jerusalem's destruction"),
    ("Mishnah_Nedarim",      "Nedarim (Vows)",                       "Laws of vows and oaths"),
    ("Mishnah_Nazir",        "Nazir (Nazirite)",                     "Nazirite vow — no wine, no haircuts, no corpse contact"),
]


def flatten_text(obj):
    """Recursively flatten nested lists of strings into a single string."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list):
        parts = []
        for item in obj:
            part = flatten_text(item)
            if part:
                parts.append(part)
        return "\n".join(parts)
    return ""


def download_talmud():
    print("\n=== Babylonian Talmud / Mishnah (via Sefaria.org API) ===")
    print(f"  Downloading {len(TALMUD_TRACTATES)} key tractates...")

    all_content = """# The Babylonian Talmud and Mishnah — Key Tractates

## What Is the Talmud?
The Talmud is the central text of Rabbinic Judaism and the primary source of Jewish religious law.
It consists of:
- **Mishnah** — the first written compilation of Jewish oral law, edited ~200 CE by Rabbi Judah the Prince
- **Gemara** — rabbinic discussion and analysis of the Mishnah; Babylonian version edited ~500 CE

The Babylonian Talmud (Talmud Bavli) is the more authoritative and complete version.
The Jerusalem Talmud (Talmud Yerushalmi) is shorter and less studied.

## Structure
- 6 orders (Sedarim), 63 tractates, ~2,700 pages of Mishnah, ~6,200 pages of Talmud
- Topics: agriculture, Sabbath, holidays, marriage, divorce, civil law, criminal law, temple ritual, purity
- Not just law — includes stories (aggadah), medical advice, astronomy, folklore, philosophy

## This Collection
Key tractates from the Mishnah — the core legal text.
Source: Sefaria.org (public domain translations)
Full Talmud available at: https://www.sefaria.org/texts/Talmud

---

"""

    for ref, name, description in TALMUD_TRACTATES:
        print(f"  Fetching: {name}...")
        url = f"https://www.sefaria.org/api/texts/{ref}?lang=en&context=0&pad=0"
        try:
            data = fetch_json(url)
            raw_text = flatten_text(data.get("text", []))

            if not raw_text.strip():
                print(f"  [empty] {name}")
                continue

            all_content += f"\n\n{'='*60}\n## {name}\n_{description}_\n\n{raw_text}\n"
            print(f"  [ok] {name} — {len(raw_text)} chars")
            time.sleep(0.5)  # be polite to Sefaria
        except Exception as e:
            print(f"  [error] {name}: {e}")
            time.sleep(1)

    save("talmud-mishnah-key-tractates.md", all_content)

    # Also download Pirkei Avot separately — it's the most widely read
    print("\n  Also saving Pirkei Avot as standalone file...")
    try:
        url = "https://www.sefaria.org/api/texts/Pirkei_Avot?lang=en&context=0&pad=0"
        data = fetch_json(url)
        avot_text = flatten_text(data.get("text", []))
        avot_content = """# Pirkei Avot — Ethics of the Fathers

The most widely read tractate of the Mishnah.
Pure ethical and wisdom teachings of the rabbis — no legal rulings.
Studied on Shabbat afternoons between Passover and Rosh Hashanah.
Source: Sefaria.org

---

""" + avot_text
        save("pirkei-avot-ethics-of-fathers.md", avot_content)
    except Exception as e:
        print(f"  Pirkei Avot standalone failed: {e}")


# ── Ethiopian Bible overview ───────────────────────────────────────────────────

def write_ethiopian_bible_overview():
    print("\n=== Ethiopian Bible Overview ===")
    content = """# Ethiopian Orthodox Bible — Overview

## The Broadest Canon in Christianity

The Ethiopian Orthodox Tewahedo Church has the largest biblical canon of any Christian denomination.
**81 books** in the Old Testament vs 39 (Protestant), 46 (Catholic), 51 (Eastern Orthodox).

The word "Tewahedo" means "made one" (unity of Christ's nature) — a theological distincton from Rome.
This church traces its roots to the 4th century CE and is one of the oldest Christian churches in the world.

## Books in the Ethiopian Canon NOT in the Protestant Bible

### Deuterocanonical Books (also in Catholic Bible)
- Tobit, Judith, 1 Maccabees, 2 Maccabees
- Wisdom of Solomon, Sirach (Ecclesiasticus), Baruch
- Additional chapters of Daniel (Susanna, Bel and the Dragon)
- Additional chapters of Esther

### Books Unique to Ethiopian Canon
| Book | Contents |
|------|----------|
| **1 Enoch (Book of Enoch)** | Angels, Watchers, Nephilim, heavenly journeys, Son of Man |
| **Book of Jubilees** | Retelling of Genesis; origins of religious law; solar calendar |
| **1 Meqabyan** | Ethiopian "Maccabees" — completely different from Catholic Maccabees |
| **2 Meqabyan** | Continuation |
| **3 Meqabyan** | Continuation |
| **Sirate Tsion** | "Law of Zion" — rules for church practice |
| **Tigaba Tsion** | "Covenant of Zion" |
| **Abba Giyorgis (Te'amer)** | Hymns |
| **Psalms of Solomon** | 18 psalms not in Hebrew Bible |
| **Prayer of Manasseh** | King Manasseh's prayer of repentance |
| **4 Baruch (Paralipomena of Jeremiah)** | Events after fall of Jerusalem |

### New Testament Additions
The Ethiopian NT also includes:
- **Sinodos** — 4-part church order document
- **Clement** — Ethiopian version of 1 Clement
- **Didascalia** — early church teaching document
- **Book of the Covenant** (Mets'hafe Kidan) — 2 parts

## The Ark of the Covenant (Ethiopian Claim)
Ethiopia claims to possess the original Ark of the Covenant in Axum.
The Ark is said to have been brought to Ethiopia by Menelik I, son of Solomon and the Queen of Sheba.
It is kept in the Church of Our Lady Mary of Zion; only one monk (the Guardian) is allowed to see it.
No independent verification has been permitted; claim remains unverified but significant culturally.

## Ethiopian Bible Texts in This Archive
- **Book of Enoch** — see `book-of-enoch.md`
- **Book of Jubilees** — see `book-of-jubilees.md`
- **Standard Bible (KJV)** — see `bible-kjv.md` (includes Protestant canon)

## Historical Significance
- Ethiopian Christianity predates European Christianity becoming mainstream
- The Ethiopian church preserved the Book of Enoch when it was lost everywhere else
- Dead Sea Scrolls (1947) confirmed Enoch was widely read in 1st century Judaism
- Ethiopian Bible shows how diverse early Christianity was in terms of canon
"""
    path = OUTPUT_DIR / "ethiopian-bible-overview.md"
    path.write_text(content, encoding="utf-8")
    print(f"  [saved] ethiopian-bible-overview.md")


# ── Dispatch ──────────────────────────────────────────────────────────────────

ALL = {
    "enoch":    download_book_of_enoch,
    "jubilees": download_book_of_jubilees,
    "granth":   download_guru_granth_sahib,
    "talmud":   download_talmud,
    "ethiopian": write_ethiopian_bible_overview,
}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
targets = args if args else ["all"]
if "all" in targets:
    targets = list(ALL.keys())

print(f"Extended Sacred Texts Downloader — {len(targets)} target(s)")
print(f"Output: {OUTPUT_DIR}\n")

for t in targets:
    if t in ALL:
        ALL[t]()
        time.sleep(1)
    else:
        print(f"Unknown: {t}. Options: {', '.join(ALL.keys())} or all")

print(f"\nDone. Run 'rebuild index' in Jarvis chat to make texts searchable.")
