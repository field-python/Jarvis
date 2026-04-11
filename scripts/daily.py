#!/usr/bin/env python3
"""daily.py — morning briefing: skill of the day + weather + news, spoken aloud"""
import sys
import os
import io
import re
import random
import subprocess
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
tts_script      = base_dir / "scripts" / "tts.sh"
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

now          = datetime.now()
today        = now.strftime("%Y-%m-%d")
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"
current_time = now.strftime("%I:%M %p").lstrip("0")

location_conf = base_dir / "config" / "location.conf"
location = "your area"
if location_conf.exists():
    lines = location_conf.read_text(encoding="utf-8").strip().splitlines()
    location = lines[0] if lines else "your area"

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Jarvis Daily Briefing")
print(f"  {current_date}  |  {current_time}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# ── skill of the day (always available — local model, no internet needed) ─────
SKILL_CATEGORIES = [
    "wilderness survival",
    "first aid and emergency medicine",
    "fire making and fire safety",
    "water sourcing and purification",
    "food preservation (canning, smoking, drying)",
    "foraging for wild edible plants",
    "shelter building and insulation",
    "knot tying and rope work",
    "cold weather and winter survival",
    "navigation without GPS (map, compass, stars)",
    "fishing and trapping basics",
    "hunting preparation and field dressing",
    "home repair and maintenance",
    "off-grid power and energy",
    "gardening and soil preparation",
    "cooking from scratch and camp cooking",
    "tool sharpening and maintenance",
    "animal care and livestock basics",
    "emergency preparedness and bugging out",
    "medicinal plants and natural remedies",
]

cache_dir  = base_dir / "cache" / "skill"
cache_dir.mkdir(parents=True, exist_ok=True)
cache_file = cache_dir / f"{today}-daily.txt"

skill_text = ""
rng        = random.Random(today)
category   = rng.choice(SKILL_CATEGORIES)

if cache_file.exists():
    skill_text = cache_file.read_text(encoding="utf-8").strip()
    print(f"Skill of the day: {category.title()} (cached)")
else:
    print(f"Generating skill of the day: {category.title()}...")
    skill_prompt = (
        f"You are Jarvis. Today is {current_date}.\n\n"
        f"Teach one specific, actionable skill from the category: {category}.\n\n"
        f"Format exactly like this:\n"
        f"SKILL: [short name, 3-6 words]\n\n"
        f"[2-3 sentences explaining what this skill is and why it matters.]\n\n"
        f"HOW TO DO IT:\n"
        f"1. [step one]\n"
        f"2. [step two]\n"
        f"3. [step three]\n"
        f"(3-5 steps, each one sentence, concrete and specific)\n\n"
        f"PRO TIP: [one sentence with a key insight or common mistake to avoid]\n\n"
        f"Be specific. Give real steps a beginner can follow today. "
        f"No fluff. Start directly with SKILL:."
    )
    stmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-skill-", delete=False
    )
    stmp.write(skill_prompt)
    stmp.close()

    result = subprocess.run(
        [sys.executable, generate_script, model, host, stmp.name],
        capture_output=True, text=True
    )
    os.unlink(stmp.name)
    skill_text = result.stdout.strip()
    if skill_text:
        cache_file.write_text(skill_text, encoding="utf-8")

# ── fetch weather ─────────────────────────────────────────────────────────────
print("Fetching weather...")
weather      = ""
weather_ok   = False
try:
    loc = urllib.parse.quote(location)
    fmt = urllib.parse.quote("%C,+%t+(feels+%f),+humidity+%h,+wind+%w")
    url = f"https://wttr.in/{loc}?format={fmt}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        weather = resp.read().decode("utf-8", errors="replace").strip()
    weather_ok = bool(weather)
except Exception:
    weather = ""

# ── fetch news ────────────────────────────────────────────────────────────────
print("Fetching news...")
headlines  = ""
news_ok    = False
try:
    feed = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    req  = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="replace")
    titles    = re.findall(r'<title>([^<]+)</title>', content)
    titles    = [t for t in titles if "Google News" not in t][:8]
    headlines = "\n".join(titles)
    news_ok   = bool(headlines)
except Exception:
    headlines = ""

# ── build prompt ──────────────────────────────────────────────────────────────
weather_section = (
    f"Weather for {location}: {weather}"
    if weather_ok else
    "Weather: unavailable (no internet connection)"
)

news_section = (
    f"Top headlines:\n{headlines}"
    if news_ok else
    "News: unavailable (no internet connection)"
)

skill_section = (
    f"Today's skill of the day ({category}):\n{skill_text}"
    if skill_text else
    ""
)

prompt = (
    f"You are Jarvis, an AI assistant giving a morning briefing. Today is {current_date}.\n\n"
    f"Deliver a spoken morning briefing in this order:\n"
    f"1. A brief greeting appropriate to the time of day\n"
    f"2. Weather update for {location} — skip this section entirely if weather is unavailable\n"
    f"3. Top news summary — skip this section entirely if news is unavailable\n"
    f"4. Introduce today's skill of the day by name and give one sentence on why it's worth knowing\n"
    f"5. A short closing remark\n\n"
    f"Rules:\n"
    f"- Plain spoken prose only — no bullet points, no headers, no markdown\n"
    f"- Keep it under 130 words total\n"
    f"- Natural Jarvis tone — calm, dry wit, professionally warm\n"
    f"- Do not say 'based on the data' or 'according to'\n"
    f"- If weather or news is unavailable, skip those sections without comment\n\n"
    f"{weather_section}\n\n"
    f"{news_section}\n\n"
    f"{skill_section}"
)

tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-daily-", delete=False
)
tmp.write(prompt)
tmp.close()

# ── display sections ──────────────────────────────────────────────────────────
print()

if not weather_ok and not news_ok:
    print("  (offline — weather and news unavailable)")
    print()

# ── generate briefing + stream ────────────────────────────────────────────────
proc = subprocess.Popen(
    [sys.executable, generate_script, model, host, tmp.name],
    stdout=subprocess.PIPE, text=True
)
buf = io.StringIO()
for ch in iter(lambda: proc.stdout.read(1), ""):
    sys.stdout.write(ch)
    sys.stdout.flush()
    buf.write(ch)
proc.wait()
briefing = buf.getvalue().strip()
os.unlink(tmp.name)
print()

# ── skill of the day block ────────────────────────────────────────────────────
if skill_text:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Skill of the Day  |  {category.title()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(skill_text)
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

# ── speak aloud ───────────────────────────────────────────────────────────────
if tts_script.exists() and briefing:
    subprocess.run(["bash", str(tts_script), briefing], stderr=subprocess.DEVNULL)
