#!/usr/bin/env python3
"""
web.py — Jarvis web interface (Flask)
Serves a mobile-friendly chat UI at http://LOCAL-IP:5000
Access from any device on the same WiFi network (or Tailscale).
"""

import json
import os
import re
import random
import secrets
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def _ensure_ssl_cert(config_dir):
    """Generate a self-signed cert (with SAN) and return an ssl.SSLContext, or None."""
    import ssl
    ssl_dir  = config_dir / "ssl"
    cert     = ssl_dir / "cert.pem"
    key      = ssl_dir / "key.pem"
    san_mark = ssl_dir / ".san-ok"   # sentinel: cert was built with SAN

    need_regen = not (cert.exists() and key.exists() and san_mark.exists())
    if need_regen:
        ssl_dir.mkdir(parents=True, exist_ok=True)
        # Remove old cert so we start clean
        cert.unlink(missing_ok=True)
        key.unlink(missing_ok=True)
        san_mark.unlink(missing_ok=True)

        local_ip = get_local_ip()
        # Collect all IPs this machine is reachable on (WiFi + Tailscale + loopback)
        all_ips = {local_ip, "127.0.0.1"}
        try:
            import socket as _sock
            for info in _sock.getaddrinfo(_sock.gethostname(), None):
                addr = info[4][0]
                if ":" not in addr:   # skip IPv6
                    all_ips.add(addr)
        except Exception:
            pass
        san = ",".join(f"IP:{ip}" for ip in sorted(all_ips)) + ",DNS:localhost"
        try:
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048",
                    "-keyout", str(key),
                    "-out",    str(cert),
                    "-days",   "3650",
                    "-nodes",
                    "-subj",   "/CN=jarvis.local",
                    "-addext", f"subjectAltName={san}",
                ],
                check=True, capture_output=True,
            )
            san_mark.write_text(san)
        except Exception as e:
            print(f"  SSL cert generation failed: {e}")
            print("  Running on plain HTTP — microphone may not work on phone.")
            return None

    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(cert), str(key))
        return ctx
    except Exception as e:
        print(f"  SSL load failed: {e}")
        return None

try:
    from flask import (Flask, Response, redirect, render_template,
                       request, session, url_for, jsonify)
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
    # New commands
    "symptom":        ("symptom.py",          [],            {}),
    "brainstorm":     ("brainstorm.py",       [],            {}),
    "pros":           ("pros.py",             [],            {}),
    "eli5":           ("eli5.py",             [],            {}),
    "compare":        ("compare.py",          [],            {}),
    "plan":           ("plan.py",             [],            {}),
    "translate":      ("translate.py",        [],            {}),
    "edit":           ("edit.py",             [],            {}),
    "calc":           ("calc.py",             [],            {}),
    "todo":           ("todo.py",             [],            {}),
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


# ── conversation history helpers ─────────────────────────────────────────────

def _history_file():
    d = BASE / "notes" / "web-history"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def _save_exchange(cmd, user_input, response_text):
    """Append a Q&A pair to today's history file."""
    try:
        entry = json.dumps({
            "time":  datetime.now().strftime("%H:%M"),
            "cmd":   cmd,
            "input": user_input,
            "reply": response_text,
        })
        with open(_history_file(), "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def _load_history(date_str=None):
    d = BASE / "notes" / "web-history"
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    f = d / f"{date_str}.jsonl"
    if not f.exists():
        return []
    entries = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


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
    env["JARVIS_WEB"]   = "1"
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
            stdin=subprocess.DEVNULL,
            text=True,
            env=env,
            bufsize=0,
        )
        full_response = []
        try:
            while True:
                chunk = proc.stdout.read(16)
                if not chunk:
                    break
                full_response.append(chunk)
                yield f"data: {json.dumps({'t': chunk})}\n\n"
        finally:
            proc.stdout.close()
            proc.kill()
            proc.wait()
        _save_exchange(cmd, inp, "".join(full_response).strip())
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


# ── /history endpoint ─────────────────────────────────────────────────────────

@app.route("/stocks")
def stocks_page():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return render_template("stocks.html")


@app.route("/api/stocks")
def stocks_api():
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import yfinance as yf
    except ImportError:
        return jsonify({"error": "yfinance not installed"}), 500

    symbol = request.args.get("symbol", "SPY").upper()
    period = request.args.get("period", "1mo")

    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"}
    if period not in valid_periods:
        period = "1mo"

    try:
        t    = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period=period)

        if hist.empty:
            return jsonify({"error": f"No data for {symbol}"}), 404

        prices = [round(float(p), 4) for p in hist["Close"]]
        labels = [str(d.date()) for d in hist.index]

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or prices[-1]
        prev  = info.get("regularMarketPreviousClose") or info.get("previousClose") or prices[-2]
        change = round(price - prev, 4) if price and prev else 0
        pct    = round(change / prev * 100, 2) if prev else 0

        div_yield = info.get("dividendYield")
        if div_yield:
            div_yield = div_yield if div_yield < 1 else div_yield / 100
            div_yield = round(div_yield * 100, 2)

        return jsonify({
            "symbol":    symbol,
            "name":      info.get("shortName") or info.get("longName") or symbol,
            "price":     round(float(price), 4) if price else None,
            "change":    change,
            "pct":       pct,
            "labels":    labels,
            "prices":    prices,
            "market_cap": info.get("marketCap"),
            "volume":    info.get("volume"),
            "avg_volume":info.get("averageVolume"),
            "hi52":      info.get("fiftyTwoWeekHigh"),
            "lo52":      info.get("fiftyTwoWeekLow"),
            "pe":        info.get("trailingPE"),
            "div_yield": div_yield,
            "sector":    info.get("sector", ""),
            "exchange":  info.get("exchange", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stocks/watchlist/add", methods=["POST"])
def stocks_watchlist_add():
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401
    sym     = request.args.get("symbol", "").upper().strip()
    wl_file = CONFIG / "watchlist.json"
    wl = json.loads(wl_file.read_text()) if wl_file.exists() else ["SPY","AAPL","TSLA","NVDA","BTC-USD"]
    if sym and sym not in wl:
        wl.append(sym)
        wl_file.write_text(json.dumps(wl, indent=2))
    return jsonify({"ok": True, "watchlist": wl})


@app.route("/api/stocks/watchlist/remove", methods=["POST"])
def stocks_watchlist_remove():
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401
    sym     = request.args.get("symbol", "").upper().strip()
    wl_file = CONFIG / "watchlist.json"
    wl = json.loads(wl_file.read_text()) if wl_file.exists() else []
    wl = [s for s in wl if s != sym]
    wl_file.write_text(json.dumps(wl, indent=2))
    return jsonify({"ok": True, "watchlist": wl})


@app.route("/api/stocks/watchlist")
def stocks_watchlist_api():
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import yfinance as yf
    except ImportError:
        return jsonify({"error": "yfinance not installed"}), 500

    wl_file = CONFIG / "watchlist.json"
    if wl_file.exists():
        try:
            watchlist = json.loads(wl_file.read_text())
        except Exception:
            watchlist = ["SPY", "AAPL", "TSLA", "NVDA", "BTC-USD"]
    else:
        watchlist = ["SPY", "AAPL", "TSLA", "NVDA", "BTC-USD"]

    results = []
    for sym in watchlist:
        try:
            t    = yf.Ticker(sym)
            info = t.info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            prev  = info.get("regularMarketPreviousClose") or info.get("previousClose")
            change = round(price - prev, 4) if price and prev else 0
            pct    = round(change / prev * 100, 2) if prev else 0
            results.append({
                "symbol": sym,
                "name":   (info.get("shortName") or sym)[:20],
                "price":  round(float(price), 2) if price else None,
                "change": change,
                "pct":    pct,
            })
        except Exception:
            results.append({"symbol": sym, "name": sym, "price": None, "change": 0, "pct": 0})

    return jsonify(results)


@app.route("/games")
def games():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return render_template("games.html")


@app.route("/game/<name>")
def game(name):
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    safe = re.sub(r'[^a-z0-9\-]', '', name)
    tmpl = f"game-{safe}.html"
    try:
        return render_template(tmpl)
    except Exception:
        return "Game not found", 404


@app.route("/history")
def history():
    if not session.get("authenticated"):
        return Response("Unauthorized", status=401)
    date_str = request.args.get("date", "")
    entries  = _load_history(date_str or None)
    # List available dates
    d = BASE / "notes" / "web-history"
    dates = sorted((f.stem for f in d.glob("*.jsonl")), reverse=True)[:30] if d.exists() else []
    return {"entries": entries, "dates": dates}


# ── /transcribe endpoint (Whisper server-side STT) ───────────────────────────

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not session.get("authenticated"):
        return Response("Unauthorized", status=401)

    audio_file = request.files.get("audio")
    if not audio_file:
        return {"error": "no audio"}, 400

    import tempfile
    suffix = ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, language="en")
        text = " ".join(s.text for s in segments).strip()
        return {"text": text}
    except Exception as e:
        return {"error": str(e), "text": ""}, 500
    finally:
        try:
            os.unlink(audio_path)
        except Exception:
            pass


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
    env["JARVIS_WEB"]   = "1"
    env.update(env_overrides)
    _groq_env(env)
    cmd_args = [PYTHON, str(SCRIPTS / script)] + extra_args + [question]

    def stream():
        proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                text=True, env=env, bufsize=0)
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

    ssl_context = _ensure_ssl_cert(CONFIG)
    scheme = "https" if ssl_context else "http"

    print(f"\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Jarvis Web UI  |  PIN: {pin}")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  This computer:   {scheme}://localhost:{port}")
    print(f"  Phone / tablet:  {scheme}://{ip}:{port}")
    if ssl_context:
        print(f"  (browser will warn 'not secure' — tap Advanced → Proceed)")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True,
            ssl_context=ssl_context)
