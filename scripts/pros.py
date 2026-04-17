#!/usr/bin/env python3
"""pros.py — structured pros and cons analysis"""
import sys, os, subprocess, tempfile
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: Jarvis pros "decision or topic"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

topic = " ".join(sys.argv[1:])

prompt = (
    f"You are Jarvis, a clear-headed analytical assistant.\n\n"
    f"Give a thorough pros and cons analysis of the following:\n"
    f"Topic: {topic}\n\n"
    f"Rules:\n"
    f"- List 5-7 pros and 5-7 cons\n"
    f"- Each point: one line, specific, not generic\n"
    f"- Weight the most important points — mark them with ★\n"
    f"- After the list: one paragraph verdict — what does the balance suggest?\n"
    f"- Format: PROS header, numbered list, then CONS header, numbered list, then VERDICT\n"
    f"- No preamble. Start with PROS:\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-pros-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Pros & Cons  |  {topic[:50]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
