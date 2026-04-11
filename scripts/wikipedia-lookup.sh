#!/usr/bin/env bash
# wikipedia-lookup.sh — extract a text summary from the local Wikipedia ZIM
# Usage: wikipedia-lookup.sh <query>
# Set WIKIPEDIA_OPEN=1 to also open the article in a browser

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
port="${WIKIPEDIA_PORT:-8091}"
host="${WIKIPEDIA_HOST:-127.0.0.1}"
open_browser="${WIKIPEDIA_OPEN:-0}"

if [[ $# -lt 1 ]]; then exit 0; fi

# ── find ZIM file ─────────────────────────────────────────────────────────────
# Check config file first, then fall back to jarvis/wikipedia/*.zim
zim_file=""
wiki_conf="$base_dir/config/wikipedia.conf"
if [[ -f "$wiki_conf" ]]; then
  configured="$(grep -v '^\s*#' "$wiki_conf" | head -1 | tr -d '\n')"
  [[ -f "$configured" ]] && zim_file="$configured"
fi

if [[ -z "$zim_file" ]]; then
  for f in "$base_dir/wikipedia"/*.zim; do
    [[ -f "$f" ]] && zim_file="$f" && break
  done
fi

[[ -z "$zim_file" ]] && exit 0

command -v kiwix-serve  >/dev/null 2>&1 || exit 0
command -v kiwix-search >/dev/null 2>&1 || exit 0
command -v curl         >/dev/null 2>&1 || exit 0

query="$*"
zim_name="$(basename "$zim_file" .zim)"
base_url="http://${host}:${port}/content/${zim_name}"

# ── start kiwix-serve if not running ──────────────────────────────────────────
if ! curl -fsS "http://${host}:${port}/nojs" >/dev/null 2>&1; then
  kiwix-serve -d -i "$host" -p "$port" "$zim_file" >/dev/null 2>&1 || true
  sleep 2
fi

# ── search for best matching article title ────────────────────────────────────
first_title="$(kiwix-search -s "$zim_file" "$query" 2>/dev/null | sed -n '1p' || true)"
[[ -z "$first_title" ]] && exit 0

slug="$(printf '%s' "$first_title" | sed 's/ /_/g')"
article_url="${base_url}/${slug}"

# ── fetch article and strip to plain text ─────────────────────────────────────
article_text="$(
  curl -fsS "$article_url" 2>/dev/null \
  | perl -0pe \
      's/<script.*?<\/script>//sg;
       s/<style.*?<\/style>//sg;
       s/<[^>]+>/ /g;
       s/&nbsp;/ /g; s/&amp;/\&/g; s/&#160;/ /g; s/&lt;/</g; s/&gt;/>/g;
       s/\s+/ /g' \
  | fold -s -w 120 \
  | sed -n '1,30p'
)"

[[ -z "$article_text" ]] && exit 0

printf 'Wikipedia (%s):\n%s\n' "$first_title" "$article_text"

# ── open in browser if requested ──────────────────────────────────────────────
if [[ "$open_browser" == "1" ]]; then
  xdg-open "$article_url" >/dev/null 2>&1 &
fi
