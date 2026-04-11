#!/usr/bin/env bash
# news.sh — Fetch and summarize current news headlines via Jarvis
# Usage: news.sh [category]  (category: world, tech, sports, entertainment — default: world)

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
generate_script="$base_dir/scripts/generate.py"
model="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"

category="${1:-world}"
current_date="$(date '+%A, %B %-d, %Y')"
current_time="$(date '+%-I:%M %p')"

# ── RSS feeds by category ─────────────────────────────────────────────────────
case "$category" in
  tech|technology)
    feed_url="https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    label="Technology"
    ;;
  sports)
    feed_url="https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    label="Sports"
    ;;
  entertainment)
    feed_url="https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    label="Entertainment"
    ;;
  *)
    feed_url="https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    label="World"
    ;;
esac

echo "Fetching $label news..."

# ── fetch headlines from RSS ──────────────────────────────────────────────────
headlines="$(
  curl -L --silent --max-time 15 "$feed_url" 2>/dev/null \
    | grep -o '<title>[^<]*</title>' \
    | sed 's/<[^>]*>//g' \
    | grep -v "Google News" \
    | head -10 \
  || true
)"

if [[ -z "$headlines" ]]; then
  echo "Could not fetch news. Check your connection."
  exit 1
fi

# ── build prompt ──────────────────────────────────────────────────────────────
tmp_prompt="$(mktemp /tmp/jarvis-news-XXXXXX.txt)"
cat > "$tmp_prompt" <<EOF
You are Jarvis, an AI assistant. Today is $current_date.

Summarize the following $label news headlines into a brief, spoken-style briefing.
Group related stories. Be direct and informative. Use plain prose — no bullet points,
no markdown, no headers. 3-5 sentences total. Speak as if reading a news brief aloud.

Headlines:
$headlines
EOF

# ── generate summary ──────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis News  |  $label  |  $current_date  |  $current_time"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
"$venv_python" "$generate_script" "$model" "$host" "$tmp_prompt"
echo ""
rm -f "$tmp_prompt"
