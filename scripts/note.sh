#!/usr/bin/env bash
# note.sh — save a quick note to the Jarvis archive
# Usage:
#   note.sh "text"     — save a one-liner note immediately
#   note.sh            — open editor for a longer note

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
notes_dir="$base_dir/notes/personal-notes"
mkdir -p "$notes_dir"

stamp="$(date +%Y-%m-%d)"
ts="$(date +%H:%M)"
daily_file="$notes_dir/$stamp.md"

# Ensure daily file has a header
if [[ ! -f "$daily_file" ]]; then
  printf '# Notes — %s\n\n' "$stamp" > "$daily_file"
fi

if [[ $# -ge 1 ]]; then
  # ── quick one-liner note ───────────────────────────────────────────────────
  note_text="$*"
  printf '**%s** %s\n\n' "$ts" "$note_text" >> "$daily_file"
  echo "Note saved: $daily_file"
else
  # ── editor mode ───────────────────────────────────────────────────────────
  tmp="$(mktemp /tmp/jarvis-note-XXXXXX.md)"
  printf '<!-- Type your note below, save and close to save it -->\n\n' > "$tmp"

  editor="${VISUAL:-${EDITOR:-nano}}"
  "$editor" "$tmp"

  # Strip the comment line and blank lines at top
  note_text="$(sed '/^<!--/d' "$tmp" | sed '/./,$!d')"
  rm -f "$tmp"

  if [[ -z "$note_text" ]]; then
    echo "Empty note — nothing saved."
    exit 0
  fi

  printf '**%s**\n\n%s\n\n' "$ts" "$note_text" >> "$daily_file"
  echo "Note saved: $daily_file"
fi
