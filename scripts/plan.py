#!/usr/bin/env python3
"""plan.py — break any goal into a concrete action plan"""
import sys, os, subprocess, tempfile
from pathlib import Path
from datetime import datetime

if len(sys.argv) < 2:
    print('Usage: Jarvis plan "goal or project"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

goal         = " ".join(sys.argv[1:])
current_date = datetime.now().strftime("%A, %B %d, %Y")

prompt = (
    f"You are Jarvis, a practical planning assistant. Today is {current_date}.\n\n"
    f"Create a concrete action plan for the following goal:\n"
    f"Goal: {goal}\n\n"
    f"Rules:\n"
    f"- Break it into phases (2-4 phases depending on scope)\n"
    f"- Each phase: 3-5 specific, actionable steps\n"
    f"- Each step starts with a verb (Do, Build, Research, Contact, etc.)\n"
    f"- Note any dependencies (what must happen before what)\n"
    f"- End with: QUICK WINS — 2-3 things that can be done today or this week\n"
    f"- No preamble. Start with Phase 1.\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-plan-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Action Plan  |  {goal[:45]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
