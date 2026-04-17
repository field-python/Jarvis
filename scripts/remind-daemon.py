#!/usr/bin/env python3
"""remind-daemon.py — background process that fires reminders via TTS"""
import sys, json, os, time, subprocess
from pathlib import Path
from datetime import datetime

base_dir    = Path(__file__).parent.parent.resolve()
remind_file = base_dir / "config" / "reminders.json"
tts_script  = base_dir / "scripts" / "tts.sh"
pid_file    = base_dir / "config" / "remind-daemon.pid"


def load():
    if remind_file.exists():
        try:
            return json.loads(remind_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save(reminders):
    remind_file.write_text(json.dumps(reminders, indent=2), encoding="utf-8")


def speak(text):
    """Speak via TTS if available, otherwise print."""
    if tts_script.exists():
        subprocess.run(["bash", str(tts_script), text],
                       stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        print(f"\n  🔔 REMINDER: {text}\n", flush=True)


def already_running():
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)   # check if process is alive
            return True
        except (ProcessLookupError, ValueError, PermissionError):
            pass
    return False


if already_running():
    print("Reminder daemon is already running.")
    sys.exit(0)

# Write PID file
pid_file.write_text(str(os.getpid()))

print(f"Reminder daemon started (PID {os.getpid()}). Checking every 30 seconds.")
print("Ctrl+C or close terminal to stop.")

try:
    while True:
        now       = datetime.now()
        reminders = load()
        fired     = []
        remaining = []

        for r in reminders:
            dt = datetime.fromisoformat(r["time"])
            if dt <= now:
                fired.append(r)
            else:
                remaining.append(r)

        for r in fired:
            msg = r["message"]
            print(f"  🔔 FIRING: {msg}", flush=True)
            speak(f"Reminder: {msg}")

        if fired:
            save(remaining)

        time.sleep(30)

except KeyboardInterrupt:
    print("\nReminder daemon stopped.")
finally:
    pid_file.unlink(missing_ok=True)
