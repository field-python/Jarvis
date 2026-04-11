#!/usr/bin/env bash
# voice.sh — Jarvis voice mode (push-to-talk loop)
# Press Enter to start recording, Enter again to stop.
# Ctrl+C or say "goodbye" to exit.

set -uo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
ask_script="$base_dir/scripts/ask.sh"
tts_script="$base_dir/scripts/tts.sh"
stt_script="$base_dir/scripts/stt.py"

tmp_audio="$(mktemp /tmp/jarvis-voice-XXXXXX.wav)"
record_pid=""
_exiting=0

# ── cleanup ───────────────────────────────────────────────────────────────────
cleanup() {
  [[ $_exiting -eq 1 ]] && return
  _exiting=1
  [[ -n "$record_pid" ]] && kill "$record_pid" 2>/dev/null || true
  rm -f "$tmp_audio"
  echo ""
  echo "Jarvis voice mode off."
}
trap 'cleanup; exit 0' INT TERM
trap cleanup EXIT

# ── check dependencies ────────────────────────────────────────────────────────
if ! command -v arecord >/dev/null 2>&1; then
  echo "arecord not found. Run: Jarvis install-voice"
  exit 1
fi
if [[ ! -f "${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/piper" ]]; then
  echo "Piper not installed. Run: Jarvis install-voice"
  exit 1
fi

# ── startup ───────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis Voice Mode  |  ON"
echo "  Enter → speak  |  Enter → stop  |  Ctrl+C → exit"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
bash "$tts_script" "Jarvis online. Press enter to speak." 2>/dev/null || true

# ── main loop ─────────────────────────────────────────────────────────────────
while true; do
  printf '\n[Press Enter to speak...] '
  read -r _ || break

  # Start recording
  rm -f "$tmp_audio"
  arecord -f S16_LE -r 16000 -c 1 -q "$tmp_audio" 2>/dev/null &
  record_pid=$!

  printf '[Recording... press Enter to stop] '
  read -r _ || { kill "$record_pid" 2>/dev/null; break; }

  # Stop recording
  kill "$record_pid" 2>/dev/null || true
  wait "$record_pid" 2>/dev/null || true
  record_pid=""

  # Require at least ~0.5s of audio (WAV header=44 bytes + ~16KB/s at 16kHz)
  audio_bytes="$(wc -c < "$tmp_audio" 2>/dev/null || echo 0)"
  if [[ "$audio_bytes" -lt 8000 ]]; then
    echo "No audio captured. Try again."
    continue
  fi

  # Transcribe
  printf 'Transcribing... '
  question="$("$venv_python" "$stt_script" "$tmp_audio" 2>/dev/null || true)"

  if [[ -z "$question" ]]; then
    echo "Couldn't make that out. Try again."
    continue
  fi

  echo "You: $question"

  # Exit phrases
  lower_q="$(printf '%s' "$question" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower_q" =~ (goodbye|shut down|exit|stop jarvis|turn off) ]]; then
    bash "$tts_script" "Goodbye." 2>/dev/null || true
    exit 0
  fi

  # Get answer
  printf 'Thinking... '
  answer="$(env JARVIS_MODE=voice "$ask_script" "$question" 2>/dev/null || true)"

  if [[ -z "$answer" ]]; then
    echo "No response. Try again."
    continue
  fi

  echo "Jarvis: $answer"
  echo ""

  bash "$tts_script" "$answer" 2>/dev/null || true
done
