#!/usr/bin/env python3
"""eli5.py — explain anything in plain simple terms"""
import sys, os, subprocess, tempfile
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: Jarvis eli5 "topic or concept"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

topic = " ".join(sys.argv[1:])

prompt = (
    f"You are Jarvis. Explain the following topic clearly and simply, as if the person has never heard of it before.\n\n"
    f"Topic: {topic}\n\n"
    f"Structure your response exactly like this:\n"
    f"1. ONE sentence: what it is in plain words (no jargon)\n"
    f"2. ONE analogy: 'Think of it like...' — a relatable real-world comparison\n"
    f"3. TWO to THREE sentences: why it matters or how it works in practice\n"
    f"4. ONE sentence: 'The key thing to remember is...'\n\n"
    f"Rules:\n"
    f"- No preamble. Start with the first sentence directly.\n"
    f"- No markdown, no bullet points, no headers — flowing prose only.\n"
    f"- If you must use a technical term, define it immediately in the same sentence.\n"
    f"- Use specific, vivid examples — not vague ones.\n"
    f"- Total length: 80-120 words.\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-eli5-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Simple Explanation  |  {topic[:45]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
