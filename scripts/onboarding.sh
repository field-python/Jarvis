#!/usr/bin/env bash
# onboarding.sh — first-run welcome and setup for Jarvis
# Usage: onboarding.sh <jarvis_base> [original args...]
# Called automatically by the launcher on first run.

set -uo pipefail

jarvis_base="${1:-}"
shift || true
original_args=("$@")

if [[ -z "$jarvis_base" ]]; then
  jarvis_base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
fi

venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"

clear
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Welcome to Jarvis — Your Offline AI Assistant"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Jarvis runs completely offline. No internet required"
echo "  for most features. Let's get you set up in 60 seconds."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Step 1: Name ──────────────────────────────────────────────────────────────
read -r -p "  Your first name (or press Enter to skip): " user_name
if [[ -n "$user_name" ]]; then
  printf -- '- My name is %s\n' "$user_name" >> "$jarvis_base/memory/user-memory.md"
  echo "  Nice to meet you, $user_name."
fi
echo ""

# ── Step 2: Location ──────────────────────────────────────────────────────────
current_loc=""
if [[ -f "$jarvis_base/config/location.conf" ]]; then
  current_loc="$(grep -v '^\s*#' "$jarvis_base/config/location.conf" | head -1 | tr -d '\n' || true)"
fi

if [[ -n "$current_loc" ]]; then
  echo "  Location already set to: $current_loc"
  read -r -p "  Change it? (Enter to keep, or type new location): " new_loc
  if [[ -n "$new_loc" ]]; then
    printf '%s\n' "$new_loc" > "$jarvis_base/config/location.conf"
    echo "  Updated to: $new_loc"
  fi
else
  echo "  Where are you located? (used for weather and regional context)"
  read -r -p "  City, State  e.g. Anchorage, AK: " user_location
  if [[ -n "$user_location" ]]; then
    printf '%s\n' "$user_location" > "$jarvis_base/config/location.conf"
    echo "  Location set to: $user_location"
  fi
fi
echo ""

# ── Step 3: Extra content ─────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Expand Jarvis knowledge? (requires internet, ~5 min)"
echo ""
echo "    1. Download general knowledge"
echo "       Movies, music, sports, science, history, cooking..."
echo "    2. Skip — use built-in knowledge only"
echo ""
read -r -p "  Choice [1/2]: " content_choice
echo ""

if [[ "$content_choice" == "1" ]]; then
  echo "  Downloading general knowledge (~120 articles)..."
  echo ""
  "$venv_python" "$jarvis_base/scripts/download-general-content.py" all
  echo ""
  echo "  Rebuilding search index..."
  "$venv_python" "$jarvis_base/scripts/build-index.py"
  echo ""
fi

# ── Done ──────────────────────────────────────────────────────────────────────
touch "$jarvis_base/config/onboarding-done"

clear
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis is ready."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Jarvis \"your question\"        Ask anything"
echo "  Jarvis chat                   Start a conversation"
echo "  Jarvis voice                  Voice mode (wake word: Hey Jarvis)"
echo "  Jarvis news                   Today's headlines"
echo "  Jarvis weather                Current weather"
echo "  Jarvis help                   All commands"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Re-run the original command if there was one
if [[ ${#original_args[@]} -gt 0 ]]; then
  exec bash "$jarvis_base/Jarvis" "${original_args[@]}"
fi
