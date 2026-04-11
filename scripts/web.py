#!/usr/bin/env python3
"""
web.py — Jarvis web interface (Flask)
Serves a mobile-friendly chat UI at http://LOCAL-IP:5000
Access from any device on the same WiFi network (or Tailscale).
"""

import json
import os
import random
import secrets
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from flask import (Flask, Response, redirect, render_template,
                       request, session, url_for)
except ImportError:
    print("\n  Flask is not installed.")
    print("  Run setup.sh to install all dependencies, or:")
    print("  ~/.jarvis-venv/bin/pip install flask\n")
    sys.exit(1)

BASE    = Path(__file__).parent.parent.resolve()
SCRIPTS = BASE / "scripts"
CONFIG  = BASE / "config"
NOTES   = BASE / "notes"
MEMORY  = BASE / "memory"

venv   = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-venv"))
PYTHON = str(Path(venv) / "bin" / "python")

# ── command map ───────────────────────────────────────────────────────────────
# key: (script_name, extra_args_before_input, env_overrides)
COMMANDS = {
    "ask":            ("ask.py",              [],            {}),
    "brief":          ("ask.py",              [],            {"JARVIS_MODE": "brief"}),
    "detailed":       ("ask.py",              [],            {"JARVIS_MODE": "detailed"}),
    "cite":           ("ask.py",              [],            {"JARVIS_MODE": "cite"}),
    "firstaid":       ("firstaid.py",         [],            {}),
    "search":         ("search.py",           [],            {}),
    "find":           ("semantic-search.py",  [],            {}),
    "weather":        ("weather.py",          [],            {}),
    "news":           ("news.py",             [],            {}),
    "daily":          ("daily.py",            [],            {}),
    "skill":          ("skill.py",            [],            {}),
    "note":           ("note.py",             [],            {}),
    "recipe-list":    ("recipe.py",           ["--list"],    {}),
    "recipe-suggest": ("recipe.py",           ["suggest"],   {}),
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_secret():
    CONFIG.mkdir(parents=True, exist_ok=True)
    f = CONFIG / "web-secret.conf"
    if f.exists():
        val = f.read_text().strip()
        if val:
            return val
    key = secrets.token_hex(32)
    f.write_text(key)
    f.chmod(0o600)
    return key


def get_pin():
    f = CONFIG / "web-pin.conf"
    if f.exists():
        val = f.read_text().strip()
        if val:
            return val
    return None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def read_conf(name, default=""):
    f = CONFIG / name
    if f.exists():
        lines = [ln for ln in f.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        return lines[0].strip() if lines else default
    return default


def _sse(text):
    """Yield SSE events for a text string in 16-char chunks."""
    for i in range(0, len(text), 16):
        chunk = text[i:i + 16]
        yield f"data: {json.dumps({'t': chunk})}\n\n"


def _sse_done():
    yield "data: [DONE]\n\n"


def _groq_env(env):
    """Inject Groq credentials into env dict if groq-mode is active."""
    groq_conf = CONFIG / "groq.conf"
    groq_mode = CONFIG / "groq-mode"
    if groq_mode.exists() and groq_conf.exists():
        key = groq_conf.read_text().strip()
        if key:
            env["JARVIS_BACKEND"] = "groq"
            env["JARVIS_MODEL"]   = "llama-3.3-70b-versatile"
            env["GROQ_API_KEY"]   = key
    return env


# ── app ───────────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder=str(BASE / "templates"))
app.secret_key = _get_or_create_secret()
app.permanent_session_lifetime = timedelta(days=30)


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    location = read_conf("location.conf", "")
    return render_template("chat.html", location=location)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("index"))
    error = False
    if request.method == "POST":
        entered = request.form.get("pin", "").strip()
        if entered == get_pin():
            session["authenticated"] = True
            session.permanent = True
            return redirect(url_for("index"))
        error = True
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── inline command handlers ───────────────────────────────────────────────────

def _stream_notes():
    notes_dir  = NOTES / "personal-notes"
    today      = datetime.now().strftime("%Y-%m-%d")
    today_file = notes_dir / f"{today}.md"

    if today_file.exists():
        text  = today_file.read_text(encoding="utf-8")
        lines = [l for l in text.splitlines() if not l.startswith("#")]
        out   = "\n".join(lines).strip()
        yield from _sse(out if out else "No notes written today yet.")
    else:
        recent = sorted(notes_dir.glob("*.md"), reverse=True)[:3] if notes_dir.exists() else []
        if recent:
            lines = [f"No notes for today. Recent dates:"]
            for f in recent:
                lines.append(f"  {f.stem}")
            yield from _sse("\n".join(lines))
        else:
            yield from _sse("No notes yet. Use Save a Note to start.")
    yield from _sse_done()


def _stream_remember(inp):
    mem = MEMORY / "user-memory.md"
    mem.parent.mkdir(parents=True, exist_ok=True)
    with open(mem, "a", encoding="utf-8") as f:
        f.write(f"- [{datetime.now().strftime('%Y-%m-%d')}] {inp}\n")
    yield from _sse("Got it — I'll remember that.")
    yield from _sse_done()


# ── /run endpoint ─────────────────────────────────────────────────────────────

@app.route("/run", methods=["POST"])
def run():
    if not session.get("authenticated"):
        return Response("Unauthorized", status=401)

    data = request.get_json(silent=True) or {}
    cmd  = data.get("cmd", "ask").strip()
    inp  = data.get("input", "").strip()

    # ── inline handlers ───────────────────────────────────────────────────────
    if cmd == "notes":
        return Response(_stream_notes(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache",
                                 "X-Accel-Buffering": "no",
                                 "Connection": "keep-alive"})

    if cmd == "remember":
        if not inp:
            return Response("No input provided", status=400)
        return Response(_stream_remember(inp), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache",
                                 "X-Accel-Buffering": "no",
                                 "Connection": "keep-alive"})

    # ── script-based handlers ─────────────────────────────────────────────────
    if cmd not in COMMANDS:
        return Response(f"Unknown command: {cmd}", status=400)

    script, extra_args, env_overrides = COMMANDS[cmd]

    env = dict(os.environ)
    env["JARVIS_THINK"] = "0"
    env.update(env_overrides)
    _groq_env(env)

    # Build args: script + extra_args + optional input
    cmd_args = [PYTHON, str(SCRIPTS / script)] + extra_args
    if inp:
        cmd_args.append(inp)

    def stream():
        proc = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            bufsize=0,
        )
        try:
            while True:
                chunk = proc.stdout.read(16)
                if not chunk:
                    break
                yield f"data: {json.dumps({'t': chunk})}\n\n"
        finally:
            proc.stdout.close()
            proc.kill()
            proc.wait()
        yield "data: [DONE]\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


# ── legacy /ask endpoint (kept for compatibility) ─────────────────────────────

@app.route("/ask", methods=["POST"])
def ask():
    if not session.get("authenticated"):
        return Response("Unauthorized", status=401)
    data     = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    mode     = data.get("mode", "ask").strip()
    if not question:
        return Response("No question provided", status=400)
    # Forward to /run logic
    request._cached_json = ({"cmd": mode, "input": question}, True)
    # Just call run() directly isn't possible mid-request; rebuild inline
    script, extra_args, env_overrides = COMMANDS.get(mode, COMMANDS["ask"])
    env = dict(os.environ)
    env["JARVIS_THINK"] = "0"
    env.update(env_overrides)
    _groq_env(env)
    cmd_args = [PYTHON, str(SCRIPTS / script)] + extra_args + [question]

    def stream():
        proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True,
                                env=env, bufsize=0)
        try:
            while True:
                chunk = proc.stdout.read(16)
                if not chunk:
                    break
                yield f"data: {json.dumps({'t': chunk})}\n\n"
        finally:
            proc.stdout.close()
            proc.kill()
            proc.wait()
        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pin = get_pin()
    if not pin:
        pin = str(random.randint(1000, 9999))
        CONFIG.mkdir(parents=True, exist_ok=True)
        pf = CONFIG / "web-pin.conf"
        pf.write_text(pin)
        pf.chmod(0o600)
        print(f"\n  No PIN set — generated PIN: {pin}")
        print(f"  Change it anytime with:  Jarvis web-pin XXXX\n")

    ip   = get_local_ip()
    port = int(os.environ.get("JARVIS_PORT", 5000))

    print(f"\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Web UI  |  PIN: {pin}")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  This computer:   http://localhost:{port}")
    print(f"  Phone / tablet:  http://{ip}:{port}")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
