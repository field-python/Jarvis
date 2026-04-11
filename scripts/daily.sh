#!/usr/bin/env bash
# daily.sh — Morning briefing: weather + news, spoken aloud by Jarvis
# Usage: daily.sh

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
generate_script="$base_dir/scripts/generate.py"
tts_script="$base_dir/scripts/tts.sh"
model="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"

current_date="$(date '+%A, %B %-d, %Y')"

# ── resolve location ──────────────────────────────────────────────────────────
location_conf="$base_dir/config/location.conf"
if [[ -f "$location_conf" ]]; then
  location="$(grep -v '^\s*#' "$location_conf" | head -1 | tr -d '\n')"
else
  location="your area"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis Daily Briefing  |  $current_date"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── fetch weather ─────────────────────────────────────────────────────────────
echo "Fetching weather..."
weather="$(
  curl -s --max-time 10 "https://wttr.in/${location// /+}?format=%C,+%t+(feels+%f),+humidity+%h,+wind+%w" 2>/dev/null || echo "weather unavailable"
)"

# ── fetch news headlines ──────────────────────────────────────────────────────
echo "Fetching news..."
headlines="$(
  curl -L --silent --max-time 15 \
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en" 2>/dev/null \
    | grep -o '<title>[^<]*</title>' \
    | sed 's/<[^>]*>//g' \
    | grep -v "Google News" \
    | head -8 \
  || echo "news unavailable"
)"

# ── build combined prompt ─────────────────────────────────────────────────────
tmp_prompt="$(mktemp /tmp/jarvis-daily-XXXXXX.txt)"
cat > "$tmp_prompt" <<EOF
You are Jarvis, an AI assistant giving a morning briefing. Today is $current_date.

Deliver a spoken morning briefing covering:
1. A greeting appropriate to the time of day
2. Current weather for $location (from the data below)
3. A summary of today's top news stories (from the headlines below)
4. One brief closing remark

Rules:
- Plain spoken prose only — no bullet points, no headers, no markdown
- Keep it under 120 words total
- Natural, conversational Jarvis tone — calm, dry wit, professionally warm
- Do not say "based on the data" or "according to" — just deliver it naturally

Weather: $weather

Top headlines:
$headlines
EOF

# ── generate and speak ────────────────────────────────────────────────────────
echo ""
briefing="$("$venv_python" "$generate_script" "$model" "$host" "$tmp_prompt")"
rm -f "$tmp_prompt"

echo "$briefing"
echo ""
bash "$tts_script" "$briefing" 2>/dev/null
