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
from datetime import timedelta
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

venv   = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-venv"))
PYTHON = str(Path(venv) / "bin" / "python")


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


@app.route("/ask", methods=["POST"])
def ask():
    if not session.get("authenticated"):
        return Response("Unauthorized", status=401)

    data     = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    mode     = data.get("mode", "normal")

    if not question:
        return Response("No question provided", status=400)

    env = dict(os.environ)
    env["JARVIS_MODE"]  = mode
    env["JARVIS_THINK"] = "0"

    # Respect groq mode if configured
    groq_conf = CONFIG / "groq.conf"
    groq_mode = CONFIG / "groq-mode"
    if groq_mode.exists() and groq_conf.exists():
        key = groq_conf.read_text().strip()
        if key:
            env["JARVIS_BACKEND"] = "groq"
            env["JARVIS_MODEL"]   = "llama-3.3-70b-versatile"
            env["GROQ_API_KEY"]   = key

    def stream():
        proc = subprocess.Popen(
            [PYTHON, str(SCRIPTS / "ask.py"), question],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            bufsize=0,
        )
        try:
            for char in iter(lambda: proc.stdout.read(1), ""):
                yield f"data: {json.dumps({'c': char})}\n\n"
        finally:
            proc.stdout.close()
            proc.kill()
            proc.wait()
        yield "data: [DONE]\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


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
