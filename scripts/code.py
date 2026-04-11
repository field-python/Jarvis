#!/usr/bin/env python3
"""code.py — generate code using Jarvis (cross-platform replacement for code.sh)"""
import sys
import os
import io
import re
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")

CODE_MODEL = "qwen2.5-coder:7b"
host       = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
output_dir = Path.home() / "jarvis-code"
MAX_FIX    = 3

if len(sys.argv) < 2:
    print('Usage: Jarvis code "describe what you want to build"')
    print()
    print("Examples:")
    print('  Jarvis code "a script that renames all jpg files with today\'s date"')
    print('  Jarvis code "a Python calculator that handles division by zero"')
    print('  Jarvis code "a bash script that backs up a folder to a zip file"')
    sys.exit(1)

task       = " ".join(sys.argv[1:])
lower_task = task.lower()

# ── detect language ───────────────────────────────────────────────────────────
if re.search(r'\b(bash|shell|sh script|shell script)\b', lower_task):
    lang    = "bash"
    ext     = ".sh"
    run_cmd = ["bash"]
else:
    lang    = "python"
    ext     = ".py"
    run_cmd = [sys.executable]

# ── search coding notes for context (keyword, fast) ──────────────────────────
coding_notes = base_dir / "notes" / "coding"
context_block = ""
if coding_notes.is_dir():
    words = [w for w in re.split(r'\W+', task) if len(w) > 3][:5]
    hits  = []
    for md_file in coding_notes.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace").lower()
            if any(w.lower() in text for w in words):
                hits.append(md_file.read_text(encoding="utf-8", errors="replace")[:80 * 3])
                if len(hits) >= 3:
                    break
        except Exception:
            pass
    if hits:
        context_block = "Relevant coding reference:\n" + "\n".join(hits) + "\n\n"

# ── build prompt ──────────────────────────────────────────────────────────────
now    = datetime.now()
prompt = (
    f"You are an expert {lang} programmer. Write clean, working {lang} code.\n\n"
    f"Rules:\n"
    f"- Output ONLY a single complete code block — no explanation before or after unless asked\n"
    f"- Use a fenced code block: ```{lang} ... ```\n"
    f"- The code must be complete and runnable as-is\n"
    f"- Add brief inline comments only where the logic is non-obvious\n"
    f"- Handle obvious errors (empty input, missing files, division by zero) gracefully\n"
    f"- Keep it simple — no unnecessary dependencies or complexity\n\n"
    f"{context_block}"
    f"Task: {task}"
)

tmp_prompt = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", prefix="jarvis-code-", delete=False
)
tmp_prompt.write(prompt)
tmp_prompt.close()

print(f"Generating {lang} code...")
print()

# ── stream generate while capturing ──────────────────────────────────────────
proc = subprocess.Popen(
    [sys.executable, generate_script, CODE_MODEL, host, tmp_prompt.name],
    stdout=subprocess.PIPE, text=True
)
buf = io.StringIO()
for ch in iter(lambda: proc.stdout.read(1), ""):
    sys.stdout.write(ch)
    sys.stdout.flush()
    buf.write(ch)
proc.wait()
raw_output = buf.getvalue()
print()
os.unlink(tmp_prompt.name)

# ── extract code block ────────────────────────────────────────────────────────
code_blocks = re.findall(r'```[^\n]*\n(.*?)```', raw_output, re.DOTALL)
code        = code_blocks[0].strip() if code_blocks else raw_output.strip()

# ── save to file ──────────────────────────────────────────────────────────────
output_dir.mkdir(parents=True, exist_ok=True)
slug     = re.sub(r'[^a-z0-9]+', '-', task.lower()).strip('-')[:40]
stamp    = now.strftime("%Y-%m-%d")
out_file = output_dir / f"{stamp}-{slug}{ext}"
out_file.write_text(code + "\n", encoding="utf-8")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"  Saved: {out_file}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# ── optional run + self-correct loop ─────────────────────────────────────────
try:
    run_choice = input("Run it now? [y/N] ").strip().lower()
except (EOFError, KeyboardInterrupt):
    run_choice = ""

if run_choice not in ("y", "yes"):
    print(f"Done. Run it later with:  {' '.join(run_cmd)} \"{out_file}\"")
    sys.exit(0)

current_file = out_file
for attempt in range(1, MAX_FIX + 1):
    print()
    print(f"[Run attempt {attempt}/{MAX_FIX}]")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if lang == "bash":
        os.chmod(current_file, 0o755)

    result     = subprocess.run(run_cmd + [str(current_file)], capture_output=False, text=True)
    run_exit   = result.returncode

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if run_exit == 0:
        print("Ran successfully.")
        sys.exit(0)

    print(f"\nError detected (exit {run_exit}).")

    if attempt >= MAX_FIX:
        print("Max fix attempts reached. Review the error above and ask Jarvis to debug.")
        sys.exit(1)

    try:
        fix_choice = input("Auto-fix and retry? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        fix_choice = ""

    if fix_choice not in ("y", "yes"):
        print(f"Done. File is at: {current_file}")
        sys.exit(1)

    print("Fixing...")
    current_code = current_file.read_text(encoding="utf-8")
    # Re-run to get the error output for the fix prompt
    run_result   = subprocess.run(
        run_cmd + [str(current_file)], capture_output=True, text=True
    )
    run_output   = (run_result.stdout + run_result.stderr).strip()

    fix_prompt = (
        f"You are an expert {lang} programmer. The following {lang} code has an error.\n\n"
        f"Original task: {task}\n\n"
        f"Code:\n```{lang}\n{current_code}\n```\n\n"
        f"Error output:\n{run_output}\n\n"
        f"Fix the code so it runs correctly. Output ONLY the corrected code block — nothing else."
    )

    tmp_fix = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-fix-", delete=False
    )
    tmp_fix.write(fix_prompt)
    tmp_fix.close()

    fix_result = subprocess.run(
        [sys.executable, generate_script, CODE_MODEL, host, tmp_fix.name],
        capture_output=True, text=True
    )
    os.unlink(tmp_fix.name)

    fix_output  = fix_result.stdout
    code_blocks = re.findall(r'```[^\n]*\n(.*?)```', fix_output, re.DOTALL)
    fixed_code  = code_blocks[0].strip() if code_blocks else fix_output.strip()

    current_file.write_text(fixed_code + "\n", encoding="utf-8")
    print("Fixed. Retrying...")
