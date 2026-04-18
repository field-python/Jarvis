#!/usr/bin/env python3
"""download-gnostic-texts.py — Download Nag Hammadi and other Gnostic texts"""
import json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
OUT_DIR  = BASE_DIR / "notes" / "generated" / "sacred-texts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GUTENBERG = [
    ("Pistis Sophia",                 "11036",  "pistis-sophia.md"),
    ("Gospel of the Infancy Jesus",   "12508",  "gospel-of-infancy-jesus.md"),
    ("Shepherd of Hermas",            "2080",   "shepherd-of-hermas.md"),
    ("Didache (Teaching of Apostles)","42827",  "didache.md"),
    ("The Nag Hammadi Library",       "28496",  "nag-hammadi-overview.md"),
]

WIKI_TOPICS = [
    ("Gospel of Philip",       "gospel-of-philip.md"),
    ("Gospel of Mary",         "gospel-of-mary.md"),
    ("Gospel of Truth",        "gospel-of-truth.md"),
    ("Apocryphon of John",     "apocryphon-of-john.md"),
    ("Gospel of Judas",        "gospel-of-judas.md"),
    ("Thunder, Perfect Mind",  "thunder-perfect-mind.md"),
    ("Hypostasis of the Archons","hypostasis-of-the-archons.md"),
    ("Sophia of Jesus Christ", "sophia-of-jesus-christ.md"),
    ("Valentinianism",         "valentinianism.md"),
    ("Gnosticism",             "gnosticism-overview.md"),
    ("Nag Hammadi library",    "nag-hammadi-library.md"),
    ("Manichaeism",            "manichaeism.md"),
    ("Hermeticism",            "hermeticism.md"),
    ("Emerald Tablet",         "emerald-tablet.md"),
    ("Corpus Hermeticum",      "corpus-hermeticum.md"),
    ("Catharism",              "catharism.md"),
    ("Bogomilism",             "bogomilism.md"),
    ("Sethianism",             "sethianism.md"),
    ("Demiurge",               "demiurge.md"),
    ("Pleroma",                "pleroma-gnostic.md"),
]

def fetch_gutenberg(book_id):
    for url in [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisOffline/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8", errors="replace")
            if len(text) > 500:
                # Strip Gutenberg header/footer
                start = text.find("*** START OF")
                end   = text.find("*** END OF")
                if start != -1: text = text[start+text[start:].find("\n")+1:]
                if end   != -1: text = text[:end]
                return text.strip()
        except Exception:
            continue
    return None

def fetch_wiki(title):
    params = urllib.parse.urlencode({
        "action":"query","prop":"extracts","explaintext":True,
        "exsectionformat":"plain","titles":title,"format":"json","exlimit":1,
    })
    req = urllib.request.Request(
        f"https://en.wikipedia.org/w/api.php?{params}",
        headers={"User-Agent": "JarvisOffline/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        page = next(iter(data.get("query",{}).get("pages",{}).values()))
        if page.get("pageid",-1) == -1: return None
        text = page.get("extract","").strip()
        return text if len(text) > 200 else None
    except Exception as e:
        print(f"    warn: {e}")
        return None

print("\nDownloading Gnostic & Hermetic texts...\n")

# Gutenberg texts
print("=== Project Gutenberg ===")
for title, book_id, fname in GUTENBERG:
    path = OUT_DIR / fname
    if path.exists():
        print(f"  skip: {fname}")
        continue
    print(f"  fetching: {title}...")
    text = fetch_gutenberg(book_id)
    if text:
        path.write_text(f"# {title}\n\n{text}\n", encoding="utf-8")
        print(f"  saved: {fname}  ({len(text):,} chars)")
    else:
        print(f"  miss: {title}")
    time.sleep(1.5)

# Wikipedia articles
print("\n=== Wikipedia ===")
for title, fname in WIKI_TOPICS:
    path = OUT_DIR / fname
    if path.exists():
        print(f"  skip: {fname}")
        continue
    print(f"  fetching: {title}...")
    text = fetch_wiki(title)
    if text:
        path.write_text(f"# {title}\n\n{text}\n", encoding="utf-8")
        print(f"  saved: {fname}  ({len(text):,} chars)")
    else:
        print(f"  miss: {title}")
    time.sleep(2.0)

print("\nDone. Run 'Jarvis rebuild-index' to index new texts.\n")
