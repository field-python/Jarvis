#!/usr/bin/env bash
# refresh-pdf-index.sh — extract text from PDFs so they become searchable
# Run this after adding new PDFs to jarvis/pdfs/

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
pdf_dir="$base_dir/pdfs"
cache_dir="$base_dir/.cache/pdftext"

mkdir -p "$cache_dir"

if ! command -v pdftotext >/dev/null 2>&1; then
  echo "pdftotext is required. Install with: sudo apt install poppler-utils"
  exit 1
fi

count=0
for pdf in "$pdf_dir"/*.pdf; do
  [[ -f "$pdf" ]] || continue
  out="$cache_dir/$(basename "$pdf").txt"
  if [[ ! -f "$out" || "$pdf" -nt "$out" ]]; then
    pdftotext "$pdf" "$out" 2>/dev/null && echo "Indexed: $(basename "$pdf")" && ((count++)) || true
  fi
done

echo "Done. $count PDF(s) indexed."
