#!/usr/bin/env python3
"""
stt.py — Speech-to-text using faster-whisper.
Usage: python3 stt.py <audio_file.wav>
Prints the transcription to stdout.
"""

import sys
import os

def transcribe(audio_path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[ERROR: faster-whisper not installed. Run: Jarvis install-voice]", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"[ERROR: audio file not found: {audio_path}]", file=sys.stderr)
        sys.exit(1)

    # Load model — downloads on first run to ~/.cache/huggingface/
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, language="en", vad_filter=True)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: stt.py <audio_file.wav>", file=sys.stderr)
        sys.exit(1)

    result = transcribe(sys.argv[1])
    print(result)
