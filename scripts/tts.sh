#!/usr/bin/env bash
# tts.sh — text to speech via Piper
# Usage: echo "text" | tts.sh
#    or: tts.sh "text to speak"

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
piper_bin="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/piper"
model="$base_dir/voice/en_GB-alan-medium.onnx"

if [[ ! -f "$piper_bin" ]]; then
  echo "[Jarvis TTS] Piper not installed. Run: Jarvis install-voice" >&2
  exit 1
fi

if [[ ! -f "$model" ]]; then
  echo "[Jarvis TTS] Voice model not found. Run: Jarvis install-voice" >&2
  exit 1
fi

# Get text from argument or stdin
if [[ $# -ge 1 ]]; then
  text="$*"
else
  text="$(cat)"
fi

[[ -z "$text" ]] && exit 0

# Strip markdown formatting so it sounds natural when spoken
clean_text="$(printf '%s' "$text" \
  | sed 's/```[^`]*```/ /g' \
  | sed 's/`[^`]*`/ /g' \
  | sed 's/^#+\s*//gm' \
  | sed 's/\*\*\([^*]*\)\*\*/\1/g' \
  | sed 's/\*\([^*]*\)\*/\1/g' \
  | sed 's/^[-*]\s*/  /gm' \
  | sed 's/\[.*\](.*)/link/g' \
  | tr -s ' \n' ' ')"

tmp="$(mktemp /tmp/jarvis-tts-XXXXXX.raw)"
printf '%s' "$clean_text" \
  | "$piper_bin" --model "$model" --output_raw 2>/dev/null \
  > "$tmp"
sox -t raw -r 22050 -e signed -b 16 -c 1 "$tmp" -t wav - 2>/dev/null \
  | paplay --rate=22050 --format=s16le --channels=1 2>/dev/null
rm -f "$tmp"
