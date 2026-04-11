#!/usr/bin/env python3
"""onboarding.py — first-run welcome and setup for Jarvis"""
import sys
import os
import readline
import subprocess
from pathlib import Path

jarvis_base   = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent
original_args = sys.argv[2:] if len(sys.argv) > 2 else []

memory_file   = jarvis_base / "memory" / "user-memory.md"
location_conf = jarvis_base / "config" / "location.conf"
memory_file.parent.mkdir(parents=True, exist_ok=True)
location_conf.parent.mkdir(parents=True, exist_ok=True)

os.system("clear")
print()
print("━" * 58)
print("  Welcome to Jarvis — Your Offline AI Assistant")
print("━" * 58)
print()
print("  Jarvis runs completely offline. No internet required")
print("  for most features. Let's get you set up in 60 seconds.")
print()
print("━" * 58)
print()

# ── Step 1: Name ──────────────────────────────────────────────────────────────
try:
    user_name = input("  Your first name (or press Enter to skip): ").strip()
except (EOFError, KeyboardInterrupt):
    user_name = ""

if user_name:
    with memory_file.open("a", encoding="utf-8") as f:
        f.write(f"- My name is {user_name}\n")
    print(f"  Nice to meet you, {user_name}.")
print()

# ── Step 2: Location ──────────────────────────────────────────────────────────
current_loc = ""
if location_conf.exists():
    lines = location_conf.read_text(encoding="utf-8").strip().splitlines()
    current_loc = lines[0] if lines else ""

try:
    if current_loc:
        print(f"  Location already set to: {current_loc}")
        new_loc = input("  Change it? (Enter to keep, or type new location): ").strip()
        if new_loc:
            location_conf.write_text(new_loc + "\n", encoding="utf-8")
            print(f"  Updated to: {new_loc}")
    else:
        print("  Where are you located? (used for weather and regional context)")
        user_location = input("  City, State  e.g. Anchorage, AK: ").strip()
        if user_location:
            location_conf.write_text(user_location + "\n", encoding="utf-8")
            print(f"  Location set to: {user_location}")
except (EOFError, KeyboardInterrupt):
    pass
print()

# ── Step 3: Optional content download ─────────────────────────────────────────
print("━" * 58)
print("  Expand Jarvis knowledge? (requires internet, ~5 min)")
print()
print("    1. Download general knowledge")
print("       Movies, music, sports, science, history, cooking...")
print("    2. Skip — use built-in knowledge only")
print()

try:
    content_choice = input("  Choice [1/2]: ").strip()
except (EOFError, KeyboardInterrupt):
    content_choice = "2"

print()
if content_choice == "1":
    download_script = jarvis_base / "scripts" / "download-general-content.py"
    build_script    = jarvis_base / "scripts" / "build-index.py"
    print("  Downloading general knowledge (~120 articles)...")
    print()
    subprocess.run([sys.executable, str(download_script), "all"])
    print()
    print("  Rebuilding search index...")
    subprocess.run([sys.executable, str(build_script)])
    print()

# ── Done ──────────────────────────────────────────────────────────────────────
(jarvis_base / "config" / "onboarding-done").touch()

os.system("clear")
print()
print("━" * 58)
print("  Jarvis is ready.")
print("━" * 58)
print()
print('  Jarvis "your question"        Ask anything')
print("  Jarvis chat                   Start a conversation")
print("  Jarvis voice                  Voice mode (wake word: Hey Jarvis)")
print("  Jarvis news                   Today's headlines")
print("  Jarvis weather                Current weather")
print("  Jarvis help                   All commands")
print()
print("━" * 58)
print()

# Re-run the original command if there was one
if original_args:
    launcher = jarvis_base / "Jarvis"
    os.execv("/usr/bin/env", ["env", "bash", str(launcher)] + original_args)
