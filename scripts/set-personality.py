#!/usr/bin/env python3
"""set-personality.py — Set Jarvis personality / humanity level."""
import sys
import os
import tty
import termios
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config" / "personality.conf"

LEVELS = {
    "1": ("Protocol",   "Pure function. Direct answers, no character, no small talk."),
    "2": ("Character",  "Jarvis as a character — dry wit, opinions, natural small talk. (default)"),
    "3": ("Ghost",      "Fully human responses. Never breaks. Can't tell it's AI."),
}

CYAN  = "\033[96m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
GREEN = "\033[92m"
RESET = "\033[0m"
HR    = "━" * 40


def current_level():
    if CONFIG_FILE.exists():
        val = CONFIG_FILE.read_text(encoding="utf-8").strip()
        if val in LEVELS:
            return val
    return "2"


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return "\x1b[" + ch3
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def draw_menu(selected):
    print("\033[H\033[J", end="")  # clear screen
    print(f"\n{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Personality Level{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}\n")
    for lvl, (name, desc) in LEVELS.items():
        if lvl == selected:
            print(f"  {GREEN}{BOLD}▶  {lvl}.  {name}{RESET}")
            print(f"     {DIM}{desc}{RESET}")
        else:
            print(f"     {lvl}.  {name}")
            print(f"     {DIM}{desc}{RESET}")
        print()
    print(f"  {DIM}↑/↓ or 1/2/3 to select  |  Enter to confirm  |  ESC to cancel{RESET}\n")


def main():
    # Allow setting directly: Jarvis personality 2
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
        if choice in LEVELS:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(f"{choice}\n", encoding="utf-8")
            name, desc = LEVELS[choice]
            print(f"Personality set to Level {choice} — {name}")
            print(f"  {desc}")
            return
        else:
            print(f"Invalid level: {choice}. Choose 1, 2, or 3.")
            sys.exit(1)

    # Interactive arrow-key selection
    keys = list(LEVELS.keys())  # ["1", "2", "3"]
    cur = current_level()
    selected = cur

    draw_menu(selected)

    try:
        while True:
            key = getch()

            if key in ("\x1b[A",):  # up arrow
                idx = keys.index(selected)
                selected = keys[(idx - 1) % len(keys)]
                draw_menu(selected)

            elif key in ("\x1b[B",):  # down arrow
                idx = keys.index(selected)
                selected = keys[(idx + 1) % len(keys)]
                draw_menu(selected)

            elif key in LEVELS:  # pressing 1, 2, or 3 directly
                selected = key
                draw_menu(selected)

            elif key in ("\r", "\n"):  # Enter — confirm
                break

            elif key in ("\x1b", "q", "Q"):  # ESC or q — cancel
                print("\nCancelled.")
                return

    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(f"{selected}\n", encoding="utf-8")
    name, desc = LEVELS[selected]
    print(f"\nPersonality set to Level {selected} — {name}")
    print(f"  {desc}\n")


if __name__ == "__main__":
    main()
