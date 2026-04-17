#!/usr/bin/env python3
"""translate.py — translate text to another language"""
import sys, os, subprocess, tempfile, re
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: Jarvis translate "text" to Spanish')
    print('       Jarvis translate "text"   (defaults to Spanish)')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

raw = " ".join(sys.argv[1:])

# Parse "text to Language" pattern
m = re.search(r'\bto\s+([A-Za-z]+)\s*$', raw, re.IGNORECASE)
if m:
    target_lang = m.group(1).capitalize()
    text        = raw[:m.start()].strip()
else:
    target_lang = "Spanish"
    text        = raw

prompt = (
    f"You are Jarvis, a translation assistant.\n\n"
    f"Translate the following text to {target_lang}.\n\n"
    f"Text: {text}\n\n"
    f"Rules:\n"
    f"- Provide the translation first\n"
    f"- Then provide a literal word-for-word breakdown if the translation differs significantly from the source\n"
    f"- Note any idioms or phrases that don't translate directly\n"
    f"- Keep cultural context where relevant\n"
    f"- No preamble. Start with the translation.\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-translate-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Translate to {target_lang}  |  {text[:40]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
