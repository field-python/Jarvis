#!/usr/bin/env bash
# auto-update.sh — refresh key pages in the Jarvis archive
# Run manually or add to cron: weekly is plenty
# Skips pages that are less than 7 days old

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
pages_dir="$base_dir/pages"
index_file="$base_dir/index/sources.md"
ua="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
stamp="$(date +%F)"
ok=0; skip=0; fail=0

fetch_if_stale() {
  local name="$1" url="$2"
  local out="$pages_dir/$name.html"
  # Skip if file is newer than 7 days
  if [[ -f "$out" ]] && [[ $(( $(date +%s) - $(stat -c %Y "$out") )) -lt 604800 ]]; then
    skip=$((skip+1))
    return
  fi
  if curl -L --fail --silent --max-time 30 -A "$ua" "$url" -o "$out" 2>/dev/null; then
    printf -- '- `pages/%s.html` - %s - updated %s\n' "$name" "$url" "$stamp" >> "$index_file"
    echo "  updated  $name"
    ok=$((ok+1))
  else
    echo "  failed   $name"
    fail=$((fail+1))
  fi
}

echo "Jarvis auto-update — $(date)"
echo ""

# Health
fetch_if_stale "health-fever-basics"         "https://medlineplus.gov/fever.html"
fetch_if_stale "health-first-aid-overview"   "https://medlineplus.gov/firstaid.html"
fetch_if_stale "health-mental-health"        "https://medlineplus.gov/mentalhealth.html"
fetch_if_stale "health-high-blood-pressure"  "https://medlineplus.gov/highbloodpressure.html"
fetch_if_stale "health-diabetes"             "https://medlineplus.gov/diabetes.html"
fetch_if_stale "meds-drug-info-overview"     "https://medlineplus.gov/druginformation.html"
fetch_if_stale "meds-antibiotics-guide"      "https://www.cdc.gov/antibiotic-use/index.html"

# Safety & preparedness
fetch_if_stale "home-repair-radon"           "https://www.epa.gov/radon/health-risk-radon"
fetch_if_stale "home-repair-lead-paint"      "https://www.epa.gov/lead/protect-your-family-lead-your-home"
fetch_if_stale "home-repair-mold"            "https://www.epa.gov/mold/mold-course-chapter-1"

# Finance
fetch_if_stale "finance-scam-protection"     "https://consumer.ftc.gov/articles/what-do-if-you-were-scammed"
fetch_if_stale "finance-dealing-with-debt"   "https://consumer.ftc.gov/articles/coping-debt"
fetch_if_stale "finance-irs-tax-basics"      "https://www.irs.gov/filing"

# Nutrition
fetch_if_stale "nutrition-safe-food-handling" "https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling"
fetch_if_stale "nutrition-myplate-basics"     "https://www.myplate.gov/eat-healthy/what-is-myplate"

# Auto
fetch_if_stale "auto-maintenance-schedule"   "https://www.fueleconomy.gov/feg/maintain.shtml"
fetch_if_stale "auto-winterize"              "https://www.dmv.org/how-to-guides/winterize-car.php"

# ── current events (always refresh — daily content) ──────────────────────────
echo ""
echo "Fetching current events..."

current_events_file="$base_dir/notes/current-events.md"
tmp_events="$(mktemp /tmp/jarvis-events-XXXXXX.md)"
today="$(date '+%A, %B %-d, %Y')"

printf '# Current Events\n<!-- Last updated: %s -->\n\n' "$today" > "$tmp_events"

# News — Google News RSS
printf '## US & World News\n' >> "$tmp_events"
curl -L --silent --max-time 15 "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en" 2>/dev/null \
  | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | grep -v "Google News" \
  | head -15 | while read -r line; do printf -- '- %s\n' "$line"; done >> "$tmp_events" \
  || printf -- '- (could not fetch)\n' >> "$tmp_events"
printf '\n' >> "$tmp_events"

# Entertainment — Google News entertainment
printf '## Entertainment\n' >> "$tmp_events"
curl -L --silent --max-time 15 "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en" 2>/dev/null \
  | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | grep -v "Google News" \
  | head -10 | while read -r line; do printf -- '- %s\n' "$line"; done >> "$tmp_events" \
  || printf -- '- (could not fetch)\n' >> "$tmp_events"
printf '\n' >> "$tmp_events"

# Sports — Google News sports
printf '## Sports\n' >> "$tmp_events"
curl -L --silent --max-time 15 "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en" 2>/dev/null \
  | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | grep -v "Google News" \
  | head -10 | while read -r line; do printf -- '- %s\n' "$line"; done >> "$tmp_events" \
  || printf -- '- (could not fetch)\n' >> "$tmp_events"
printf '\n' >> "$tmp_events"

# Key facts block
printf '## Key Facts\n' >> "$tmp_events"
printf -- '- Current US President: Donald Trump (took office January 20, 2025)\n' >> "$tmp_events"
printf -- '- Last updated: %s\n' "$today" >> "$tmp_events"

# Move into place
mv "$tmp_events" "$current_events_file"
echo "  current events updated"

echo ""
echo "Done — $ok updated, $skip skipped, $fail failed."
[[ $skip -gt 0 ]] && echo "  (skipped = pages fetched within the last 7 days, still current)"
echo "  Note: base knowledge comes from model training — only web-fetched pages update here."
