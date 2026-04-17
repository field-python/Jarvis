#!/usr/bin/env python3
"""edit.py — improve and polish any piece of writing"""
import sys, os, subprocess, tempfile
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: Jarvis edit "your text here"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

text = " ".join(sys.argv[1:])

prompt = (
    f"You are Jarvis, an expert editor. Improve the following text.\n\n"
    f"Original text:\n{text}\n\n"
    f"Rules:\n"
    f"- Fix grammar, spelling, punctuation\n"
    f"- Improve clarity and flow without changing the meaning or voice\n"
    f"- Cut unnecessary words\n"
    f"- Output the improved version first\n"
    f"- Then list 3-5 specific changes you made and why, as brief bullets\n"
    f"- If the text is already strong, say so and make only minor suggestions\n"
    f"- No preamble. Start with REVISED:\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-edit-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  Writing Editor")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
