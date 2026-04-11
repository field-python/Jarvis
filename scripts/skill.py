#!/usr/bin/env python3
"""skill.py — Skill of the Day: one practical, actionable skill per day"""
import sys
import os
import select
import subprocess
import tempfile
import random
import tty
import termios
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

now          = datetime.now()
today        = now.strftime("%Y-%m-%d")
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

DIM    = "\033[2m"
YELLOW = "\033[93m"
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


CATEGORIES = [
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

# Parse args: 'Jarvis skill [category|new]'
arg        = " ".join(sys.argv[1:]).strip().lower() if len(sys.argv) > 1 else ""
force_new  = arg == "new"
category   = None

if arg and not force_new:
    # Find closest matching category
    for cat in CATEGORIES:
        if any(word in cat for word in arg.split()):
            category = cat
            break
    if not category:
        category = arg  # use as-is if no match

# Cache file — one per day (or per day+category if category specified)
cache_dir  = base_dir / "cache" / "skill"
cache_dir.mkdir(parents=True, exist_ok=True)
cache_key  = f"{today}-{category or 'daily'}.txt"
cache_file = cache_dir / cache_key

if cache_file.exists() and not force_new:
    cached = cache_file.read_text(encoding="utf-8").strip()
    cat_label = (category or "Daily Skill").title()
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Skill  |  {cat_label}  |  {current_date}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(cached)
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  (cached — 'Jarvis skill new' for a different one)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    sys.exit(0)

# Pick category — seed by date so it's consistent all day unless forced
if not category:
    rng      = random.Random(today)
    category = rng.choice(CATEGORIES)

cat_label = category.title()

prompt = (
    f"You are Jarvis, a practical AI assistant. Today is {current_date}.\n\n"
    f"Teach one specific, actionable skill from the category: {category}.\n\n"
    f"Format your response exactly like this:\n"
    f"SKILL: [short name of the skill, 3-6 words]\n\n"
    f"[2-3 sentences explaining what this skill is and why it matters.]\n\n"
    f"HOW TO DO IT:\n"
    f"1. [first step]\n"
    f"2. [second step]\n"
    f"3. [third step]\n"
    f"(3-5 steps, each one sentence, concrete and specific)\n\n"
    f"PRO TIP: [one sentence with a key insight or common mistake to avoid]\n\n"
    f"Rules: Be specific, not vague. Give real steps a beginner can follow today. "
    f"No fluff, no intros like 'Great question!'. Start directly with SKILL:."
)

tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-skill-", delete=False
)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Jarvis Skill  |  {cat_label}  |  {current_date}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Capture output for caching
import io

def stream_and_capture(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    buf  = io.StringIO()
    for ch in iter(lambda: proc.stdout.read(1), ""):
        sys.stdout.write(ch)
        sys.stdout.flush()
        buf.write(ch)
    proc.wait()
    return buf.getvalue()

response = stream_and_capture([sys.executable, generate_script, model, host, tmp.name])
os.unlink(tmp.name)

if response.strip():
    cache_file.write_text(response, encoding="utf-8")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# ── "another skill?" loop ─────────────────────────────────────────────────────
used_categories = {category}

while True:
    ans = input_with_esc(
        f"  {YELLOW}Another skill? (ESC to exit / category name for specific): {RESET}"
    )
    if ans is None:
        break
    ans = ans.strip()
    if not ans:
        # blank → pick a different random category
        remaining = [c for c in CATEGORIES if c not in used_categories]
        if not remaining:
            remaining = list(CATEGORIES)
        next_cat = random.choice(remaining)
    else:
        # Match to a category
        next_cat = None
        low = ans.lower()
        for cat in CATEGORIES:
            if any(w in cat for w in low.split()):
                next_cat = cat
                break
        if not next_cat:
            next_cat = low  # use as-is

    used_categories.add(next_cat)
    next_label = next_cat.title()
    next_prompt = (
        f"You are Jarvis, a practical AI assistant. Today is {current_date}.\n\n"
        f"Teach one specific, actionable skill from the category: {next_cat}.\n\n"
        f"Format your response exactly like this:\n"
        f"SKILL: [short name of the skill, 3-6 words]\n\n"
        f"[2-3 sentences explaining what this skill is and why it matters.]\n\n"
        f"HOW TO DO IT:\n"
        f"1. [first step]\n"
        f"2. [second step]\n"
        f"3. [third step]\n"
        f"(3-5 steps, each one sentence, concrete and specific)\n\n"
        f"PRO TIP: [one sentence with a key insight or common mistake to avoid]\n\n"
        f"Rules: Be specific, not vague. Give real steps a beginner can follow today. "
        f"No fluff. Start directly with SKILL:."
    )

    next_tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-skill-", delete=False
    )
    next_tmp.write(next_prompt)
    next_tmp.close()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Skill  |  {next_label}  |  {current_date}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    stream_and_capture([sys.executable, generate_script, model, host, next_tmp.name])
    os.unlink(next_tmp.name)
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
