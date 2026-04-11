#!/usr/bin/env bash
# install-voice.sh — install Whisper (STT) + Piper (TTS) for Jarvis voice mode
# Run once: bash /media/.../ARCHIVE/jarvis/scripts/install-voice.sh

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
venv_pip="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/pip"
voice_dir="$base_dir/voice"

mkdir -p "$voice_dir"

echo "=== Jarvis Voice Setup ==="
echo ""

# ── 1. Check arecord ──────────────────────────────────────────────────────────
echo "[1/4] Checking audio tools..."
if ! command -v arecord >/dev/null 2>&1; then
  echo "  arecord not found. Installing alsa-utils..."
  sudo apt-get install -y alsa-utils
else
  echo "  arecord: OK"
fi

if ! command -v aplay >/dev/null 2>&1; then
  echo "  aplay not found — install alsa-utils manually: sudo apt install alsa-utils"
  exit 1
fi
echo "  aplay: OK"

# ── 2. Python packages ────────────────────────────────────────────────────────
echo ""
echo "[2/4] Installing Python packages (faster-whisper + piper-tts + wake word)..."
# pyaudio needs portaudio headers first
if ! dpkg -l libportaudio2 >/dev/null 2>&1; then
  echo "  installing portaudio (required for pyaudio)..."
  sudo apt-get install -y portaudio19-dev python3-pyaudio
fi
"$venv_pip" install --quiet --upgrade faster-whisper piper-tts pyaudio openwakeword
echo "  done"

# ── 3. Download Piper voice model ─────────────────────────────────────────────
echo ""
echo "[3/4] Downloading Piper voice model (en_US-lessac-medium)..."
model_base="$voice_dir/en_US-lessac-medium"
hf_base="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium"

if [[ -f "${model_base}.onnx" && -f "${model_base}.onnx.json" ]]; then
  echo "  model already downloaded, skipping"
else
  echo "  downloading .onnx model (~60MB)..."
  curl -L --progress-bar -o "${model_base}.onnx" \
    "${hf_base}/en_US-lessac-medium.onnx"
  echo "  downloading model config..."
  curl -L --silent -o "${model_base}.onnx.json" \
    "${hf_base}/en_US-lessac-medium.onnx.json"
  echo "  done"
fi

# ── 4. Test ───────────────────────────────────────────────────────────────────
echo ""
echo "[4/4] Testing TTS..."
piper_bin="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/piper"
if echo "Jarvis voice setup complete." | "$piper_bin" \
    --model "${model_base}.onnx" \
    --output_raw 2>/dev/null \
    | aplay -r 22050 -f S16_LE -t raw -q 2>/dev/null; then
  echo "  TTS test passed — you should have heard a voice."
else
  echo "  TTS test failed. Check your audio output (speakers/headphones plugged in?)."
fi

echo ""
echo "=== Voice setup complete ==="
echo "Run: Jarvis voice"
