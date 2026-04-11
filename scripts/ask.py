#!/usr/bin/env python3
"""ask.py — ask Jarvis a question using the local archive as context
Env vars:
  JARVIS_MODE   — normal (default), brief, detailed, cite, voice, code
  JARVIS_MODEL  — ollama model name (default: Jarvis)
  OLLAMA_HOST   — ollama host (default: 127.0.0.1:11434)
  JARVIS_SAVE   — set to 1 to save answer to notes
"""
import sys
import os
import io
import hashlib
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")

model       = os.environ.get("JARVIS_MODEL", "Jarvis")
host        = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
mode        = os.environ.get("JARVIS_MODE", "normal")
save_answer = os.environ.get("JARVIS_SAVE", "0") == "1"

# Disable Qwen3 thinking mode — faster responses, no meaningful quality loss for Q&A
os.environ["JARVIS_THINK"] = "0"

if len(sys.argv) < 2:
    print("Usage: ask.py <question>")
    sys.exit(1)

question = " ".join(sys.argv[1:])

# ── archive search ────────────────────────────────────────────────────────────
hits = ""
if mode not in ("brief", "voice"):
    semantic_script = base_dir / "scripts" / "semantic-search.py"
    if semantic_script.exists():
        result = subprocess.run(
            [sys.executable, str(semantic_script), question],
            capture_output=True, text=True
        )
        hits = result.stdout.strip()

    if not hits:
        # Keyword fallback
        search_script = base_dir / "scripts" / "search.py"
        if search_script.exists():
            result = subprocess.run(
                [sys.executable, str(search_script), question],
                capture_output=True, text=True
            )
            raw_hits = result.stdout.strip().splitlines()
            # Filter noise, cap at 4 lines, 500 chars each
            filtered = [ln[:500] for ln in raw_hits
                        if "/templates/" not in ln and "/.cache/" not in ln][:4]
            hits = "\n".join(filtered)

context_block = hits.replace(str(base_dir) + "/", "") if hits else ""

# ── location ─────────────────────────────────────────────────────────────────
location_conf = base_dir / "config" / "location.conf"
if location_conf.exists():
    lines = [ln for ln in location_conf.read_text(encoding="utf-8").splitlines()
             if not ln.strip().startswith("#")]
    user_location = lines[0].strip() if lines else "North America"
else:
    user_location = "North America"

# ── user memory ───────────────────────────────────────────────────────────────
memory_file  = base_dir / "memory" / "user-memory.md"
memory_block = ""
if memory_file.exists():
    lines = [ln for ln in memory_file.read_text(encoding="utf-8").splitlines()
             if ln.strip()
             and not ln.strip().startswith("#")
             and not ln.strip().startswith("<!--")
             and not ln.strip().startswith("-->")]
    memory_block = "\n".join(lines)

# ── mode instruction ──────────────────────────────────────────────────────────
MODE_INSTRUCTIONS = {
    "brief": (
        "Answer in under 80 words using your own knowledge. "
        "Be direct and practical. If genuinely uncertain, say so in one phrase."
    ),
    "detailed": (
        "Give a thorough answer with clear steps and useful context. "
        "Use headers or bullets where helpful. "
        "Suggest follow-up questions under 'Next questions:' if useful."
    ),
    "cite": (
        "Answer clearly, then list sources under 'Sources:' using the archive file names. "
        "Suggest follow-up questions under 'Next questions:' if useful."
    ),
    "voice": (
        "Answer in 2-4 plain sentences as if speaking aloud. "
        "No bullet points, no headers, no markdown, no code blocks, no follow-up questions. "
        "Use natural spoken language — say 'first, then, finally' instead of lists."
    ),
    "code": (
        "You are helping someone who is learning to code. "
        "Explain concepts clearly using plain English and real analogies. "
        "Always show working code examples. Explain what each part of the code does and WHY "
        "it works that way — not just what to type. "
        "Point out common beginner mistakes. Be encouraging. "
        "If there are multiple ways to do something, show the simplest one first."
    ),
}
mode_instruction = MODE_INSTRUCTIONS.get(
    mode,
    "Give a clear, practical answer. Match length to complexity. "
    "Suggest follow-up questions under 'Next questions:' if useful."
)

# ── archive section ───────────────────────────────────────────────────────────
if context_block:
    archive_section = f"Local archive excerpts (use as primary evidence):\n{context_block}"
else:
    archive_section = "No archive excerpts found — answer from general knowledge."

# ── question cache (brief + normal only) ─────────────────────────────────────
cache_dir  = base_dir / "cache" / "qa"
cache_key  = ""
cache_file = None

if mode in ("brief", "normal"):
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key  = hashlib.md5(f"{mode}|{question}".encode()).hexdigest()
    cache_file = cache_dir / f"{cache_key}.txt"
    if cache_file.exists():
        print(cache_file.read_text(encoding="utf-8"), end="")
        print("\n(cached — 'Jarvis cache-clear' to reset)", file=sys.stderr)
        sys.exit(0)

# ── build prompt ──────────────────────────────────────────────────────────────
now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

memory_section = (
    f"User memory (personal facts to keep in mind):\n{memory_block}\n\n"
    if memory_block else ""
)

prompt = (
    f"You are Jarvis, an advanced offline AI assistant covering all of North America.\n"
    f"Today's date: {current_date}. Your training data extends to early 2025. "
    f"If the user provides current information, accept it as fact.\n\n"
    f"The user's home region is {user_location}. ONLY mention this if the question is "
    f"explicitly about geography, local wildlife, regional weather, local laws, or wilderness "
    f"conditions. Do NOT add location context to questions about technology, math, science, "
    f"history, coding, general knowledge, or anything that is not location-specific. "
    f"Most questions have nothing to do with location — treat them normally.\n\n"
    f"If the user mentions a specific location in their question, use that location. "
    f"Do not override it.\n\n"
    f"Rules:\n"
    f"- Answer from archive excerpts when relevant; otherwise use general knowledge.\n"
    f"- Do not invent facts.\n"
    f"- Do not tell the user to visit websites or search the internet.\n"
    f"- Do not mention file paths or archive structure unless citations were requested.\n\n"
    f"Mode: {mode_instruction}\n\n"
    f"{memory_section}"
    f"Question: {question}\n\n"
    f"{archive_section}"
)

# ── generate ──────────────────────────────────────────────────────────────────
tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-prompt-", delete=False
)
tmp.write(prompt)
tmp.close()


def stream_and_capture(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    buf  = io.StringIO()
    for ch in iter(lambda: proc.stdout.read(1), ""):
        sys.stdout.write(ch)
        sys.stdout.flush()
        buf.write(ch)
    proc.wait()
    return buf.getvalue()


if save_answer:
    response = stream_and_capture(
        [sys.executable, generate_script, model, host, tmp.name]
    )
    save_dir = base_dir / "notes" / "saved-answers"
    save_dir.mkdir(parents=True, exist_ok=True)
    slug     = hashlib.md5(question.encode()).hexdigest()[:12]
    stamp    = now.strftime("%Y-%m-%d")
    out      = save_dir / f"{stamp}-{slug}.md"
    out.write_text(
        f"# {question}\n\n**Date:** {stamp}\n\n**Question:** {question}\n\n## Answer\n\n{response}\n",
        encoding="utf-8"
    )
    print(f"\nSaved: {out}", file=sys.stderr)
else:
    response = stream_and_capture(
        [sys.executable, generate_script, model, host, tmp.name]
    )

os.unlink(tmp.name)

# ── cache ─────────────────────────────────────────────────────────────────────
if cache_key and cache_file and response.strip():
    cache_file.write_text(response, encoding="utf-8")
