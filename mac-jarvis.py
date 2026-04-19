#!/usr/bin/env python3
"""
mac-jarvis.py — Jarvis launcher for Mac (Groq-powered, no Ollama needed)
"""
import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

BASE  = Path(__file__).parent.resolve()
SCRIPTS = BASE / "scripts"
CONFIG  = BASE / "config"
NOTES   = BASE / "notes"

VENV_ROOT = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-mac-venv"))
PYTHON    = str(Path(VENV_ROOT) / "bin" / "python")

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_CONF  = CONFIG / "groq.conf"

BOLD  = "\033[1m"
CYAN  = "\033[96m"
YL    = "\033[93m"
GR    = "\033[92m"
RD    = "\033[91m"
DIM   = "\033[2m"
R     = "\033[0m"
HR    = "━" * 52


def _py():
    """Return Python binary — venv if it exists, else system python3."""
    if Path(PYTHON).exists():
        return PYTHON
    return sys.executable


def _env(extra=None):
    e = dict(os.environ)
    e["JARVIS_BACKEND"] = "groq"
    e["JARVIS_MODEL"]   = GROQ_MODEL
    e["JARVIS_VENV"]    = VENV_ROOT
    if extra:
        e.update(extra)
    return e


def run_py(script, *args, extra_env=None):
    result = subprocess.run(
        [_py(), str(SCRIPTS / script)] + [str(a) for a in args],
        env=_env(extra_env)
    )
    sys.exit(result.returncode)


def check_key():
    if GROQ_CONF.exists() and GROQ_CONF.read_text(encoding="utf-8").strip():
        return True
    print(f"\n{RD}  No Groq API key found.{R}")
    print(f"  Get a free key at: {BOLD}console.groq.com{R}")
    print(f"  Then run:  {CYAN}Jarvis groq-key YOUR_KEY_HERE{R}\n")
    return False


def do_groq_key(args):
    if not args:
        if GROQ_CONF.exists() and GROQ_CONF.read_text().strip():
            print(f"  {GR}Groq key is set.{R}  To change it: Jarvis groq-key NEW_KEY")
        else:
            print(f"  No key set. Usage:  Jarvis groq-key YOUR_KEY_HERE")
        return
    key = args[0].strip()
    CONFIG.mkdir(parents=True, exist_ok=True)
    GROQ_CONF.write_text(key + "\n", encoding="utf-8")
    print(f"  {GR}✓ Groq key saved.{R}  Try: Jarvis \"hello\"")


def do_help():
    print(f"""
{BOLD}{CYAN}{HR}
  ✦  Jarvis  |  Your AI Assistant  ✦
{HR}{R}

  {BOLD}ASK{R}
  Jarvis "question"              Ask anything
  Jarvis brief "question"        Short direct answer
  Jarvis detailed "question"     In-depth answer

  {BOLD}CONVERSATION{R}
  Jarvis chat                    Start a conversation
  Jarvis web "question"          Search the web + answer

  {BOLD}DAILY{R}
  Jarvis news                    Today's headlines
  Jarvis weather                 Current weather (your location)
  Jarvis weather "London"        Weather for any city
  Jarvis daily                   Morning briefing (news + weather)
  Jarvis timer 10m               Countdown timer  (e.g. 1h, 10m, 30s)

  {BOLD}NOTES{R}
  Jarvis note "text"             Save a quick note
  Jarvis notes                   View today's notes

  {BOLD}SETUP{R}
  Jarvis groq-key YOUR_KEY       Set your Groq API key
  Jarvis set-location "City, ST" Set your home location

{BOLD}{CYAN}{HR}{R}
  Free API key:  {BOLD}console.groq.com{R}
{BOLD}{CYAN}{HR}{R}
""")


def do_set_location(args):
    if not args:
        conf = CONFIG / "location.conf"
        current = conf.read_text().strip() if conf.exists() else "Not set"
        print(f"  Location: {current}")
        print(f'  Usage: Jarvis set-location "City, State"')
        return
    loc = " ".join(args)
    CONFIG.mkdir(parents=True, exist_ok=True)
    (CONFIG / "location.conf").write_text(loc + "\n", encoding="utf-8")
    print(f"  {GR}Location set to: {loc}{R}")


def do_notes(args):
    notes_dir = NOTES / "personal-notes"
    if not notes_dir.exists() or not any(notes_dir.iterdir()):
        print('  No notes yet. Try: Jarvis note "something to remember"')
        return
    today = datetime.now().strftime("%Y-%m-%d")
    if args and re.match(r'^\d{4}-\d{2}-\d{2}$', args[0]):
        today = args[0]
    f = notes_dir / f"{today}.md"
    if not f.exists():
        print(f"  No notes for {today}.")
        return
    print(f"\n  {BOLD}Notes — {today}{R}\n")
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            line = re.sub(r'\*\*(\d{2}:\d{2})\*\*', r'  [\1]', line)
            print(f"  {line}")
    print()


# ── main ──────────────────────────────────────────────────────────────────────
args = sys.argv[1:]

if not args or args[0] in ("-h", "--help", "help"):
    do_help()
    sys.exit(0)

cmd  = args[0].lower()
rest = args[1:]

# Key management (no Groq check needed)
if cmd == "groq-key":
    do_groq_key(rest)
    sys.exit(0)

if cmd == "set-location":
    do_set_location(rest)
    sys.exit(0)

if cmd == "notes":
    do_notes(rest)
    sys.exit(0)

# Everything below needs a valid key
if not check_key():
    sys.exit(1)

if cmd in ("note",):
    run_py("note.py", *rest)

elif cmd in ("timer",):
    run_py("timer.py", *rest)

elif cmd in ("news",):
    run_py("news.py", *rest)

elif cmd in ("weather",):
    run_py("weather.py", *rest)

elif cmd in ("daily",):
    run_py("daily.py", *rest)

elif cmd in ("chat", "hello"):
    run_py("chat.py")

elif cmd in ("web",):
    if not rest:
        print('  Usage: Jarvis web "your question"')
        sys.exit(1)
    run_py("ask.py", " ".join(rest), extra_env={"JARVIS_MODE": "normal"})

elif cmd in ("brief",):
    if not rest:
        print('  Usage: Jarvis brief "your question"')
        sys.exit(1)
    run_py("ask.py", " ".join(rest), extra_env={"JARVIS_MODE": "brief"})

elif cmd in ("detailed",):
    if not rest:
        print('  Usage: Jarvis detailed "your question"')
        sys.exit(1)
    run_py("ask.py", " ".join(rest), extra_env={"JARVIS_MODE": "detailed"})

else:
    # Default: treat the whole input as a question
    question = " ".join(args)
    run_py("ask.py", question, extra_env={"JARVIS_MODE": "normal"})
