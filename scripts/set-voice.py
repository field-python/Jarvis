#!/usr/bin/env python3
"""
set-voice.py — Interactive Piper voice selector for Jarvis.
Downloads voices on demand and saves the selection to config/voice.conf.
"""
import sys
import os
import urllib.request
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
voice_dir  = base_dir / "voice"
config_dir = base_dir / "config"
tts_script = base_dir / "scripts" / "tts.sh"

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

VOICES = [
    {
        "name":  "en_GB-alan-medium",
        "label": "British Male   — Alan    (current default)",
        "path":  "en/en_GB/alan/medium",
    },
    {
        "name":  "en_US-ryan-high",
        "label": "US Male        — Ryan    (clear, natural)",
        "path":  "en/en_US/ryan/high",
    },
    {
        "name":  "en_US-joe-medium",
        "label": "US Male        — Joe     (deeper tone)",
        "path":  "en/en_US/joe/medium",
    },
    {
        "name":  "en_US-amy-medium",
        "label": "US Female      — Amy",
        "path":  "en/en_US/amy/medium",
    },
    {
        "name":  "en_US-lessac-medium",
        "label": "US Female      — Lessac  (warm, clear)",
        "path":  "en/en_US/lessac/medium",
    },
    {
        "name":  "en_GB-jenny_dioco-medium",
        "label": "British Female — Jenny",
        "path":  "en/en_GB/jenny_dioco/medium",
    },
]

BOLD  = "\033[1m"
CYAN  = "\033[96m"
DIM   = "\033[2m"
GREEN = "\033[92m"
RESET = "\033[0m"
HR    = "━" * 44


def current_voice() -> str:
    conf = config_dir / "voice.conf"
    if conf.exists():
        v = conf.read_text().strip()
        if v:
            return v
    return "en_GB-alan-medium"


def is_downloaded(name: str) -> bool:
    return (voice_dir / f"{name}.onnx").exists()


def download_voice(voice: dict) -> bool:
    name = voice["name"]
    path = voice["path"]
    voice_dir.mkdir(parents=True, exist_ok=True)

    for ext in (".onnx", ".onnx.json"):
        dest = voice_dir / f"{name}{ext}"
        if dest.exists():
            continue
        url = f"{BASE_URL}/{path}/{name}{ext}"
        print(f"  Downloading {name}{ext} ...", end=" ", flush=True)
        try:
            urllib.request.urlretrieve(url, dest)
            print("done.")
        except Exception as e:
            print(f"FAILED ({e})")
            try:
                dest.unlink()
            except OSError:
                pass
            return False
    return True



def main():
    cur = current_voice()

    print(f"\n{BOLD}{CYAN}{HR}")
    print(f"  Jarvis  |  Voice Selection")
    print(f"{HR}{RESET}\n")

    for i, v in enumerate(VOICES, 1):
        downloaded = is_downloaded(v["name"])
        active     = v["name"] == cur
        dl_tag     = f"  {DIM}[ready]{RESET}"   if downloaded and not active else ""
        cur_tag    = f"  {GREEN}◀ active{RESET}" if active else ""
        nd_tag     = f"  {DIM}[download on select]{RESET}" if not downloaded else ""
        print(f"  {BOLD}{i}.{RESET} {v['label']}{cur_tag}{dl_tag}{nd_tag}")

    print(f"\n{DIM}  Enter number to switch  |  Enter to cancel{RESET}")
    try:
        raw = input("\n  Choice: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return

    if not raw:
        print("  No change.")
        return

    if not raw.isdigit() or not (1 <= int(raw) <= len(VOICES)):
        print("  Invalid choice.")
        return

    voice = VOICES[int(raw) - 1]

    if voice["name"] == cur:
        print(f"\n  Already using {voice['label'].strip()}.")
        return

    if not is_downloaded(voice["name"]):
        print()
        ok = download_voice(voice)
        if not ok:
            print(f"\n  Download failed. Voice not changed.")
            return

    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "voice.conf").write_text(voice["name"] + "\n")
    print(f"\n  {GREEN}Voice set to:{RESET} {voice['label'].strip()}")
    print(f"  Playing preview...\n")
    import subprocess
    subprocess.run(["bash", str(tts_script), "Jarvis online. How may I assist you?"])
    print(f"\n{HR}\n")


if __name__ == "__main__":
    main()
