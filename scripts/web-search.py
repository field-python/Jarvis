#!/usr/bin/env python3
"""
web-search.py — Search the web via DuckDuckGo and save results to archive.
No API key required. Falls back gracefully when offline.

Usage: python3 web-search.py "search query" [--results N]
Prints fetched content to stdout for use in ask.sh context.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import html

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_CACHE_DIR = os.path.join(BASE_DIR, "notes", "web-cache")

MAX_RESULTS = 4
MAX_PAGE_CHARS = 3000
TIMEOUT = 12


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def ddg_search(query, max_results=MAX_RESULTS):
    """Query DuckDuckGo instant answer API and HTML search."""
    results = []

    # DuckDuckGo instant answer API (no key needed)
    try:
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
        url = f"https://api.duckduckgo.com/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))

        # Abstract (best single answer)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "url": data.get("AbstractURL", ""),
                "snippet": data["AbstractText"][:500],
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", "")[:300],
                })
    except Exception:
        pass

    # DuckDuckGo HTML search for additional results
    if len(results) < max_results:
        try:
            params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
            url = f"https://html.duckduckgo.com/html/?{params}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "text/html",
                }
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                content = r.read().decode("utf-8", errors="ignore")

            # Extract result links and snippets
            links = re.findall(
                r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
                content
            )
            snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)</(?:span|a)>',
                content
            )

            for i, (url_raw, title) in enumerate(links[:max_results]):
                # DDG wraps URLs — extract actual URL
                if "uddg=" in url_raw:
                    actual_url = urllib.parse.unquote(
                        re.search(r"uddg=([^&]+)", url_raw).group(1)
                    )
                else:
                    actual_url = url_raw

                snippet = html.unescape(re.sub(r"<[^>]+>", "", snippets[i])).strip() if i < len(snippets) else ""

                results.append({
                    "title": html.unescape(title).strip(),
                    "url": actual_url,
                    "snippet": snippet[:300],
                })

                if len(results) >= max_results:
                    break

        except Exception:
            pass

    return results[:max_results]


def fetch_page(url, max_chars=MAX_PAGE_CHARS):
    """Fetch a URL and return clean plain text."""
    if not url or not url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read().decode("utf-8", errors="ignore")

        # Strip scripts, styles, nav
        raw = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", " ", raw)
        # Decode HTML entities
        text = html.unescape(text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]
    except Exception:
        return None


def save_to_cache(query, content):
    """Save fetched content to archive for offline use."""
    os.makedirs(WEB_CACHE_DIR, exist_ok=True)
    slug = slugify(query)
    stamp = time.strftime("%Y-%m-%d")
    out_path = os.path.join(WEB_CACHE_DIR, f"{stamp}-{slug}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Web search: {query}\n\n")
        f.write(f"*Fetched: {stamp}*\n\n")
        f.write(content)
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: web-search.py \"query\" [--results N]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    max_r = MAX_RESULTS
    quick_mode = "--quick" in sys.argv  # snippets only, no page fetching
    if "--results" in sys.argv:
        idx = sys.argv.index("--results")
        if idx + 1 < len(sys.argv):
            max_r = int(sys.argv[idx + 1])

    print(f"Searching: {query}", file=sys.stderr)
    results = ddg_search(query, max_r)

    if not results:
        print("No results found or offline.", file=sys.stderr)
        sys.exit(1)

    all_content = []

    for i, result in enumerate(results):
        print(f"  [{i+1}/{len(results)}] {result['title'][:60]}", file=sys.stderr)

        section = f"## {result['title']}\nSource: {result['url']}\n\n"

        if quick_mode:
            # Quick mode: snippets only, no page fetching (fast, for voice fallback)
            section += result.get("snippet", "(no content)")
        elif result.get("url"):
            # Full mode: fetch page content
            page_text = fetch_page(result["url"])
            if page_text and len(page_text) > 200:
                section += page_text
            else:
                section += result.get("snippet", "(no content)")
        else:
            section += result.get("snippet", "(no content)")

        all_content.append(section)
        if not quick_mode:
            time.sleep(0.5)

    combined = "\n\n---\n\n".join(all_content)

    # Save to cache for offline use
    saved_path = save_to_cache(query, combined)
    print(f"  saved: {saved_path}", file=sys.stderr)

    # Output content for ask.sh to use as context
    print(combined)


if __name__ == "__main__":
    main()
