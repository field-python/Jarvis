#!/usr/bin/env bash
# timer.sh — Countdown timer with spoken alert via Jarvis TTS
# Usage: timer.sh <duration>
# Examples:
#   timer.sh 10m
#   timer.sh 30s
#   timer.sh 1h
#   timer.sh "10 minutes"
#   timer.sh 1h30m

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
tts_script="$base_dir/scripts/tts.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: Jarvis timer <duration>"
  echo ""
  echo "Examples:"
  echo "  Jarvis timer 1h"
  echo "  Jarvis timer 10m"
  echo "  Jarvis timer 30s"
  echo "  Jarvis timer 1h30m"
  echo "  Jarvis timer \"10 minutes\""
  exit 1
fi

input="$*"

# ── parse duration to seconds ─────────────────────────────────────────────────
parse_seconds() {
  local raw="${1,,}"  # lowercase
  # Remove spaces around units
  raw="${raw// /}"

  local total=0

  # Handle natural language: "10 minutes", "5 seconds", "1 hour"
  raw="${raw/minutes/m}"
  raw="${raw/minute/m}"
  raw="${raw/seconds/s}"
  raw="${raw/second/s}"
  raw="${raw/hours/h}"
  raw="${raw/hour/h}"
  raw="${raw/mins/m}"
  raw="${raw/min/m}"
  raw="${raw/secs/s}"
  raw="${raw/sec/s}"
  raw="${raw/hrs/h}"
  raw="${raw/hr/h}"

  # Parse hours
  if [[ "$raw" =~ ([0-9]+)h ]]; then
    total=$((total + ${BASH_REMATCH[1]} * 3600))
  fi
  # Parse minutes
  if [[ "$raw" =~ ([0-9]+)m ]]; then
    total=$((total + ${BASH_REMATCH[1]} * 60))
  fi
  # Parse seconds
  if [[ "$raw" =~ ([0-9]+)s ]]; then
    total=$((total + ${BASH_REMATCH[1]}))
  fi
  # Plain number with no unit = minutes
  if [[ "$raw" =~ ^[0-9]+$ ]]; then
    total=$((raw * 60))
  fi

  echo "$total"
}

total_seconds="$(parse_seconds "$input")"

if [[ "$total_seconds" -le 0 ]]; then
  echo "Couldn't parse duration: $input"
  echo "Try: 10m, 30s, 1h, 1h30m, or \"10 minutes\""
  exit 1
fi

# ── format duration for display ───────────────────────────────────────────────
format_duration() {
  local s=$1
  local h=$((s / 3600))
  local m=$(( (s % 3600) / 60 ))
  local sec=$((s % 60))
  local out=""
  [[ $h -gt 0 ]] && out="${h}h "
  [[ $m -gt 0 ]] && out="${out}${m}m "
  [[ $sec -gt 0 ]] && out="${out}${sec}s"
  echo "${out% }"
}

duration_label="$(format_duration "$total_seconds")"

# ── spoken label ──────────────────────────────────────────────────────────────
spoken_label() {
  local s=$1
  local h=$((s / 3600))
  local m=$(( (s % 3600) / 60 ))
  local sec=$((s % 60))
  local parts=()
  [[ $h -gt 0 ]] && parts+=("$h hour$( [[ $h -gt 1 ]] && echo s )")
  [[ $m -gt 0 ]] && parts+=("$m minute$( [[ $m -gt 1 ]] && echo s )")
  [[ $sec -gt 0 ]] && parts+=("$sec second$( [[ $sec -gt 1 ]] && echo s )")
  local IFS=", "
  echo "${parts[*]}"
}

spoken="$(spoken_label "$total_seconds")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Timer set: $duration_label"
echo "  Press Ctrl+C to cancel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "$tts_script" "Timer started. $spoken on the clock." 2>/dev/null &

remaining=$total_seconds
while [[ $remaining -gt 0 ]]; do
  label="$(format_duration "$remaining")"
  printf "\r  ⏱  %s remaining   " "$label"

  # Spoken warnings
  if [[ $remaining -eq 300 ]]; then
    bash "$tts_script" "Five minutes remaining." 2>/dev/null &
  elif [[ $remaining -eq 60 ]]; then
    bash "$tts_script" "One minute remaining." 2>/dev/null &
  elif [[ $remaining -eq 30 ]]; then
    bash "$tts_script" "Thirty seconds remaining." 2>/dev/null &
  elif [[ $remaining -eq 10 ]]; then
    bash "$tts_script" "Ten seconds." 2>/dev/null &
  fi

  sleep 1
  remaining=$((remaining - 1))
done

printf "\r  ✓  Timer done!               \n"
echo ""
bash "$tts_script" "Time's up." 2>/dev/null
