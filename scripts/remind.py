#!/usr/bin/env python3
"""remind.py — add, list, and delete reminders"""
import sys, json, re
from pathlib import Path
from datetime import datetime, timedelta

base_dir     = Path(__file__).parent.parent.resolve()
remind_file  = base_dir / "config" / "reminders.json"

YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
RESET  = "\033[0m"


def load():
    if remind_file.exists():
        try:
            return json.loads(remind_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save(reminders):
    remind_file.parent.mkdir(parents=True, exist_ok=True)
    remind_file.write_text(json.dumps(reminders, indent=2), encoding="utf-8")


def parse_time(text):
    """Parse time expressions like '3pm', '3:30pm', 'in 10 minutes', 'in 2 hours'.
    Returns ISO datetime string or None."""
    now  = datetime.now()
    text = text.strip().lower()

    # "in X minutes/hours"
    m = re.match(r'in\s+(\d+)\s*(min\w*|hour\w*|hr\w*)', text)
    if m:
        n    = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("h"):
            dt = now + timedelta(hours=n)
        else:
            dt = now + timedelta(minutes=n)
        return dt.strftime("%Y-%m-%dT%H:%M")

    # "at 3pm", "at 3:30pm", "at 15:30"
    m = re.search(r'(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if m:
        hour   = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm   = m.group(3)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt.strftime("%Y-%m-%dT%H:%M")

    return None


def show_all(reminders):
    print()
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Reminders{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    if not reminders:
        print(f"\n  {DIM}No reminders set.{RESET}\n")
        print(f"  Try: Jarvis remind me at 3pm to call the dentist")
        print()
        return
    print()
    now = datetime.now()
    for i, r in enumerate(reminders, 1):
        dt       = datetime.fromisoformat(r["time"])
        msg      = r["message"]
        diff     = dt - now
        minutes  = int(diff.total_seconds() / 60)
        if minutes < 0:
            when = f"{RED}overdue{RESET}"
        elif minutes < 60:
            when = f"{GREEN}in {minutes}m{RESET}"
        elif minutes < 1440:
            hours = minutes // 60
            when  = f"{GREEN}in {hours}h {minutes%60}m{RESET}"
        else:
            when = f"{DIM}{dt.strftime('%b %d %I:%M %p')}{RESET}"
        time_str = dt.strftime("%I:%M %p").lstrip("0")
        print(f"  {BOLD}{i:>2}.{RESET} {time_str}  —  {msg}  {DIM}({when}){RESET}")
    print()
    print(f"  {DIM}Jarvis remind delete 1  — remove reminder #1{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")


arg  = sys.argv[1].lower() if len(sys.argv) > 1 else ""
rest = " ".join(sys.argv[2:])

reminders = load()

# ── Jarvis remind                         → show all
# ── Jarvis remind me at 3pm to "msg"      → add
# ── Jarvis remind in 10 minutes to "msg"  → add
# ── Jarvis remind delete 1                → delete #1
# ── Jarvis remind clear                   → delete all fired

if not arg or arg in ("list", "show"):
    show_all(reminders)

elif arg in ("delete", "remove", "rm", "del"):
    try:
        n = int(rest.strip()) - 1
        if 0 <= n < len(reminders):
            removed = reminders.pop(n)
            save(reminders)
            print(f"  {RED}Removed:{RESET} {removed['message']}")
        else:
            print(f"  No reminder #{n+1}")
    except ValueError:
        print("  Usage: Jarvis remind delete 1")

elif arg == "clear":
    now     = datetime.now()
    before  = len(reminders)
    reminders = [r for r in reminders if datetime.fromisoformat(r["time"]) > now]
    save(reminders)
    print(f"  Cleared {before - len(reminders)} past reminder(s).")

else:
    # Try to parse as "remind me at X to Y" or "remind in X to Y"
    full = " ".join(sys.argv[1:])
    # Extract message after "to"
    m = re.search(r'\bto\b\s+(.+)$', full, re.IGNORECASE)
    if not m:
        print(f"  {RED}Couldn't parse reminder.{RESET}")
        print("  Try: Jarvis remind me at 3pm to call the dentist")
        print("  Try: Jarvis remind in 30 minutes to take medication")
        sys.exit(1)

    message   = m.group(1).strip()
    time_part = full[:m.start()].strip()
    # Remove "me" "remind" etc from time part
    time_part = re.sub(r'\b(remind|me|please)\b', '', time_part, flags=re.IGNORECASE).strip()

    dt_str = parse_time(time_part)
    if not dt_str:
        print(f"  {RED}Couldn't understand the time: '{time_part}'{RESET}")
        print("  Examples: 'at 3pm', 'at 3:30pm', 'in 10 minutes', 'in 2 hours'")
        sys.exit(1)

    dt = datetime.fromisoformat(dt_str)
    reminders.append({"time": dt_str, "message": message})
    reminders.sort(key=lambda r: r["time"])
    save(reminders)

    time_str = dt.strftime("%I:%M %p").lstrip("0")
    diff     = dt - datetime.now()
    minutes  = int(diff.total_seconds() / 60)
    if minutes < 60:
        eta = f"in {minutes} minutes"
    else:
        eta = f"in {minutes//60}h {minutes%60}m"

    print()
    print(f"  {GREEN}✓ Reminder set:{RESET} {message}")
    print(f"  {DIM}At {time_str} ({eta}){RESET}")
    print()
    print(f"  {DIM}Make sure the reminder daemon is running: Jarvis remind-start{RESET}")
    print()
