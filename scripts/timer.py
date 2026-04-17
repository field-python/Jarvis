#!/usr/bin/env python3
"""timer.py — countdown timer with spoken alerts via Jarvis TTS. Supports 2 simultaneous timers."""
import sys
import os
import re
import subprocess
import time
import threading
import tty
import termios
import select as _select
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
tts_script = base_dir / "scripts" / "tts.sh"

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

_print_lock = threading.Lock()


def tts(text):
    if tts_script.exists():
        subprocess.Popen(
            ["bash", str(tts_script), text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def parse_seconds(raw):
    raw = raw.lower().replace(" ", "")
    for old, new in [
        ("minutes", "m"), ("minute", "m"), ("seconds", "s"), ("second", "s"),
        ("hours", "h"),   ("hour", "h"),   ("mins", "m"),    ("min", "m"),
        ("secs", "s"),    ("sec", "s"),    ("hrs", "h"),     ("hr", "h"),
    ]:
        raw = raw.replace(old, new)

    total = 0
    h = re.search(r'(\d+)h', raw)
    m = re.search(r'(\d+)m', raw)
    s = re.search(r'(\d+)s', raw)
    p = re.fullmatch(r'(\d+)', raw)

    if h: total += int(h.group(1)) * 3600
    if m: total += int(m.group(1)) * 60
    if s: total += int(s.group(1))
    if p: total += int(p.group(1)) * 60
    return total


def format_duration(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s   = divmod(rem, 60)
    parts  = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts) or "0s"


def spoken_label(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s   = divmod(rem, 60)
    parts  = []
    if h: parts.append(f"{h} hour{'s' if h > 1 else ''}")
    if m: parts.append(f"{m} minute{'s' if m > 1 else ''}")
    if s: parts.append(f"{s} second{'s' if s > 1 else ''}")
    return ", ".join(parts)


# Shared state for active timers
_timers = {}       # id -> {"label": str, "remaining": int, "done": bool, "cancelled": bool}
_timer_id = 0
_stop_all = threading.Event()


def run_timer_thread(tid, total_seconds, label):
    """Runs a single timer in a background thread."""
    _timers[tid]["remaining"] = total_seconds
    tts(f"Timer {label} started. {spoken_label(total_seconds)} on the clock.")

    remaining = total_seconds
    while remaining > 0 and not _stop_all.is_set() and not _timers[tid].get("cancelled"):
        _timers[tid]["remaining"] = remaining

        if remaining == 300: tts(f"Timer {label}: five minutes remaining.")
        elif remaining == 60: tts(f"Timer {label}: one minute remaining.")
        elif remaining == 30: tts(f"Timer {label}: thirty seconds.")
        elif remaining == 10: tts(f"Timer {label}: ten seconds.")

        time.sleep(1)
        remaining -= 1

    if not _timers[tid].get("cancelled"):
        _timers[tid]["remaining"] = 0
        _timers[tid]["done"] = True
        tts(f"Timer {label} done. Time's up.")

    with _print_lock:
        pass  # redraw will pick it up next tick


def input_with_esc(prompt_str):
    """Like input() but returns None on ESC."""
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = _select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
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
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def status_line():
    """Build a compact status line for all active timers."""
    parts = []
    for tid, info in _timers.items():
        label = info["label"]
        if info.get("done"):
            parts.append(f"{GREEN}✓ {label} DONE{RESET}")
        elif info.get("cancelled"):
            parts.append(f"{RED}✗ {label} cancelled{RESET}")
        else:
            parts.append(f"{CYAN}⏱ {label}: {format_duration(info['remaining'])}{RESET}")
    return "  " + "   |   ".join(parts) if parts else ""


def main():
    global _timer_id

    if len(sys.argv) < 2:
        print("Usage: Jarvis timer <duration>  [e.g. 1h, 10m, 30s]")
        sys.exit(1)

    inp           = " ".join(sys.argv[1:])
    total_seconds = parse_seconds(inp)

    if total_seconds <= 0:
        print(f"  Couldn't parse duration: {inp}")
        print("  Try: 1h, 10m, 30s, 1h30m")
        sys.exit(1)

    print()
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"  {BOLD}Jarvis Timer{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print()

    try:
        while True:
            # Start timer
            _timer_id += 1
            tid   = _timer_id
            label = f"#{tid}"
            _timers[tid] = {"label": label, "remaining": total_seconds, "done": False, "cancelled": False}

            t = threading.Thread(target=run_timer_thread, args=(tid, total_seconds, label), daemon=True)
            t.start()

            print(f"  {GREEN}Timer {label} started: {format_duration(total_seconds)}{RESET}")
            print()

            # Show live status and optionally accept a second timer
            if len(_timers) < 2:
                print(f"  {DIM}Add a second timer, or press Enter / ESC when done:{RESET}")
                ans = input_with_esc(f"  {YELLOW}Second timer (e.g. 5m) or Enter to wait: {RESET}")
                if ans and ans.strip():
                    secs2 = parse_seconds(ans.strip())
                    if secs2 > 0:
                        total_seconds = secs2
                        continue   # loop back to start second timer
            break

        # Live display — show countdown for all running timers
        print()
        try:
            while any(not info.get("done") and not info.get("cancelled") for info in _timers.values()):
                with _print_lock:
                    line = status_line()
                    sys.stdout.write(f"\r{line}   ")
                    sys.stdout.flush()
                time.sleep(0.5)
        except KeyboardInterrupt:
            _stop_all.set()
            for info in _timers.values():
                info["cancelled"] = True
            print(f"\n\n  {RED}Timer(s) cancelled.{RESET}")
            return

        # Final summary
        print(f"\r{status_line()}   ")
        print()
        all_done = all(info.get("done") for info in _timers.values())
        if all_done:
            print(f"  {GREEN}{BOLD}All timers complete!{RESET}")
        print()

    except KeyboardInterrupt:
        _stop_all.set()
        print(f"\n\n  {RED}Cancelled.{RESET}")


if __name__ == "__main__":
    main()
