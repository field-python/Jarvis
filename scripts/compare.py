#!/usr/bin/env python3
"""compare.py — side-by-side comparison of two things"""
import sys, os, subprocess, tempfile
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: Jarvis compare "X vs Y"')
    sys.exit(1)

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

topic = " ".join(sys.argv[1:])

prompt = (
    f"You are Jarvis. Create a clear, well-organized comparison.\n\n"
    f"Comparison: {topic}\n\n"
    f"Format your response like this:\n"
    f"- Start with a one-line intro naming both things\n"
    f"- Compare across 5-6 meaningful dimensions using this format for each:\n"
    f"  [emoji] DIMENSION NAME\n"
    f"  • [Thing 1]: specific detail\n"
    f"  • [Thing 2]: specific detail\n"
    f"- End with a '🏆 BEST FOR' section:\n"
    f"  • [Thing 1]: who or what it suits best\n"
    f"  • [Thing 2]: who or what it suits best\n\n"
    f"Rules:\n"
    f"- Use relevant emojis for each dimension (e.g. 💰 for cost, ⚡ for speed, 🛡️ for durability)\n"
    f"- Be specific and concrete — numbers, real trade-offs, not vague praise\n"
    f"- No preamble beyond the one-line intro. Don't say 'here is a comparison'.\n"
)

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-compare-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Compare  |  {topic[:50]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
