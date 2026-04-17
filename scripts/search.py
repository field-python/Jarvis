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
raw_query   = " ".join(sys.argv[1:])
# Support comma-separated terms: "term1, term2" runs two searches and merges results
queries     = [q.strip() for q in raw_query.split(",") if q.strip()]
query       = queries[0]  # used for single-query paths below

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

def run_rg(q):
    cmd = [
        "rg", "-n", "-S", "-m", "1",
        "--glob", "*.md", "--glob", "*.txt",
        "--glob", "*.html", "--glob", "*.htm", "--glob", "*.csv",
        "--glob", "!*.zim", "--glob", "!*.aria2",
        q,
    ] + roots + ([str(cache_dir)] if cache_dir.exists() else [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout
    output = output.replace(str(cache_dir) + "/", "").replace(".pdf.txt:", ".pdf:")
    return [line for line in output.splitlines()
            if not any(p in line.lower() for p in SKIP)]


def run_python(q):
    try:
        pattern = re.compile(q, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
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
    return found


if shutil.which("rg"):
    seen  = set()
    lines = []
    for q in queries:
        for line in run_rg(q):
            if line not in seen:
                seen.add(line)
                lines.append(line)
    print("\n".join(lines))
else:
    seen  = set()
    found = []
    for q in queries:
        for entry in run_python(q):
            if entry not in seen:
                seen.add(entry)
                found.append(entry)
    print("\n".join(found[:50]))
