#!/usr/bin/env python3
"""set-personality.py — Set Jarvis personality / humanity level."""
import sys
import os
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config" / "personality.conf"

LEVELS = {
    "1": ("Protocol",   "Pure function. Direct answers, no character, no small talk."),
    "2": ("Character",  "Jarvis as a character — dry wit, opinions, natural small talk. (default)"),
    "3": ("Ghost",      "Fully human responses. Never breaks. Can't tell it's AI."),
}

def current_level():
    if CONFIG_FILE.exists():
        val = CONFIG_FILE.read_text(encoding="utf-8").strip()
        if val in LEVELS:
            return val
    return "2"

def main():
    # Allow setting directly: Jarvis personality 2
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
        if choice in LEVELS:
            CONFIG_FILE.write_text(f"{choice}\n", encoding="utf-8")
            name, desc = LEVELS[choice]
            print(f"Personality set to Level {choice} — {name}")
            print(f"  {desc}")
            return
        else:
            print(f"Invalid level: {choice}. Choose 1, 2, or 3.")
            sys.exit(1)

    # Interactive selection
    cur = current_level()
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Jarvis  |  Personality Level")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    for lvl, (name, desc) in LEVELS.items():
        marker = " ◀ current" if lvl == cur else ""
        print(f"  {lvl}.  {name}{marker}")
        print(f"       {desc}")
        print()

    try:
        choice = input("  Choose level [1/2/3, Enter to keep current]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if not choice:
        print(f"Keeping Level {cur} — {LEVELS[cur][0]}.")
        return

    if choice not in LEVELS:
        print("Invalid choice. No changes made.")
        sys.exit(1)

    CONFIG_FILE.write_text(f"{choice}\n", encoding="utf-8")
    name, desc = LEVELS[choice]
    print()
    print(f"Personality set to Level {choice} — {name}")
    print(f"  {desc}")

if __name__ == "__main__":
    main()
