#!/usr/bin/env python3
"""weather.py — fetch weather from wttr.in and have Jarvis interpret it"""
import sys
import os
import subprocess
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

if len(sys.argv) >= 2:
    location = " ".join(sys.argv[1:])
else:
    location_conf = base_dir / "config" / "location.conf"
    if location_conf.exists():
        lines = location_conf.read_text(encoding="utf-8").strip().splitlines()
        location = lines[0] if lines else "Anchorage, Alaska"
    else:
        location = "Anchorage, Alaska"

now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

print(f"Fetching weather for {location}...")


def fetch_wttr(fmt):
    loc = urllib.parse.quote(location)
    url = f"https://wttr.in/{loc}?format={urllib.parse.quote(fmt)}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


weather_raw    = fetch_wttr("4")
weather_detail = fetch_wttr("%l:+%C,+%t+(feels+%f),+humidity+%h,+wind+%w,+%P")

if not weather_raw and not weather_detail:
    print("Could not fetch weather. Check your connection.")
    sys.exit(1)

weather_data = f"{weather_raw}\n{weather_detail}".strip()

prompt = (
    f"You are Jarvis, an AI assistant. Today is {current_date}.\n\n"
    f"Interpret the following weather data for {location} and give a practical spoken-style briefing.\n"
    f"Mention current conditions, temperature, and any notable factors (wind, humidity, precipitation).\n"
    f"Add one practical tip if relevant (e.g. dress warmly, carry an umbrella).\n"
    f"3-4 plain sentences. No markdown, no bullet points.\n\n"
    f"Weather data:\n{weather_data}"
)

tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-weather-", delete=False
)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Jarvis Weather  |  {location}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
