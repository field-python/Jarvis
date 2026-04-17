#!/usr/bin/env python3
"""weather.py — fetch weather from wttr.in and have Jarvis interpret it"""
import sys
import os
import re
import subprocess
import tempfile
import tty
import termios
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN  = "\033[96m"
YELLOW = "\033[93m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"

default_location = "Anchorage, Alaska"
location_conf = base_dir / "config" / "location.conf"
if location_conf.exists():
    lines = location_conf.read_text(encoding="utf-8").strip().splitlines()
    default_location = lines[0] if lines else default_location


def input_with_esc(prompt_str):
    """Like input() but returns None on ESC. Supports backspace."""
    import select
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
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
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


def fetch_wttr(location, fmt):
    loc = urllib.parse.quote(location)
    url = f"https://wttr.in/{loc}?format={urllib.parse.quote(fmt)}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def show_weather(location):
    now          = datetime.now()
    current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"
    current_time = now.strftime("%-I:%M %p")

    print(f"Fetching weather for {location}...")

    weather_raw    = fetch_wttr(location, "4")
    weather_detail = fetch_wttr(location, "%l:+%C,+%t+(feels+%f),+humidity+%h,+wind+%w,+%P")

    if not weather_raw and not weather_detail:
        print("Could not fetch weather. Check your connection.")
        return False

    weather_data = f"{weather_raw}\n{weather_detail}".strip()

    prompt = (
        f"You are Jarvis, an AI assistant. Today is {current_date}.\n\n"
        f"Interpret the following weather data for {location} and give a practical spoken-style briefing.\n"
        f"Mention current conditions, temperature, and any notable factors (wind, humidity, precipitation).\n"
        f"Add one practical tip if relevant (e.g. dress warmly, carry an umbrella).\n"
        f"3-4 plain sentences. No markdown, no bullet points.\n\n"
        f"Weather data:\n{weather_data}"
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-weather-", delete=False
    )
    tmp.write(prompt)
    tmp.close()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Weather  |  {location}  |  {current_time}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    subprocess.run([sys.executable, generate_script, model, host, tmp.name])
    print()
    os.unlink(tmp.name)
    return True


def main():
    # First location from command line or saved default
    if len(sys.argv) >= 2:
        location = " ".join(sys.argv[1:])
    else:
        location = default_location

    while True:
        show_weather(location)

        print(f"  {DIM}{'─' * 40}{RESET}")
        try:
            ans = input_with_esc(
                f"  {YELLOW}Check another city? (ESC to exit): {RESET}"
            )
        except KeyboardInterrupt:
            break
        if ans is None:
            break
        ans = ans.strip()
        if not ans:
            break
        location = ans


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
