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
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
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
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = total // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
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

# Primary: Google News RSS (reliable, no auth needed)
# Secondary: AP News RSS (sometimes blocks; tried as fallback)
FEEDS = {
    # ── World / US ────────────────────────────────────────────────────────────
    "world":         ("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",          "World News"),
    "us":            ("https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkoyNXVhV05vYjI5bkVnSmxiaUFBUAE?hl=en-US&gl=US&ceid=US:en", "US News"),
    "politics":      ("https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkoyNXVhV05vYjI5bkVnSmxiaUFBUAE?hl=en-US&gl=US&ceid=US:en", "Politics"),

    # ── Local / Regional ──────────────────────────────────────────────────────
    "alaska":        ("https://www.adn.com/arc/outboundfeeds/rss/",                     "Alaska — ADN"),
    "anchorage":     ("https://www.adn.com/arc/outboundfeeds/rss/",                     "Anchorage — ADN"),

    # ── Independent / alternative ─────────────────────────────────────────────
    "hill":          ("https://thehill.com/feed/",                                       "The Hill"),
    "reason":        ("https://reason.com/feed/",                                        "Reason"),
    "intercept":     ("https://theintercept.com/feed/?rss",                              "The Intercept"),
    "propublica":    ("https://feeds.propublica.org/propublica/main",                    "ProPublica"),

    # ── Specialty ─────────────────────────────────────────────────────────────
    "tech":          ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Tech News"),
    "technology":    ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Tech News"),
    "science":       ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNR1p0T1hZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Science News"),
    "health":        ("https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en",       "Health News"),
    "business":      ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Business News"),
    "sports":        ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Sports News"),
    "entertainment": ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en", "Entertainment"),
}

if not fetch_and_show(category):
    sys.exit(1)

# ── "more" loop ───────────────────────────────────────────────────────────────
categories_hint = "world  us  politics  tech  science  sports  ent  hill  reason  intercept"
while True:
    print(f"  {DIM}{'─' * 40}{RESET}")
    print()
    print(f"  {DIM}Categories: {categories_hint}{RESET}")
    ans = input_with_esc(
        f"  {YELLOW}Category (ESC to exit): {RESET}"
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
