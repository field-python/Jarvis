#!/usr/bin/env python3
"""
menu.py — Interactive Jarvis command menu
Arrow keys or number to select, Enter to confirm, Q to quit.
"""

import sys
import os
import subprocess
import tty
import termios

JARVIS = os.environ.get("JARVIS_LAUNCHER", os.path.expanduser("~/Jarvis"))

MENU = [
    # (label, command_args, needs_input, input_prompt)

    # ── Ask ──────────────────────────────────────────────────────────────────
    ("Ask a question",          ["ask"],          True,  "Question: "),
    ("Brief answer",            ["brief"],        True,  "Question: "),
    ("Detailed answer",         ["detailed"],     True,  "Question: "),
    ("Cite sources",            ["cite"],         True,  "Question: "),
    ("Web search",              ["web"],          True,  "Search: "),

    # ── Learn ─────────────────────────────────────────────────────────────────
    ("Code help",               ["code"],         True,  "Describe what to build: "),
    ("Learn to code",           ["learn"],        True,  "Topic (e.g. Python for loops): "),
    ("Language Hub",            ["language"],     False, ""),

    # ── Conversation ──────────────────────────────────────────────────────────
    ("Chat mode",               ["chat"],         False, ""),
    ("Voice mode",              ["voice"],        False, ""),

    # ── Notes & Memory ────────────────────────────────────────────────────────
    ("Save a note",             ["note"],         True,  "Note: "),
    ("View today's notes",      ["notes"],        False, ""),
    ("Remember a fact",         ["remember"],     True,  "Fact to remember: "),

    # ── Recipes ───────────────────────────────────────────────────────────────
    ("Browse recipes",          ["recipe", "list"],  False, ""),
    ("Search recipes",          ["recipe"],          True,  "Recipe or ingredient: "),
    ("Recipe from ingredients", ["recipe", "suggest"], True, "What do you have on hand: "),

    # ── Skills & Reference ────────────────────────────────────────────────────
    ("Skill of the day",        ["skill"],        False, ""),
    ("First Aid reference",     ["firstaid"],     True,  "Topic (e.g. hypothermia): "),

    # ── News & Weather ────────────────────────────────────────────────────────
    ("News briefing",           ["news"],         False, ""),
    ("Weather",                 ["weather"],      False, ""),
    ("Morning daily briefing",  ["daily"],        False, ""),
    ("Set a timer",             ["timer"],        True,  "Duration (e.g. 1h, 10m, 30s): "),

    # ── Archive & Search ──────────────────────────────────────────────────────
    ("Wikipedia lookup",        ["wiki"],         True,  "Topic: "),
    ("Search archive",          ["search"],       True,  "Search: "),
    ("Semantic find",           ["find"],         True,  "Topic: "),
    ("List archive topics",     ["list"],         False, ""),

    # ── System ────────────────────────────────────────────────────────────────
    ("Update current events",   ["update"],       False, ""),
    ("Download general knowledge", ["download-general"], False, ""),
    ("Show help",               ["help"],         False, ""),
]

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
CLEAR_LINE = "\033[2K\r"


def getch():
    """Read a single character without echo."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            return f"\x1b{ch2}{ch3}"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_with_esc(prompt_str):
    """Like input() but returns None if ESC is pressed. Supports backspace."""
    import select
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Check for arrow keys or other escape sequences
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)  # drain the sequence, ignore it
                    continue
                # Plain ESC — go back to menu
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):  # backspace
                if buf:
                    buf.pop()
                    sys.stdout.write("\x08 \x08")
                    sys.stdout.flush()
            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def draw_menu(items, selected):
    os.system("clear")
    HR = "━" * 76
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Command Menu{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()

    split = (len(items) + 1) // 2   # always balanced — left gets the extra if odd
    COL_W = 40                       # visible character width of the left column

    for row in range(split):
        # ── left column ──────────────────────────────────────────────────────
        num = f"{row + 1:>2}."
        label = items[row][0]
        if row == selected:
            plain   = f"  {num} ▶  {label}"
            colored = f"  {BOLD}{GREEN}{num} ▶  {label}{RESET}"
        else:
            plain   = f"  {num}    {label}"
            colored = f"  {DIM}{num}    {label}{RESET}"
        left_cell = colored + " " * max(0, COL_W - len(plain))

        # ── right column (items split+row, aligned beside rows 0..N) ─────────
        j = split + row
        if j < len(items):
            rnum = f"{j + 1:>2}."
            rlabel = items[j][0]
            if j == selected:
                right_cell = f"  {BOLD}{GREEN}{rnum} ▶  {rlabel}{RESET}"
            else:
                right_cell = f"  {DIM}{rnum}    {rlabel}{RESET}"
            print(f"{left_cell}{right_cell}")
        else:
            print(left_cell)

    print()
    print(f"  {DIM}↑↓ or 1-{len(items)} to select  |  Enter to run  |  Q to quit{RESET}")
    print()


# Commands that loop — keep asking questions instead of returning to menu
ASK_LOOP_CMDS = {"ask", "brief", "detailed", "cite", "web"}


def run_command(label, cmd_args, needs_input, prompt):
    loop = cmd_args[0] in ASK_LOOP_CMDS and needs_input
    first = True

    while True:
        os.system("clear")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}  {label}{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print()

        if needs_input:
            ask_prompt = prompt if first else "Enter next question here or ESC for menu: "
            first = False
            try:
                user_input = input_with_esc(f"  {YELLOW}{ask_prompt}{RESET}")
            except KeyboardInterrupt:
                return
            if user_input is None:   # ESC pressed
                return
            user_input = user_input.strip()
            if not user_input:
                continue  # empty Enter — re-show prompt
            full_cmd = [JARVIS] + cmd_args + [user_input]
        else:
            full_cmd = [JARVIS] + cmd_args

        print()
        try:
            subprocess.run(full_cmd)
        except KeyboardInterrupt:
            pass

        # ── after response ────────────────────────────────────────────────────
        print()
        print(f"  {DIM}{'─' * 40}{RESET}")

        if loop:
            # loop back to top — next iteration shows "Enter next question here or ESC for menu:"
            continue
        else:
            input(f"  {DIM}Press Enter to return to menu...{RESET}")
            return


def main():
    selected = 0
    num_buf = ""

    while True:
        draw_menu(MENU, selected)

        key = getch()

        if key in ("q", "Q", "\x03"):  # Q or Ctrl+C
            os.system("clear")
            sys.exit(0)

        elif key == "\x1b[A":  # up arrow — move up within current column
            split = (len(MENU) + 1) // 2
            if selected < split:
                selected = (selected - 1) % split
            else:
                right_size = len(MENU) - split
                selected = split + (selected - split - 1) % right_size
            num_buf = ""

        elif key == "\x1b[B":  # down arrow — move down within current column
            split = (len(MENU) + 1) // 2
            if selected < split:
                selected = (selected + 1) % split
            else:
                right_size = len(MENU) - split
                selected = split + (selected - split + 1) % right_size
            num_buf = ""

        elif key == "\x1b[C":  # right arrow — jump to right column, same row
            split = (len(MENU) + 1) // 2
            if selected < split:
                j = split + selected
                if j < len(MENU):
                    selected = j
            num_buf = ""

        elif key == "\x1b[D":  # left arrow — jump to left column, same row
            split = (len(MENU) + 1) // 2
            if selected >= split:
                selected = selected - split
            num_buf = ""

        elif key == "\r" or key == "\n":  # Enter
            label, cmd_args, needs_input, prompt = MENU[selected]
            run_command(label, cmd_args, needs_input, prompt)
            num_buf = ""

        elif key.isdigit():
            num_buf += key
            n = int(num_buf)
            if 1 <= n <= len(MENU):
                selected = n - 1
                # If two digits possible, wait; if already max range, run immediately
                if n * 10 > len(MENU):
                    label, cmd_args, needs_input, prompt = MENU[selected]
                    run_command(label, cmd_args, needs_input, prompt)
                    num_buf = ""
            else:
                num_buf = ""


if __name__ == "__main__":
    main()
