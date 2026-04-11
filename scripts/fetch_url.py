#!/usr/bin/env python3
"""fetch_url.py — save a webpage to the Jarvis archive"""
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage: fetch_url.py <url> [short-name]")
    sys.exit(1)

url  = sys.argv[1]
name = sys.argv[2] if len(sys.argv) == 3 else ""

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
pages_dir  = base_dir / "pages"
index_file = base_dir / "index" / "sources.md"

pages_dir.mkdir(parents=True, exist_ok=True)
(base_dir / "index").mkdir(parents=True, exist_ok=True)

if not name:
    parsed   = urllib.parse.urlparse(url)
    host_path = (parsed.netloc + parsed.path).rstrip("/")
    name = host_path.replace("/", "__").replace(":", "__")

output = pages_dir / f"{name}.html"
stamp  = datetime.now().strftime("%Y-%m-%d")

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/135.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        output.write_bytes(resp.read())
    with index_file.open("a", encoding="utf-8") as f:
        f.write(f"- `pages/{name}.html` - {url} - saved {stamp}\n")
    print(f"Saved: {output}")
except Exception as e:
    print(f"Error fetching {url}: {e}", file=sys.stderr)
    sys.exit(1)
