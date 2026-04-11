#!/usr/bin/env bash
# search.sh — search the Jarvis local archive
# Usage: search.sh <search terms>

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <search terms>"
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
config_file="$base_dir/config/archive-roots.txt"
cache_dir="$base_dir/.cache/pdftext"

if ! command -v rg >/dev/null 2>&1; then
  echo "ripgrep (rg) is required. Install with: sudo apt install ripgrep"
  exit 1
fi

declare -a roots=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -d "$line" ]] || continue
  roots+=("$line")
done < "$config_file"

if [[ ${#roots[@]} -eq 0 ]]; then
  echo "No readable archive roots in $config_file"
  exit 1
fi

rg -n -S -m 1 \
  --glob '*.md' \
  --glob '*.txt' \
  --glob '*.html' \
  --glob '*.htm' \
  --glob '*.csv' \
  --glob '!*.zim' \
  --glob '!*.aria2' \
  "$*" \
  "${roots[@]}" \
  "$cache_dir" 2>/dev/null \
  | sed "s|$cache_dir/||" \
  | sed 's|\.pdf\.txt:|.pdf:|' \
  | grep -vi 'breadcrumb\|<nav\|header__\|footer\|javascript\|cookie\|privacy policy' \
  | grep -vi 'skip to main content\|aria-\|og:\|viewport\|favicon\|siteassets' \
  | grep -vi '/index/improvements/\|/\.cache/' \
  || true
