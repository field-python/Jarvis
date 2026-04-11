#!/usr/bin/env python3
"""firstaid.py — offline first aid and emergency medical reference"""
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

if len(sys.argv) < 2:
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Jarvis First Aid  |  Emergency Reference")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("  Usage: Jarvis firstaid \"topic\"")
    print()
    print("  Examples:")
    print("    Jarvis firstaid \"severe bleeding\"")
    print("    Jarvis firstaid \"hypothermia\"")
    print("    Jarvis firstaid \"broken bone\"")
    print("    Jarvis firstaid \"heart attack\"")
    print("    Jarvis firstaid \"choking\"")
    print("    Jarvis firstaid \"burn treatment\"")
    print("    Jarvis firstaid \"snakebite\"")
    print("    Jarvis firstaid \"allergic reaction\"")
    print("    Jarvis firstaid \"frostbite\"")
    print("    Jarvis firstaid \"wound infection\"")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    sys.exit(0)

topic = " ".join(sys.argv[1:]).strip()

# Search archive for any relevant first aid content
archive_context = ""
try:
    semantic_script = base_dir / "scripts" / "semantic-search.py"
    if semantic_script.exists():
        result = subprocess.run(
            [sys.executable, str(semantic_script), f"first aid {topic}"],
            capture_output=True, text=True, timeout=10
        )
        hits = result.stdout.strip()
        if hits:
            archive_context = f"\nRelevant archive excerpts:\n{hits}\n"
except Exception:
    pass

prompt = (
    f"You are Jarvis, an offline first aid and emergency medical reference. "
    f"Today is {current_date}.\n\n"
    f"Provide clear, step-by-step first aid guidance for: {topic}\n\n"
    f"Format your response exactly like this:\n\n"
    f"SITUATION: [one sentence describing when this applies]\n\n"
    f"CALL 911 / GET HELP IF: [list 2-4 conditions that require professional medical help]\n\n"
    f"IMMEDIATE STEPS:\n"
    f"1. [first action — most urgent]\n"
    f"2. [second action]\n"
    f"3. [continue as needed, 3-7 steps total]\n\n"
    f"WATCH FOR: [2-3 warning signs that the situation is getting worse]\n\n"
    f"DO NOT: [1-3 common mistakes to avoid]\n\n"
    f"Rules:\n"
    f"- Be specific and actionable. Someone may be using this in a real emergency.\n"
    f"- Use plain language. No jargon unless explained.\n"
    f"- Steps should be ordered by urgency.\n"
    f"- If the topic is outside first aid scope, say so clearly.\n"
    f"- Do not add disclaimers that interrupt the instructions — put them in CALL 911 section.\n"
    f"{archive_context}"
)

tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-firstaid-", delete=False
)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Jarvis First Aid  |  {topic.title()}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("  ! When professional help is available, always seek it.")
print()

subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
