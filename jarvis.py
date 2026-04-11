#!/usr/bin/env python3
"""
jarvis.py — Jarvis canonical launcher (Python, cross-platform)
Works on Linux and macOS. Replaces the bash Jarvis launcher.
"""
import sys
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# ── paths ─────────────────────────────────────────────────────────────────────
JARVIS_BASE = Path(__file__).parent.resolve()
SCRIPTS     = JARVIS_BASE / "scripts"
CONFIG      = JARVIS_BASE / "config"
NOTES_DIR   = JARVIS_BASE / "notes"
MEMORY_DIR  = JARVIS_BASE / "memory"

venv_root = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-venv"))
PYTHON    = str(Path(venv_root) / "bin" / "python")

CLOUD_HOST  = "127.0.0.1:11435"
CLOUD_MODEL = "qwen3:8b"
GROQ_MODEL  = "llama-3.3-70b-versatile"

# ── read config flags ─────────────────────────────────────────────────────────
fast_mode  = (CONFIG / "fast-mode").exists()
groq_mode  = (CONFIG / "groq-mode").exists()
cloud_mode = (CONFIG / "cloud-mode").exists()

if groq_mode:
    os.environ.setdefault("JARVIS_BACKEND", "groq")
    os.environ.setdefault("JARVIS_MODEL",   GROQ_MODEL)
if cloud_mode:
    os.environ.setdefault("OLLAMA_HOST",  CLOUD_HOST)
    os.environ.setdefault("JARVIS_MODEL", CLOUD_MODEL)

model = os.environ.get("JARVIS_MODEL", "Jarvis")
host  = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

# ── colors ────────────────────────────────────────────────────────────────────
CYAN  = "\033[96m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"
HR    = "━" * 56


# ── helpers ───────────────────────────────────────────────────────────────────
def _env(extra=None):
    e = dict(os.environ)
    if extra:
        e.update(extra)
    return e


def run_py(script, *args, extra_env=None):
    """Run a venv Python script and exit with its return code."""
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / script)] + [str(a) for a in args],
        env=_env(extra_env)
    )
    sys.exit(result.returncode)


def read_conf(name, default=""):
    f = CONFIG / name
    if f.exists():
        lines = [l for l in f.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        return lines[0].strip() if lines else default
    return default


def groq_key_saved():
    f = CONFIG / "groq.conf"
    return f.exists() and bool(f.read_text(encoding="utf-8").strip())


def cloud_up():
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 11435), timeout=2)
        s.close()
        return True
    except OSError:
        return False


# ── startup checks ────────────────────────────────────────────────────────────
def ensure_jarvis_model():
    """Rebuild Jarvis model if missing. Skips if ollama not installed (Groq-only setup)."""
    if not shutil.which("ollama"):
        return
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "Jarvis" not in (result.stdout or ""):
        print("Jarvis model not found — rebuilding from Modelfile...")
        subprocess.run(["ollama", "create", "Jarvis", "-f",
                        str(JARVIS_BASE / "Jarvis.Modelfile")])
        print("Done. Continuing...")


def check_onboarding(argv):
    if not (CONFIG / "onboarding-done").exists():
        if not (CONFIG / "location.conf").exists():
            r = subprocess.run(
                [PYTHON, str(SCRIPTS / "onboarding.py"), str(JARVIS_BASE)] + argv
            )
            sys.exit(r.returncode)
        else:
            (CONFIG / "onboarding-done").touch()


# ── inline handlers ───────────────────────────────────────────────────────────
def do_help():
    fast_lbl  = "ON" if fast_mode  else "OFF"
    cloud_lbl = "ON" if cloud_mode else "OFF"
    groq_lbl  = "ON" if groq_mode  else "OFF"
    loc       = read_conf("location.conf", "Not set")
    print(f"""\
{BOLD}{CYAN}{HR}
  Jarvis  |  Offline AI Assistant
  Location: {loc}  |  Fast: {fast_lbl}  |  Cloud: {cloud_lbl}  |  Groq: {groq_lbl}
{HR}{RESET}

  ASK
  Jarvis "question"              Ask anything — full answer with archive
  Jarvis brief "question"        Short answer, no archive (one-off fast query)
  Jarvis detailed "question"     In-depth answer with steps and context
  Jarvis cite "question"         Answer with archive sources listed
  Jarvis groq "question"         Ask via Groq cloud ({GROQ_MODEL})
  Jarvis cloud "question"        Ask via cloud RTX 4090 (needs SSH tunnel)
  Jarvis code "task"             Generate code — beginner-friendly
  Jarvis learn "topic"           Step-by-step interactive coding lesson
  Jarvis language                Language hub — learn, translate, phrases (10 languages)
  Jarvis note "text"             Save a quick note
  Jarvis note                    Open editor for a longer note
  Jarvis notes                   View today's notes
  Jarvis notes 2026-04-09        View notes from a specific date

  CONVERSATION
  Jarvis hello / chat            Start a conversation (remembers context)
  Jarvis voice                   Wake-word voice mode (Hey Jarvis)
  Jarvis convo                   Continuous voice mode (no wake word needed)
  Jarvis cloud-voice             Voice mode via cloud RTX 4090

  SEARCH
  Jarvis wiki "topic"            Full Wikipedia lookup — text + browser option
  Jarvis search "keyword"        Keyword search the archive
  Jarvis find "topic"            Semantic search — finds related notes
  Jarvis list                    List all archive topics

  SETTINGS
  Jarvis fast                    Toggle fast mode ON/OFF  (currently: {fast_lbl})
  Jarvis groq-on                 Route ALL commands to Groq cloud (currently: {groq_lbl})
  Jarvis groq-off                Switch back to local model
  Jarvis groq-key YOUR_KEY       Save your Groq API key
  Jarvis cloud-on                Route all commands to cloud RTX 4090
  Jarvis cloud-off               Switch back to local model
  Jarvis set-location "City, ST" Set your home region for location context
  Jarvis remember "fact"         Save a personal fact to Jarvis memory
  Jarvis remember                View all saved memory

  CONTENT & UPDATES
  Jarvis news [category]         Headlines (world/tech/sports/entertainment)
  Jarvis weather [location]      Current weather interpreted by Jarvis
  Jarvis timer 1h                Countdown timer with spoken alerts
  Jarvis daily                   Morning briefing: weather + news spoken aloud
  Jarvis skill [category]        Skill of the day (survival, cooking, etc.)
  Jarvis firstaid "topic"        Offline first aid reference
  Jarvis recipe "search"         Search saved recipes
  Jarvis recipe list / add / suggest
  Jarvis web "question"          Search the web and answer (saves offline)
  Jarvis update                  Fetch current news and refresh pages
  Jarvis fetch "url" "name"      Save a webpage to the archive
  Jarvis download-regions        Download regional content (states/provinces)
  Jarvis download-coding         Download coding references
  Jarvis download-general        Download general knowledge
  Jarvis rebuild-index           Rebuild semantic search index

  CUSTOMIZE
  Jarvis set-voice               Pick a TTS voice (British, US male/female, etc.)
  Jarvis customize               Full customization menu (voice, layout, fonts)

  SETUP
  Jarvis install-voice           One-time setup for voice mode
  Jarvis onboard                 Re-run first-time setup wizard
  Jarvis cache-clear             Clear cached answers

{BOLD}{CYAN}{HR}{RESET}""")


def do_notes(args):
    notes_dir = NOTES_DIR / "personal-notes"
    if not notes_dir.exists() or not any(notes_dir.iterdir()):
        print('No notes yet. Try: Jarvis note "something to remember"')
        return

    def show(f, label):
        print(f"\n{HR}\n  Notes  |  {label}\n{HR}\n")
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                continue
            line = re.sub(r'\*\*(\d{2}:\d{2})\*\*', r'  [\1]', line)
            print(line)
        print(HR)

    if args and re.match(r'^\d{4}-\d{2}-\d{2}$', args[0]):
        t = notes_dir / f"{args[0]}.md"
        show(t, args[0]) if t.exists() else print(f"No notes for {args[0]}.")
        return

    today      = datetime.now().strftime("%Y-%m-%d")
    today_file = notes_dir / f"{today}.md"
    if today_file.exists():
        show(today_file, f"Today — {today}")
        others = sorted([f.stem for f in notes_dir.glob("*.md")
                         if f.stem != today], reverse=True)[:5]
        if others:
            print("\n  Other dates:")
            for d in others:
                print(f"    {d}  →  Jarvis notes {d}")
            print()
    else:
        print(f"\n{HR}\n  Notes  |  No notes for today\n{HR}\n  All dates:")
        for f in sorted(notes_dir.glob("*.md"), reverse=True):
            print(f"    {f.stem}  →  Jarvis notes {f.stem}")
        print(f"\n{HR}")


def do_list():
    print(f"\n{HR}\n  Jarvis  |  Archive Topics\n{HR}\n")
    gen = NOTES_DIR / "generated"
    if gen.exists():
        topics = sorted(d.name for d in gen.iterdir() if d.is_dir())
        half = (len(topics) + 1) // 2
        for i in range(half):
            left  = topics[i] if i < len(topics) else ""
            right = topics[i + half] if (i + half) < len(topics) else ""
            print(f"  {left:<38}{right}")
    print()
    n_notes = len(list(NOTES_DIR.rglob("*.md")))
    pages   = JARVIS_BASE / "pages"
    n_pages = len(list(pages.rglob("*.html"))) if pages.exists() else 0
    print(f"  {n_notes} notes  |  {n_pages} pages\n{HR}")


def do_remember(args):
    mem = MEMORY_DIR / "user-memory.md"
    if not args:
        print(f"\n{HR}\n  Jarvis  |  Memory\n{HR}\n")
        if mem.exists():
            lines = [l for l in mem.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.strip().startswith(("#", "<!--"))]
            print("\n".join(f"  {l}" for l in lines) if lines else "  (empty)")
        else:
            print("  (no memory saved yet)")
        print(f"\n{HR}")
        return
    fact = " ".join(args)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(mem, "a", encoding="utf-8") as f:
        f.write(f"- [{datetime.now().strftime('%Y-%m-%d')}] {fact}\n")
    print(f"Remembered: {fact}")


def do_set_location(args):
    if not args:
        print(f'Usage: Jarvis set-location "City, State"\n'
              f'Current: {read_conf("location.conf", "Not set")}')
        return
    loc = " ".join(args)
    CONFIG.mkdir(parents=True, exist_ok=True)
    (CONFIG / "location.conf").write_text(loc + "\n", encoding="utf-8")
    print(f"Location set to: {loc}")


def do_web(args):
    if not args:
        print('Usage: Jarvis web "topic or question"')
        sys.exit(1)
    query  = " ".join(args)
    now    = datetime.now()
    date_s = f"{now.strftime('%A, %B')} {now.day}, {now.year}"
    loc    = read_conf("location.conf", "North America")

    print("Searching the web...")
    try:
        devtty  = open("/dev/tty", "w")
        stderr_ = devtty
    except OSError:
        devtty  = None
        stderr_ = subprocess.DEVNULL

    result = subprocess.run(
        [PYTHON, str(SCRIPTS / "web-search.py"), query],
        stdout=subprocess.PIPE, stderr=stderr_, text=True
    )
    if devtty:
        devtty.close()

    web_context = result.stdout.strip()
    if not web_context:
        print("Could not reach the web. Falling back to archive...")
        run_py("ask.py", query, extra_env={"JARVIS_MODE": "normal"})
        return

    prompt = (
        f"You are Jarvis, an advanced offline AI assistant.\n"
        f"Today's date: {date_s}\n"
        f"The user's home region is {loc}.\n\n"
        f"Answer the question using the web search results below as your primary source. "
        f"Be direct and accurate. Do not tell the user to visit websites.\n\n"
        f"Question: {query}\n\nWeb search results:\n{web_context}"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     prefix="jarvis-web-", delete=False) as f:
        f.write(prompt)
        tmp = f.name
    subprocess.run([PYTHON, str(SCRIPTS / "generate.py"), model, host, tmp])
    os.unlink(tmp)


def do_wiki(args):
    if not args:
        print('Usage: Jarvis wiki "topic"')
        sys.exit(1)
    query   = " ".join(args)
    wiki_sh = SCRIPTS / "wikipedia-lookup.sh"
    print(f"\n{HR}\n  Jarvis Wiki  |  {query}\n{HR}\n")
    print("  Starting Wikipedia server (first time may take a moment)...")
    r = subprocess.run(["bash", str(wiki_sh), query],
                       capture_output=True, text=True)
    if not r.stdout.strip():
        print(f"  No article found for: {query}\n{HR}")
        return
    print(f"\n{r.stdout}\n{HR}")
    ans = input("  Open full article with photos in browser? (y/n): ").strip().lower()
    if ans.startswith("y"):
        subprocess.Popen(["bash", str(wiki_sh), query],
                         env=_env({"WIKIPEDIA_OPEN": "1"}),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  Opening in browser...")
    print(HR)


def do_groq(args):
    if not groq_key_saved():
        print(f"\n{HR}\n  Jarvis Groq  |  No API Key\n{HR}\n"
              f"  Save your key first:\n    Jarvis groq-key YOUR_API_KEY\n{HR}")
        sys.exit(1)
    print(f"  [Groq — {GROQ_MODEL}]")
    env = {"JARVIS_BACKEND": "groq", "JARVIS_MODEL": GROQ_MODEL}
    sub = args[0].lower() if args else ""
    if sub in ("brief", "detailed", "cite"):
        run_py("ask.py", *args[1:], extra_env={**env, "JARVIS_MODE": sub})
    else:
        run_py("ask.py", *args, extra_env=env)


def do_cloud(args):
    if not cloud_up():
        print(f"\n{HR}\n  Jarvis Cloud  |  Not Connected\n{HR}\n"
              f"  Start the SSH tunnel first (in a separate terminal):\n\n"
              f"    ssh -p 37001 root@85.218.235.6 \\\n"
              f"        -L 11435:localhost:11434 \\\n"
              f"        -i ~/.ssh/jarvis_vast\n\n{HR}")
        sys.exit(1)
    print(f"  [Cloud RTX 4090 — {CLOUD_MODEL}]")
    env = {"JARVIS_MODEL": CLOUD_MODEL, "OLLAMA_HOST": CLOUD_HOST}
    sub = args[0].lower() if args else ""
    if sub in ("brief", "detailed", "cite"):
        run_py("ask.py", *args[1:], extra_env={**env, "JARVIS_MODE": sub})
    else:
        run_py("ask.py", *args, extra_env=env)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ensure_jarvis_model()
    check_onboarding(sys.argv[1:])

    args = sys.argv[1:]
    cmd  = args[0].lower() if args else ""
    rest = args[1:]

    # ── help ──────────────────────────────────────────────────────────────────
    if cmd in ("help", "--help", "-h", ""):
        do_help()

    # ── groq ──────────────────────────────────────────────────────────────────
    elif cmd == "groq":
        do_groq(rest)
    elif cmd == "groq-on":
        if not groq_key_saved():
            print("  No Groq API key saved. Add it first:\n    Jarvis groq-key YOUR_API_KEY")
            sys.exit(1)
        (CONFIG / "groq-mode").touch()
        print(f"Groq mode ON — all commands now use {GROQ_MODEL} via Groq.\n"
              f"Run 'Jarvis groq-off' to switch back.")
    elif cmd == "groq-off":
        (CONFIG / "groq-mode").unlink(missing_ok=True)
        print("Groq mode OFF — back to local model.")
    elif cmd == "groq-key":
        if not rest:
            print("Usage: Jarvis groq-key YOUR_API_KEY")
            if (CONFIG / "groq.conf").exists():
                print("Key is currently saved.")
            return
        CONFIG.mkdir(parents=True, exist_ok=True)
        kf = CONFIG / "groq.conf"
        kf.write_text(rest[0] + "\n", encoding="utf-8")
        kf.chmod(0o600)
        print("Groq API key saved.\n"
              "Use 'Jarvis groq \"question\"' for one-off queries.\n"
              "Use 'Jarvis groq-on' to make Groq the default for all commands.")

    # ── cloud ─────────────────────────────────────────────────────────────────
    elif cmd == "cloud":
        do_cloud(rest)
    elif cmd == "cloud-on":
        if not cloud_up():
            print("  Cloud GPU not reachable. Start the SSH tunnel first.")
            sys.exit(1)
        (CONFIG / "cloud-mode").touch()
        print("Cloud mode ON — all commands use the RTX 4090.\n"
              "Run 'Jarvis cloud-off' to switch back.")
    elif cmd == "cloud-off":
        (CONFIG / "cloud-mode").unlink(missing_ok=True)
        print("Cloud mode OFF — back to local model.")
    elif cmd == "cloud-voice":
        if not cloud_up():
            print(f"\n{HR}\n  Jarvis Cloud Voice  |  Not Connected\n{HR}\n"
                  f"  Start the SSH tunnel first:\n\n"
                  f"    ssh -p 37001 root@85.218.235.6 \\\n"
                  f"        -L 11435:localhost:11434 \\\n"
                  f"        -i ~/.ssh/jarvis_vast\n\n{HR}")
            sys.exit(1)
        print(f"  [Cloud Voice — RTX 4090 — {CLOUD_MODEL}]")
        run_py("voice.py", extra_env={"JARVIS_MODEL": CLOUD_MODEL, "OLLAMA_HOST": CLOUD_HOST})

    # ── fast mode ─────────────────────────────────────────────────────────────
    elif cmd == "fast":
        flag = CONFIG / "fast-mode"
        if flag.exists():
            flag.unlink()
            print("Fast mode OFF — Jarvis back to full mode.")
        else:
            flag.touch()
            print("Fast mode ON. Run 'Jarvis fast' again to turn off.")

    # ── scripts ───────────────────────────────────────────────────────────────
    elif cmd in ("language", "lang"):
        run_py("language.py")
    elif cmd == "code":
        run_py("code.py", *rest)
    elif cmd == "learn":
        run_py("learn.py", *rest)
    elif cmd == "menu":
        run_py("menu.py", extra_env={"JARVIS_LAUNCHER": sys.argv[0]})
    elif cmd == "note":
        run_py("note.py", *rest)
    elif cmd == "notes":
        do_notes(rest)
    elif cmd == "news":
        run_py("news.py", *rest)
    elif cmd == "weather":
        run_py("weather.py", *rest)
    elif cmd == "timer":
        run_py("timer.py", *rest)
    elif cmd == "daily":
        run_py("daily.py")
    elif cmd == "skill":
        run_py("skill.py", *rest)
    elif cmd in ("firstaid", "first-aid", "fa"):
        run_py("firstaid.py", *rest)
    elif cmd in ("recipe", "recipes"):
        run_py("recipe.py", *rest)
    elif cmd in ("wiki", "wikipedia"):
        do_wiki(rest)
    elif cmd == "web":
        do_web(rest)
    elif cmd == "ask":
        run_py("ask.py", *rest)
    elif cmd in ("brief", "detailed", "cite"):
        run_py("ask.py", *rest, extra_env={"JARVIS_MODE": cmd})
    elif cmd == "search":
        run_py("search.py", *rest)
    elif cmd == "find":
        run_py("semantic-search.py", *rest)
    elif cmd == "list":
        do_list()
    elif cmd == "voice":
        if rest and rest[0] == "--local":
            run_py("voice.py", extra_env={"JARVIS_BACKEND": "local"})
        else:
            run_py("voice.py")
    elif cmd in ("convo", "conversation"):
        if rest and rest[0] == "--local":
            run_py("voice.py", "--convo", extra_env={"JARVIS_BACKEND": "local"})
        else:
            run_py("voice.py", "--convo")
    elif cmd == "install-voice":
        subprocess.run(["bash", str(SCRIPTS / "install-voice.sh")])
    elif cmd in ("set-voice", "voice-select"):
        run_py("set-voice.py")
    elif cmd == "customize":
        run_py("customize.py")
    elif cmd in ("chat", "hello"):
        if fast_mode:
            run_py("chat.py", extra_env={"JARVIS_MODEL": "Jarvis-fast"})
        else:
            run_py("chat.py")
    elif cmd == "save":
        run_py("ask.py", *rest, extra_env={"JARVIS_SAVE": "1"})
    elif cmd == "remember":
        do_remember(rest)
    elif cmd == "set-location":
        do_set_location(rest)
    elif cmd == "download-regions":
        run_py("download-region-content.py", *rest)
    elif cmd == "download-coding":
        run_py("download-coding-content.py", *rest)
    elif cmd == "download-general":
        run_py("download-general-content.py", *rest)
    elif cmd == "rebuild-index":
        print("Rebuilding semantic index (this takes a few minutes)...")
        r = subprocess.run([PYTHON, str(SCRIPTS / "build-index.py")])
        sys.exit(r.returncode)
    elif cmd == "update":
        run_py("auto_update.py")
    elif cmd == "fetch":
        run_py("fetch_url.py", *rest)
    elif cmd == "pdf":
        subprocess.run(["bash", str(SCRIPTS / "refresh-pdf-index.sh")])
    elif cmd == "cache-clear":
        cache = JARVIS_BASE / "cache" / "qa"
        if cache.exists():
            shutil.rmtree(cache)
        print("Answer cache cleared.")
    elif cmd == "onboard":
        (CONFIG / "onboarding-done").unlink(missing_ok=True)
        run_py("onboarding.py", str(JARVIS_BASE))

    # ── default: treat as a question ─────────────────────────────────────────
    else:
        if fast_mode:
            run_py("ask.py", *args,
                   extra_env={"JARVIS_MODE": "brief", "JARVIS_MODEL": "Jarvis-fast"})
        else:
            run_py("ask.py", *args)


if __name__ == "__main__":
    main()
