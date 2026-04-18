#!/usr/bin/env python3
"""Send a prompt to Ollama or Groq and stream the response, stripping <think> blocks."""
import sys
import os
from pathlib import Path

model  = sys.argv[1]
host   = sys.argv[2]
pfile  = sys.argv[3]

with open(pfile) as f:
    prompt = f.read()

backend   = os.environ.get("JARVIS_BACKEND", "ollama").lower()
use_think = os.environ.get("JARVIS_THINK", "1").lower() not in ("0", "false", "no")


def stream_output(chunks):
    """Stream chunks to stdout, stripping <think> blocks, with word wrapping."""
    import shutil
    try:
        cols = shutil.get_terminal_size().columns - 1
    except Exception:
        cols = 79

    in_think = False
    pending  = ""   # raw chunk accumulator for think-stripping
    word     = ""   # current word being built character by character
    col      = 0    # current terminal column position

    def emit(w, sep):
        """Emit a word followed by a separator (' ', '\n', or '')."""
        nonlocal col
        if sep == "\n":
            if col + len(w) > cols and col > 0 and w:
                sys.stdout.write("\n")
                col = 0
            sys.stdout.write(w + "\n")
            sys.stdout.flush()
            col = 0
        elif sep == " ":
            if col + len(w) > cols and col > 0 and w:
                sys.stdout.write("\n")
                col = 0
            sys.stdout.write(w)
            col += len(w)
            if col < cols:
                sys.stdout.write(" ")
                col += 1
            sys.stdout.flush()
        else:  # end of stream
            if col + len(w) > cols and col > 0 and w:
                sys.stdout.write("\n")
                col = 0
            sys.stdout.write(w)
            col += len(w)
            sys.stdout.flush()

    def process_text(text):
        """Feed text through word-wrap emitter."""
        nonlocal word
        for ch in text:
            if ch in (" ", "\n"):
                emit(word, ch)
                word = ""
            else:
                word += ch

    for chunk in chunks:
        if not chunk:
            continue
        pending += chunk

        while pending:
            if in_think:
                end = pending.find("</think>")
                if end == -1:
                    pending = ""
                    break
                pending  = pending[end + 8:].lstrip("\n")
                in_think = False
            else:
                start = pending.find("<think>")
                if start == -1:
                    # safe to emit all but last 7 chars (in case <think> is split)
                    safe = len(pending) - 7
                    if safe > 0:
                        process_text(pending[:safe])
                        pending = pending[safe:]
                    break
                process_text(pending[:start])
                pending  = pending[start + 7:]
                in_think = True

    if pending and not in_think:
        process_text(pending)

    # flush remaining word
    if word:
        emit(word, "")

    print()


if backend == "groq":
    try:
        from groq import Groq
    except ImportError:
        print("Error: groq package not installed. Run: pip install groq", file=sys.stderr)
        sys.exit(1)

    # Load API key — env var takes priority, then config file
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        config_path = Path(__file__).parent.parent / "config" / "groq.conf"
        if config_path.exists():
            api_key = config_path.read_text(encoding="utf-8").strip()

    if not api_key:
        print("Error: No Groq API key found.", file=sys.stderr)
        print("Run: Jarvis groq-key YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        def groq_chunks():
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        stream_output(groq_chunks())

    except Exception as e:
        name = type(e).__name__
        msg  = str(e)
        if "403" in msg or "PermissionDenied" in name:
            print("\n[Jarvis] Groq API blocked (403 — Access Denied).", file=sys.stderr)
            print("  This usually means your network or IP is being blocked by Groq.", file=sys.stderr)
            print("  Try: check your internet connection, disable a VPN, or switch to Ollama.", file=sys.stderr)
        elif "401" in msg or "Authentication" in name:
            print("\n[Jarvis] Groq API key rejected (401).", file=sys.stderr)
            print("  Run: Jarvis groq-key YOUR_API_KEY  to update it.", file=sys.stderr)
        elif "429" in msg or "RateLimit" in name:
            print("\n[Jarvis] Groq rate limit hit — wait a moment and try again.", file=sys.stderr)
        elif "timeout" in msg.lower() or "ConnectionError" in name:
            print("\n[Jarvis] Could not reach Groq — check your internet connection.", file=sys.stderr)
        else:
            print(f"\n[Jarvis] Groq request failed: {e}", file=sys.stderr)
        sys.exit(1)

else:
    import ollama

    client = ollama.Client(host=f"http://{host}")

    def ollama_chunks():
        gen_kwargs = dict(model=model, prompt=prompt, stream=True)
        if not use_think:
            gen_kwargs["think"] = False
        for part in client.generate(**gen_kwargs):
            if isinstance(part, dict):
                yield part.get("response", "")
            else:
                yield getattr(part, "response", "") or ""

    stream_output(ollama_chunks())
