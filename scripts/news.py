#!/usr/bin/env python3
"""news.py — fetch and summarize current news headlines via Jarvis"""
import sys
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

category = sys.argv[1].lower() if len(sys.argv) > 1 else "world"

FEEDS = {
    "tech":          ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en", "Technology"),
    "technology":    ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en", "Technology"),
    "sports":        ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en", "Sports"),
    "entertainment": ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en", "Entertainment"),
}

feed_url, label = FEEDS.get(category, (
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "World"
))

now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"
current_time = now.strftime("%I:%M %p").lstrip("0")

print(f"Fetching {label} news...")

try:
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="replace")
    titles    = re.findall(r'<title>([^<]+)</title>', content)
    titles    = [t for t in titles if "Google News" not in t][:10]
    headlines = "\n".join(titles)
except Exception:
    print("Could not fetch news. Check your connection.")
    sys.exit(1)

if not headlines:
    print("No headlines found.")
    sys.exit(1)

prompt = (
    f"You are Jarvis, an AI assistant. Today is {current_date}.\n\n"
    f"Summarize the following {label} news headlines into a brief, spoken-style briefing.\n"
    f"Group related stories. Be direct and informative. Use plain prose — no bullet points,\n"
    f"no markdown, no headers. 3-5 sentences total. Speak as if reading a news brief aloud.\n\n"
    f"Headlines:\n{headlines}"
)

tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-news-", delete=False
)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Jarvis News  |  {label}  |  {current_date}  |  {current_time}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
