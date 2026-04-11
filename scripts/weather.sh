#!/usr/bin/env bash
# weather.sh — Fetch weather from wttr.in and have Jarvis interpret it
# Usage: weather.sh [location]  (defaults to location.conf)

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
generate_script="$base_dir/scripts/generate.py"
model="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"

# ── resolve location ──────────────────────────────────────────────────────────
if [[ $# -ge 1 ]]; then
  location="$*"
else
  location_conf="$base_dir/config/location.conf"
  if [[ -f "$location_conf" ]]; then
    location="$(grep -v '^\s*#' "$location_conf" | head -1 | tr -d '\n')"
  else
    location="Anchorage, Alaska"
  fi
fi

current_date="$(date '+%A, %B %-d, %Y')"
echo "Fetching weather for $location..."

# ── fetch from wttr.in (plain text, no API key needed) ───────────────────────
weather_raw="$(
  curl -s --max-time 15 "https://wttr.in/${location// /+}?format=4" 2>/dev/null || true
)"

weather_detail="$(
  curl -s --max-time 15 "https://wttr.in/${location// /+}?format=%l:+%C,+%t+(feels+%f),+humidity+%h,+wind+%w,+%P" 2>/dev/null || true
)"

if [[ -z "$weather_raw" && -z "$weather_detail" ]]; then
  echo "Could not fetch weather. Check your connection."
  exit 1
fi

weather_data="${weather_raw}
${weather_detail}"

# ── build prompt ──────────────────────────────────────────────────────────────
tmp_prompt="$(mktemp /tmp/jarvis-weather-XXXXXX.txt)"
cat > "$tmp_prompt" <<EOF
You are Jarvis, an AI assistant. Today is $current_date.

Interpret the following weather data for $location and give a practical spoken-style briefing.
Mention current conditions, temperature, and any notable factors (wind, humidity, precipitation).
Add one practical tip if relevant (e.g. dress warmly, carry an umbrella).
3-4 plain sentences. No markdown, no bullet points.

Weather data:
$weather_data
EOF

# ── output ────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis Weather  |  $location"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
"$venv_python" "$generate_script" "$model" "$host" "$tmp_prompt"
echo ""
rm -f "$tmp_prompt"
