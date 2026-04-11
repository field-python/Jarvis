#!/usr/bin/env python3
"""search.py — search the Jarvis local archive (wrapper around ripgrep with Python fallback)"""
import sys
import re
import subprocess
import shutil
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: search.py <search terms>")
    sys.exit(1)

script_dir  = Path(__file__).parent.resolve()
base_dir    = script_dir.parent
config_file = base_dir / "config" / "archive-roots.txt"
cache_dir   = base_dir / ".cache" / "pdftext"
query       = " ".join(sys.argv[1:])

roots = []
if config_file.exists():
    for line in config_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if Path(line).is_dir():
            roots.append(line)

if not roots:
    sys.exit(0)

SKIP = [
    "breadcrumb", "<nav", "header__", "footer", "javascript", "cookie",
    "privacy policy", "skip to main content", "aria-", "og:", "viewport",
    "favicon", "/index/improvements/", "/.cache/",
]

if shutil.which("rg"):
    cmd = [
        "rg", "-n", "-S", "-m", "1",
        "--glob", "*.md", "--glob", "*.txt",
        "--glob", "*.html", "--glob", "*.htm", "--glob", "*.csv",
        "--glob", "!*.zim", "--glob", "!*.aria2",
        query,
    ] + roots + ([str(cache_dir)] if cache_dir.exists() else [])

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    # Normalise PDF cache paths
    output = output.replace(str(cache_dir) + "/", "").replace(".pdf.txt:", ".pdf:")

    for line in output.splitlines():
        low = line.lower()
        if not any(p in low for p in SKIP):
            print(line)
else:
    # Fallback: pure-Python search (slower but no extra deps)
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    found = []
    for root in roots:
        for ext in ("*.md", "*.txt"):
            for fpath in Path(root).rglob(ext):
                try:
                    for i, line in enumerate(
                        fpath.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                    ):
                        if pattern.search(line):
                            low = line.lower()
                            if not any(p in low for p in SKIP):
                                found.append(f"{fpath}:{i}:{line[:300]}")
                            break
                except Exception:
                    pass

    print("\n".join(found[:50]))
