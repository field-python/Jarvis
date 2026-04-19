#!/usr/bin/env python3
"""
set-voice.py — Interactive Piper voice selector for Jarvis.
Downloads voices on demand and saves the selection to config/voice.conf.
"""
import sys
import os
import tty
import termios
import select
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


def getch():
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                rest = os.read(fd, 2).decode("utf-8", errors="replace")
                if rest and rest[0] == "O" and len(rest) > 1:
                    return "\x1b[" + rest[1]
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


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



def draw_menu(selected: int, cur: str):
    os.system("clear")
    print(f"\n{BOLD}{CYAN}{HR}")
    print(f"  Jarvis  |  Voice Selection")
    print(f"{HR}{RESET}\n")
    for i, v in enumerate(VOICES):
        downloaded = is_downloaded(v["name"])
        active     = v["name"] == cur
        cur_tag    = f"  {GREEN}◀ active{RESET}" if active else ""
        dl_tag     = f"  {DIM}[ready]{RESET}"    if downloaded and not active else ""
        nd_tag     = f"  {DIM}[download on select]{RESET}" if not downloaded else ""
        num = f"{i + 1}."
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {v['label']}{RESET}{cur_tag}{dl_tag}{nd_tag}")
        else:
            print(f"  {DIM}{num}    {v['label']}{RESET}{cur_tag}{dl_tag}{nd_tag}")
    print(f"\n  {DIM}↑↓ to select  |  Enter to activate  |  Q/ESC to exit{RESET}\n")


def main():
    cur      = current_voice()
    selected = next((i for i, v in enumerate(VOICES) if v["name"] == cur), 0)

    while True:
        draw_menu(selected, cur)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            os.system("clear")
            return

        elif key == "\x1b[A":
            selected = (selected - 1) % len(VOICES)

        elif key == "\x1b[B":
            selected = (selected + 1) % len(VOICES)

        elif key.isdigit():
            n = int(key)
            if 1 <= n <= len(VOICES):
                selected = n - 1

        elif key in ("\r", "\n"):
            voice = VOICES[selected]
            if voice["name"] == cur:
                print(f"\n  Already using {voice['label'].strip()}.")
                getch()
                continue

            if not is_downloaded(voice["name"]):
                print()
                ok = download_voice(voice)
                if not ok:
                    print(f"\n  Download failed. Voice not changed.")
                    getch()
                    continue

            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "voice.conf").write_text(voice["name"] + "\n")
            cur = voice["name"]
            os.system("clear")
            print(f"\n{BOLD}{CYAN}{HR}")
            print(f"  Jarvis  |  Voice Selection")
            print(f"{HR}{RESET}\n")
            print(f"  {GREEN}Voice set to:{RESET} {voice['label'].strip()}")
            print(f"  Playing preview...\n")
            import subprocess
            subprocess.run(["bash", str(tts_script), "Jarvis online. How may I assist you?"])
            print(f"\n  {DIM}Any key to continue...{RESET}", end="", flush=True)
            getch()
            print()


if __name__ == "__main__":
    main()
