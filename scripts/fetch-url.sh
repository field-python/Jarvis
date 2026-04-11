#!/usr/bin/env bash
# fetch-url.sh — save a webpage to the Jarvis archive
# Usage: fetch-url.sh <url> [short-name]

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <url> [short-name]"
  exit 1
fi

url="$1"
name="${2:-}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
pages_dir="$base_dir/pages"
index_file="$base_dir/index/sources.md"
user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"

mkdir -p "$pages_dir" "$base_dir/index"

if [[ -z "$name" ]]; then
  host_path="${url#http://}"
  host_path="${host_path#https://}"
  host_path="${host_path%%\?*}"
  host_path="${host_path%%\#*}"
  name="$(printf '%s' "$host_path" | tr '/:' '__')"
fi

output="$pages_dir/$name.html"

if command -v curl >/dev/null 2>&1; then
  curl -L --fail --silent --show-error \
    -A "$user_agent" \
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
    "$url" -o "$output"
elif command -v wget >/dev/null 2>&1; then
  wget --user-agent="$user_agent" -O "$output" "$url"
else
  echo "Neither curl nor wget is installed."
  exit 1
fi

stamp="$(date +%F)"
printf -- '- `pages/%s.html` - %s - saved %s\n' "$name" "$url" "$stamp" >> "$index_file"
echo "Saved: $output"
