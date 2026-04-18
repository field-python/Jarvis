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
_hour        = now.hour
if _hour < 12:
    time_of_day = "morning"
elif _hour < 17:
    time_of_day = "afternoon"
elif _hour < 21:
    time_of_day = "evening"
else:
    time_of_day = "night"

location_conf = base_dir / "config" / "location.conf"
location = "your area"
if location_conf.exists():
    lines = location_conf.read_text(encoding="utf-8").strip().splitlines()
    location = lines[0] if lines else "your area"

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  📅 Jarvis Daily Briefing")
print(f"  {current_date}  |  {current_time}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# ── skill of the day (always available — local model, no internet needed) ─────
# ── location-aware skill selection ───────────────────────────────────────────
# Base categories relevant year-round everywhere
SKILL_CATEGORIES_BASE = [
    "first aid and emergency medicine",
    "home repair and maintenance",
    "cooking from scratch",
    "tool sharpening and maintenance",
    "knot tying and rope work",
    "food preservation (canning, smoking, drying)",
    "emergency preparedness",
    "navigation without GPS (map, compass, stars)",
    "animal care and livestock basics",
    "medicinal plants and natural remedies",
    "off-grid power and energy",
    "gardening and soil preparation",
    "water sourcing and purification",
]

# Seasonal / climate-aware additions based on location keywords and month
_month = now.month
_loc_lower = location.lower()

SKILL_CATEGORIES = list(SKILL_CATEGORIES_BASE)

# Cold-climate / Alaska additions (year-round relevant in cold regions)
if any(k in _loc_lower for k in ("alaska", "yukon", "canada", "montana", "idaho", "wyoming", "minnesota", "wisconsin", "maine", "vermont", "north dakota", "michigan")):
    SKILL_CATEGORIES += [
        "cold weather and winter survival",
        "ice fishing and winter fishing",
        "snowmobile and sled dog travel",
        "firewood processing and wood heating",
        "permafrost and frozen ground building",
    ]
    if _month in (10, 11, 12, 1, 2, 3):   # winter
        SKILL_CATEGORIES += [
            "avalanche safety and snow travel",
            "cold-weather camp cooking",
            "frostbite and hypothermia treatment",
        ]
    elif _month in (4, 5, 6):              # spring / breakup
        SKILL_CATEGORIES += [
            "spring foraging for wild plants",
            "river and flood preparedness",
            "bear awareness and deterrence",
        ]
    elif _month in (7, 8, 9):              # summer
        SKILL_CATEGORIES += [
            "salmon fishing and fish processing",
            "berry picking and wild fruit preservation",
            "wilderness fire safety",
            "foraging for wild edible plants",
        ]
elif any(k in _loc_lower for k in ("florida", "texas", "arizona", "california", "georgia", "louisiana", "mississippi", "alabama", "hawaii")):
    SKILL_CATEGORIES += [
        "heat safety and hydration",
        "hurricane and severe storm preparedness",
        "tropical foraging and wild plants",
        "water purification in humid climates",
    ]
    if _month in (6, 7, 8, 9):             # summer / storm season
        SKILL_CATEGORIES += [
            "cooling without electricity",
            "shelter from extreme heat",
        ]
else:
    # Generic additions for other regions
    SKILL_CATEGORIES += [
        "wilderness survival",
        "fire making and fire safety",
        "shelter building and insulation",
        "fishing and trapping basics",
        "hunting preparation and field dressing",
        "camp cooking",
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

# ── fetch news (world + local) ────────────────────────────────────────────────
print("Fetching news...")

def fetch_rss_titles(url, max_titles=5):
    """Return up to max_titles headlines from an RSS feed, or []."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        titles = re.findall(r'<title>([^<]+)</title>', content)
        titles = [t for t in titles if "Google News" not in t and "ADN" not in t
                  and len(t) > 10][:max_titles]
        return titles
    except Exception:
        return []

world_titles = fetch_rss_titles(
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", max_titles=4
)

# Pick a local feed based on location
_loc_lower = location.lower()
local_feed  = None
local_label = None
if any(k in _loc_lower for k in ("alaska", "anchorage", "juneau", "fairbanks")):
    local_feed  = "https://www.adn.com/arc/outboundfeeds/rss/"
    local_label = "Alaska (ADN)"
elif any(k in _loc_lower for k in ("seattle", "washington")):
    local_feed  = "https://www.seattletimes.com/feed/"
    local_label = "Seattle Times"
elif any(k in _loc_lower for k in ("new york", "nyc")):
    local_feed  = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
    local_label = "NY Times"

local_titles = fetch_rss_titles(local_feed, max_titles=3) if local_feed else []

# Build headlines block: 2 world + up to 1 local = 3 stories
selected = []
selected += world_titles[:2]
if local_titles:
    selected.append(f"[{local_label}] {local_titles[0]}")
elif len(world_titles) > 2:
    selected.append(world_titles[2])

headlines = "\n".join(selected)
news_ok   = bool(headlines)
local_ok  = bool(local_titles)

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
    f"You are Jarvis, an AI assistant giving a daily briefing. Today is {current_date} and it is currently {time_of_day} ({current_time}).\n\n"
    f"Deliver a spoken briefing in this order:\n"
    f"1. A brief 'good {time_of_day}' greeting — just one sentence\n"
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
    print(f"  🛠️ Skill of the Day  |  {category.title()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(skill_text)
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

# ── speak aloud ───────────────────────────────────────────────────────────────
if tts_script.exists() and briefing:
    subprocess.run(["bash", str(tts_script), briefing], stderr=subprocess.DEVNULL)
