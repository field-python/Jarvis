#!/usr/bin/env python3
"""news.py — fetch and summarize current news headlines via Jarvis"""
import sys
import os
import re
import select
import subprocess
import tempfile
import tty
import termios
import urllib.request
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def input_with_esc(prompt_str):
    """Like input() but returns None if ESC is pressed."""
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf.pop()
                    sys.stdout.write("\x08 \x08")
                    sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def fetch_and_show(category_arg):
    """Fetch and display one category of news. Returns False if fetch fails."""
    cat = category_arg.lower().strip()
    feed_url, label = FEEDS.get(cat, (
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "World"
    ))

    now          = datetime.now()
    current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"
    current_time = now.strftime("%-I:%M %p")

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
        return False

    if not headlines:
        print("No headlines found.")
        return False

    prompt = (
        f"You are Jarvis, an AI assistant. Today is {current_date}.\n\n"
        f"Summarize the following {label} news headlines into a brief, spoken-style briefing.\n"
        f"Group related stories. Be direct and factual — report what happened, not what to think about it.\n"
        f"No editorializing, no political framing, no loaded language. Plain prose only — no bullet points,\n"
        f"no markdown, no headers. 3-5 sentences total. Speak as if reading a wire-service brief aloud.\n\n"
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
    return True


category = sys.argv[1].lower() if len(sys.argv) > 1 else "world"

# Independent / wire-service sources: AP, Reuters, The Hill, Reason
# Fallback to AP RSS if a specialty feed is unavailable
FEEDS = {
    # ── World / US ────────────────────────────────────────────────────────────
    "world":         ("https://feeds.apnews.com/apnews/topnews",                   "World — AP News"),
    "us":            ("https://feeds.apnews.com/apnews/usnews",                     "US News — AP"),
    "politics":      ("https://feeds.apnews.com/apnews/politics",                   "Politics — AP"),

    # ── Independent / alternative ─────────────────────────────────────────────
    "reuters":       ("https://feeds.reuters.com/reuters/topNews",                  "Reuters Top News"),
    "hill":          ("https://thehill.com/feed/",                                  "The Hill"),
    "reason":        ("https://reason.com/feed/",                                   "Reason"),
    "intercept":     ("https://theintercept.com/feed/?rss",                         "The Intercept"),
    "propublica":    ("https://feeds.propublica.org/propublica/main",               "ProPublica"),

    # ── Specialty ─────────────────────────────────────────────────────────────
    "tech":          ("https://feeds.apnews.com/apnews/technology",                 "Technology — AP"),
    "technology":    ("https://feeds.apnews.com/apnews/technology",                 "Technology — AP"),
    "science":       ("https://feeds.apnews.com/apnews/science",                    "Science — AP"),
    "health":        ("https://feeds.apnews.com/apnews/health",                     "Health — AP"),
    "business":      ("https://feeds.apnews.com/apnews/business",                   "Business — AP"),
    "sports":        ("https://feeds.apnews.com/apnews/sports",                     "Sports — AP"),
    "entertainment": ("https://feeds.apnews.com/apnews/entertainment",              "Entertainment — AP"),
    "alaska":        ("https://feeds.apnews.com/apnews/alaska",                     "Alaska — AP"),
}

if not fetch_and_show(category):
    sys.exit(1)

# ── "more" loop ───────────────────────────────────────────────────────────────
categories_hint = "world  us  politics  tech  science  sports  ent  hill  reason  intercept"
while True:
    print(f"  {DIM}{'─' * 40}{RESET}")
    print()
    ans = input_with_esc(
        f"  {YELLOW}Another category? (world/us/tech/science/sports/ent/politics/hill/reason/intercept / ESC): {RESET}"
    )
    if ans is None:
        break
    ans = ans.strip().lower()
    if not ans:
        continue
    # Friendly prefix matching
    if ans.startswith("pol"):
        ans = "politics"
    elif ans.startswith("sci"):
        ans = "science"
    elif ans.startswith("hea"):
        ans = "health"
    elif ans.startswith("bus"):
        ans = "business"
    elif ans.startswith("sp"):
        ans = "sports"
    elif ans in ("ent", "entertainment", "e"):
        ans = "entertainment"
    elif ans.startswith("tech") or ans == "t":
        ans = "tech"
    elif ans.startswith("hill") or ans == "h":
        ans = "hill"
    elif ans.startswith("rea"):
        ans = "reason"
    elif ans.startswith("int"):
        ans = "intercept"
    elif ans.startswith("pro"):
        ans = "propublica"
    elif ans.startswith("reu"):
        ans = "reuters"
    elif ans.startswith("al"):
        ans = "alaska"
    elif ans.startswith("us"):
        ans = "us"
    elif ans.startswith("w"):
        ans = "world"
    print()
    fetch_and_show(ans)
