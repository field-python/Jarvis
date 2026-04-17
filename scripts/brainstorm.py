#!/usr/bin/env python3
"""brainstorm.py — generate a structured list of ideas on any topic"""
import sys, os, subprocess, tempfile
from pathlib import Path
from datetime import datetime

if len(sys.argv) < 2:
    print('Usage: Jarvis brainstorm "topic or problem"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

topic        = " ".join(sys.argv[1:])
current_date = datetime.now().strftime("%A, %B %d, %Y")

prompt = (
    f"You are Jarvis, a creative brainstorming assistant. Today is {current_date}.\n\n"
    f"Generate a rich, diverse set of ideas for the following topic or problem:\n"
    f"Topic: {topic}\n\n"
    f"Rules:\n"
    f"- Generate 12-15 distinct ideas\n"
    f"- Group them into 3-4 natural categories\n"
    f"- Each idea: one line, specific and actionable, not vague\n"
    f"- Include conventional ideas AND unexpected/creative ones\n"
    f"- Format: Category header, then numbered ideas under it\n"
    f"- No preamble. Start directly with the first category.\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-brainstorm-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Brainstorm  |  {topic[:50]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
