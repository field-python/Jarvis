#!/usr/bin/env python3
"""timer.py — countdown timer with spoken alerts via Jarvis TTS"""
import sys
import re
import subprocess
import time
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
tts_script = base_dir / "scripts" / "tts.sh"


def tts(text):
    if tts_script.exists():
        subprocess.Popen(
            ["bash", str(tts_script), text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def parse_seconds(raw):
    raw = raw.lower().replace(" ", "")
    for old, new in [
        ("minutes", "m"), ("minute", "m"), ("seconds", "s"), ("second", "s"),
        ("hours", "h"),   ("hour", "h"),   ("mins", "m"),    ("min", "m"),
        ("secs", "s"),    ("sec", "s"),    ("hrs", "h"),     ("hr", "h"),
    ]:
        raw = raw.replace(old, new)

    total = 0
    h = re.search(r'(\d+)h', raw)
    m = re.search(r'(\d+)m', raw)
    s = re.search(r'(\d+)s', raw)
    p = re.fullmatch(r'(\d+)', raw)

    if h: total += int(h.group(1)) * 3600
    if m: total += int(m.group(1)) * 60
    if s: total += int(s.group(1))
    if p: total += int(p.group(1)) * 60   # plain number = minutes
    return total


def format_duration(seconds):
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    parts  = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts) or "0s"


def spoken_label(seconds):
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    parts  = []
    if h: parts.append(f"{h} hour{'s' if h > 1 else ''}")
    if m: parts.append(f"{m} minute{'s' if m > 1 else ''}")
    if s: parts.append(f"{s} second{'s' if s > 1 else ''}")
    return ", ".join(parts)


if len(sys.argv) < 2:
    print("Usage: Jarvis timer <duration>")
    print()
    print("Examples:")
    print("  Jarvis timer 1h")
    print("  Jarvis timer 10m")
    print("  Jarvis timer 30s")
    print("  Jarvis timer 1h30m")
    print('  Jarvis timer "10 minutes"')
    sys.exit(1)

inp           = " ".join(sys.argv[1:])
total_seconds = parse_seconds(inp)

if total_seconds <= 0:
    print(f"Couldn't parse duration: {inp}")
    print("Try: 10m, 30s, 1h, 1h30m, or \"10 minutes\"")
    sys.exit(1)

duration_label = format_duration(total_seconds)
spoken         = spoken_label(total_seconds)

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Timer set: {duration_label}")
print("  Press Ctrl+C to cancel")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

tts(f"Timer started. {spoken} on the clock.")

remaining = total_seconds
try:
    while remaining > 0:
        print(f"\r  ⏱  {format_duration(remaining)} remaining   ", end="", flush=True)

        if remaining == 300: tts("Five minutes remaining.")
        elif remaining == 60: tts("One minute remaining.")
        elif remaining == 30: tts("Thirty seconds remaining.")
        elif remaining == 10: tts("Ten seconds.")

        time.sleep(1)
        remaining -= 1
except KeyboardInterrupt:
    print("\n\n  Timer cancelled.")
    sys.exit(0)

print("\r  ✓  Timer done!               ")
print()
tts("Time's up.")
