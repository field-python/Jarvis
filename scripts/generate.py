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
    """Stream chunks to stdout, stripping <think>...</think> blocks."""
    in_think = False
    pending  = ""

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
                    safe = len(pending) - 7
                    if safe > 0:
                        print(pending[:safe], end="", flush=True)
                        pending = pending[safe:]
                    break
                print(pending[:start], end="", flush=True)
                pending  = pending[start + 7:]
                in_think = True

    if pending and not in_think:
        print(pending, end="", flush=True)

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
