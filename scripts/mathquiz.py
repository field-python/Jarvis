#!/usr/bin/env python3
"""mathquiz.py — Timed arithmetic challenge"""
import sys
import os
import re
import random
import tty
import termios
import select
import time

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
HR     = "━" * 50

Q_COUNT = 10

# (label, description, a_range, b_range, operations)
DIFFICULTIES = [
    ("Easy",   "Single-digit  +  −",            (1, 9),   (1, 9),   ["+", "-"]),
    ("Medium", "Two-digit  +  −  ×",             (5, 25),  (2, 12),  ["+", "-", "×"]),
    ("Hard",   "Multi-digit  +  −  ×  ÷",        (8, 99),  (2, 12),  ["+", "-", "×", "÷"]),
]


def getch():
    import os as _os
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", "replace")
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_answer(prompt_str):
    """Accept digits and minus sign only. Returns string or None on ESC."""
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf.pop()
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = total // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
                    sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ch == "-" and not buf:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
            elif ch.isdigit():
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def make_question(a_range, b_range, ops):
    op = random.choice(ops)
    if op == "÷":
        # Only exact divisions
        b = random.randint(2, b_range[1])
        a = b * random.randint(2, max(2, a_range[1] // b))
        return a, b, op, a // b
    a = random.randint(*a_range)
    b = random.randint(*b_range)
    if op == "-":
        a, b = max(a, b), min(a, b)   # never negative
    ans = {"+" : a + b, "-" : a - b, "×" : a * b}[op]
    return a, b, op, ans


def diff_menu():
    selected = 0
    while True:
        os.system("clear")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print(f"{BOLD}{CYAN}  Jarvis  |  Math Quiz{RESET}")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print()
        print(f"  Difficulty  ({Q_COUNT} questions each):")
        print()
        for i, (label, desc, *_) in enumerate(DIFFICULTIES):
            if i == selected:
                print(f"  {BOLD}{GREEN}▶  {label:<8}{RESET}  {desc}")
            else:
                print(f"     {DIM}{label:<8}  {desc}{RESET}")
        print()
        print(f"  {DIM}↑↓ to choose  |  Enter to start  |  Q to quit{RESET}")

        key = getch()
        if key in ("q", "Q", "\x1b", "\x03"):
            return None
        elif key in ("\x1b[A", "\x1bOA"):
            selected = (selected - 1) % len(DIFFICULTIES)
        elif key in ("\x1b[B", "\x1bOB"):
            selected = (selected + 1) % len(DIFFICULTIES)
        elif key in ("\r", "\n"):
            return selected


def play(diff_idx):
    label, _, a_range, b_range, ops = DIFFICULTIES[diff_idx]
    correct = 0
    total_asked = 0
    times = []

    for q_num in range(1, Q_COUNT + 1):
        a, b, op, answer = make_question(a_range, b_range, ops)
        question = f"{a} {op} {b} = ?"

        os.system("clear")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        score_str = f"{correct}/{q_num - 1}" if q_num > 1 else ""
        pct_str   = f"  ({round(correct / (q_num-1) * 100)}%)" if q_num > 1 else ""
        print(f"{BOLD}{CYAN}  Math Quiz  |  {label}  |  {q_num}/{Q_COUNT}"
              f"  {DIM}{score_str}{pct_str}{RESET}")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print()
        box_inner = f"    {question}    "
        box_width = len(box_inner)
        print(f"  ┌{'─' * box_width}┐")
        print(f"  │{BOLD}{YELLOW}{box_inner}{RESET}│")
        print(f"  └{'─' * box_width}┘")
        print()

        t_start = time.monotonic()
        raw = input_answer(f"  {CYAN}Answer: {RESET}")
        elapsed = time.monotonic() - t_start

        if raw is None:   # ESC
            return correct, total_asked, times

        total_asked += 1

        try:
            given = int(raw.strip())
        except ValueError:
            print(f"  {DIM}(skipped){RESET}")
            time.sleep(0.6)
            continue

        times.append(elapsed)

        if given == answer:
            correct += 1
            print(f"  {GREEN}{BOLD}✓  Correct!{RESET}  {DIM}{elapsed:.1f}s{RESET}")
        else:
            print(f"  {RED}✗  Wrong.{RESET}  {DIM}Answer was {BOLD}{answer}{RESET}")

        time.sleep(0.85)

    return correct, total_asked, times


def main():
    while True:
        diff_idx = diff_menu()
        if diff_idx is None:
            break

        correct, total, times = play(diff_idx)
        label = DIFFICULTIES[diff_idx][0]

        os.system("clear")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print(f"{BOLD}  Math Quiz  |  {label}  |  Results{RESET}")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print()
        print(f"  Score:      {correct} / {total}")
        if total:
            pct   = round(correct / total * 100)
            color = GREEN if pct >= 80 else (YELLOW if pct >= 60 else RED)
            bar_filled = round(pct / 5)
            bar   = f"{color}{'█' * bar_filled}{DIM}{'░' * (20 - bar_filled)}{RESET}"
            print(f"  Result:     {bar}  {color}{BOLD}{pct}%{RESET}")
        if times:
            avg = sum(times) / len(times)
            best_t = min(times)
            print(f"  Avg time:   {avg:.1f}s per question")
            print(f"  Fastest:    {best_t:.1f}s")
        print()

        print(f"  {DIM}[Enter] Play again  |  [Q] Quit{RESET}", end="", flush=True)
        key = getch().lower()
        if key in ("q", "\x1b", "\x03"):
            break

    os.system("clear")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
