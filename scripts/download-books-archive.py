#!/usr/bin/env python3
"""
download-books-archive.py — Download free books from Archive.org as plain text.
Covers: Graham Hancock, Jacques Vallée, Whitley Strieber, Rick Strassman,
        Jeremy Narby, Erich von Däniken, and others.

Run: python3 download-books-archive.py [--force]

All texts are in the public domain or freely available on Archive.org.
Text files only — no images or binary formats.
"""

import os
import sys
import time
import urllib.request
import urllib.error

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "books")

HEADERS = {
    "User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"
}

BOOKS = [
    # ── Graham Hancock ────────────────────────────────────────────────────────
    {
        "slug": "hancock-fingerprints-of-the-gods",
        "title": "Fingerprints of the Gods — Graham Hancock",
        "url": "https://ia803100.us.archive.org/8/items/fingerprintsofthegodsbygrahamhancock/Fingerprints%20of%20the%20Gods%20by%20Graham%20Hancock.pdf",
        "format": "pdf",
    },
    {
        "slug": "hancock-america-before",
        "title": "America Before — Graham Hancock",
        "url": "https://archive.org/stream/abelc/America%20Before%20-%20The%20Key%20to%20Earth%E2%80%99s%20Lost%20Civilization%20by%20Graham%20Hancock%20(2019)_djvu.txt",
        "format": "txt",
    },
    {
        "slug": "hancock-sign-and-the-seal",
        "title": "The Sign and the Seal — Graham Hancock",
        "url": "https://archive.org/stream/SignAndTheSealTheQuestFoGrahamHancock/Sign%20and%20the%20Seal_%20The%20Quest%20fo%20-%20Graham%20Hancock_djvu.txt",
        "format": "txt",
    },

    # ── Jacques Vallée ────────────────────────────────────────────────────────
    {
        "slug": "vallee-passport-to-magonia",
        "title": "Passport to Magonia — Jacques Vallée",
        "url": "https://ia801800.us.archive.org/19/items/jacques-vallee-passportto-magonia_202012/JacquesValleePassporttoMagonia.pdf",
        "format": "pdf",
    },

    # ── Whitley Strieber ──────────────────────────────────────────────────────
    {
        "slug": "strieber-communion",
        "title": "Communion — Whitley Strieber",
        "url": "https://ia601600.us.archive.org/35/items/CommunionWhitleyStrieber/Communion,%20Whitley%20Strieber.pdf",
        "format": "pdf",
    },

    # ── Rick Strassman ────────────────────────────────────────────────────────
    {
        "slug": "strassman-dmt-spirit-molecule",
        "title": "DMT: The Spirit Molecule — Rick Strassman",
        "url": "https://archive.org/stream/RickStrassmanDMTTheSpiritMoleculex/Rick+Strassman+-+DMT+The+Spirit+Molecule+(x)_djvu.txt",
        "format": "txt",
    },

    # ── Jeremy Narby ─────────────────────────────────────────────────────────
    {
        "slug": "narby-cosmic-serpent",
        "title": "The Cosmic Serpent — Jeremy Narby",
        "url": "https://archive.org/stream/CosmicSerpent/cosserpent_djvu.txt",
        "format": "txt",
    },

    # ── Erich von Däniken ─────────────────────────────────────────────────────
    {
        "slug": "daniken-chariots-of-the-gods",
        "title": "Chariots of the Gods — Erich von Däniken",
        "url": "https://archive.org/stream/ERICHVONDANIKENCHARIOTSOFTHEGODS.WASGODANASTRONAUT/ERICH+VON+DANIKEN+-+CHARIOTS+OF+THE+GODS.+WAS+GOD+AN+ASTRONAUT_djvu.txt",
        "format": "txt",
    },
]

# ── Wikipedia topics for cloning / consciousness upload ──────────────────────
import json
import re
import urllib.parse

WIKI_TOPICS = {
    "cloning-consciousness": [
        "Human cloning",
        "Therapeutic cloning",
        "Reproductive cloning",
        "Dolly (sheep)",
        "Somatic cell nuclear transfer",
        "Cloning conspiracy theory",
        "Celebrity cloning conspiracy",
        "Human cloning in fiction",
        "Mind uploading",
        "Whole brain emulation",
        "Transhumanism",
        "Singularity (technological)",
        "Ray Kurzweil",
        "The Singularity Is Near",
        "Cryonics",
        "Alcor Life Extension Foundation",
        "Brain preservation",
        "Connectome",
        "Neural interface",
        "Brain–computer interface",
        "Neuralink",
        "Elon Musk",
        "Digital immortality",
        "Substrate-independent minds",
        "Simulation hypothesis",
        "Nick Bostrom",
        "Are You Living in a Computer Simulation",
        "Upload (TV series)",
        "Cognitive enhancement",
        "Intelligence amplification",
        "Posthumanism",
        "Extropianism",
        "Max More",
        "Natasha Vita-More",
        "2045 Initiative",
        "Dmitry Itskov",
        "Avatar project (2045 Initiative)",
        "Technological immortality",
        "Life extension",
        "Aubrey de Grey",
        "SENS Research Foundation",
        "Longevity escape velocity",
        "Telomere",
        "Senolytics",
        "Peter Thiel",
        "Silicon Valley longevity",
        "Google Calico",
        "Calico (company)",
        "Unity Biotechnology",
        "Human Connectome Project",
        "OpenWorm",
        "Emulation",
        "Artificial general intelligence",
        "Artificial consciousness",
        "Philosophy of mind",
        "Chinese room",
        "John Searle",
        "Functionalism (philosophy of mind)",
        "Qualia",
        "Hard problem of consciousness",
        "Identity (philosophy)",
        "Personal identity",
        "Teleportation paradox",
        "Ship of Theseus",
    ],
}


def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except Exception as e:
        print(f"    error: {e}")
        return None


def wiki_fetch(title, max_chars=6000):
    params = urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "extracts",
        "explaintext": "1", "exsectionformat": "plain", "format": "json",
        "redirects": "1", "exchars": str(max_chars),
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        if page.get("pageid", -1) == -1:
            return None
        text = page.get("extract", "").strip()
        return text if len(text) > 150 else None
    except Exception as e:
        print(f"    warn: {title}: {e}")
        return None


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    force = "--force" in sys.argv
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Download books ────────────────────────────────────────────────────────
    print(f"\n[BOOKS]  →  {OUTPUT_DIR}\n")
    for book in BOOKS:
        ext      = ".pdf" if book["format"] == "pdf" else ".txt"
        out_path = os.path.join(OUTPUT_DIR, book["slug"] + ext)

        if os.path.exists(out_path) and not force:
            print(f"  skip  {book['title']}")
            continue

        print(f"  fetch {book['title']}...", end=" ", flush=True)
        data = fetch_url(book["url"])
        if not data:
            print("failed")
            continue

        with open(out_path, "wb") as f:
            f.write(data)
        size_mb = len(data) / 1_000_000
        print(f"ok ({size_mb:.1f} MB)")
        time.sleep(1)

    # ── Download Wikipedia topics ─────────────────────────────────────────────
    for cat, topics in WIKI_TOPICS.items():
        cat_dir = os.path.join(OUTPUT_DIR, cat)
        os.makedirs(cat_dir, exist_ok=True)
        print(f"\n[{cat.upper()}]  {len(topics)} topics  →  {cat_dir}")

        for title in topics:
            slug     = slugify(title)
            out_path = os.path.join(cat_dir, f"{slug}.md")

            if os.path.exists(out_path) and not force:
                print(f"  skip  {title}")
                continue

            print(f"  fetch {title}...", end=" ", flush=True)
            text = wiki_fetch(title)
            if not text:
                print("not found")
                continue

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Source: Wikipedia*\n\n{text}\n")
            print(f"ok ({len(text):,} chars)")
            grand_total = 0
            time.sleep(0.3)

    print(f"\nDone.")
    print("Run 'Jarvis rebuild-index' to make everything searchable.")
    print("\nNOTE: For Hancock's 'Supernatural' and 'Magicians of the Gods',")
    print("create a free account at archive.org and borrow them there.")


if __name__ == "__main__":
    main()
