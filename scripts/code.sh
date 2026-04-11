#!/usr/bin/env bash
# code.sh — Jarvis coding assistant using qwen2.5-coder
# Usage: code.sh "describe what you want to build"
#
# Features:
#   - Uses qwen2.5-coder:7b for better code quality
#   - Searches ARCHIVE coding notes for relevant context
#   - Saves generated code to a file automatically
#   - Optional self-correcting run loop (tries to fix errors up to 3 times)

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"

CODE_MODEL="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"
output_dir="$HOME/jarvis-code"
max_fix_attempts=3

if [[ $# -lt 1 ]]; then
  echo "Usage: Jarvis code \"describe what you want to build\""
  echo ""
  echo "Examples:"
  echo "  Jarvis code \"a script that renames all jpg files in a folder with today's date\""
  echo "  Jarvis code \"a Python calculator that handles division by zero\""
  echo "  Jarvis code \"a bash script that backs up a folder to a zip file\""
  exit 1
fi

task="$*"

# ── detect language from task description ─────────────────────────────────────
lang="python"
ext=".py"
run_cmd="$venv_python"

lower_task="$(printf '%s' "$task" | tr '[:upper:]' '[:lower:]')"
if printf '%s' "$lower_task" | grep -qE '\b(bash|shell|sh script|shell script)\b'; then
  lang="bash"
  ext=".sh"
  run_cmd="bash"
elif printf '%s' "$lower_task" | grep -qE '\b(python|py)\b'; then
  lang="python"
  ext=".py"
  run_cmd="$venv_python"
fi

# ── search coding notes for relevant context (keyword search — fast) ──────────
hits="$(
  grep -r --include="*.md" -il \
    "$(printf '%s' "$task" | tr ' ' '\n' | awk 'length>3' | head -5 | paste -sd'|')" \
    "$base_dir/notes/coding/" 2>/dev/null \
    | head -3 \
    | xargs -I{} head -80 {} 2>/dev/null \
  || true
)"

context_block=""
[[ -n "$hits" ]] && context_block="Relevant coding reference:
$hits

"

# ── build prompt ──────────────────────────────────────────────────────────────
current_date="$(date '+%Y-%m-%d')"

prompt="$(cat <<EOF
You are an expert $lang programmer. Write clean, working $lang code.

Rules:
- Output ONLY a single complete code block — no explanation before or after unless asked
- Use a fenced code block: \`\`\`$lang ... \`\`\`
- The code must be complete and runnable as-is
- Add brief inline comments only where the logic is non-obvious
- Handle obvious errors (empty input, missing files, division by zero) gracefully
- Keep it simple — no unnecessary dependencies or complexity

${context_block}Task: $task
EOF
)"

# ── generate ──────────────────────────────────────────────────────────────────
tmp_prompt="$(mktemp /tmp/jarvis-code-XXXXXX.txt)"
printf '%s\n' "$prompt" > "$tmp_prompt"

echo "Generating $lang code..."
echo ""

tmp_response="$(mktemp /tmp/jarvis-code-resp-XXXXXX.txt)"
"$venv_python" "$base_dir/scripts/generate.py" "$CODE_MODEL" "$host" "$tmp_prompt" | tee "$tmp_response"
echo ""
raw_output="$(cat "$tmp_response")"
rm -f "$tmp_prompt" "$tmp_response"

# ── extract code block ────────────────────────────────────────────────────────
code="$(printf '%s\n' "$raw_output" | sed -n '/^```/,/^```/{/^```/d;p}')"

if [[ -z "$code" ]]; then
  # No fenced block — use the whole output
  code="$raw_output"
fi

# ── save to file ──────────────────────────────────────────────────────────────
mkdir -p "$output_dir"
slug="$(printf '%s' "$task" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/-\+/-/g; s/^-//; s/-$//' | cut -c1-40)"
stamp="$(date +%Y-%m-%d)"
out_file="$output_dir/${stamp}-${slug}${ext}"

printf '%s\n' "$code" > "$out_file"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Saved: $out_file"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── optional run + self-correct loop ─────────────────────────────────────────
read -r -p "Run it now? [y/N] " run_choice
if [[ ! "$run_choice" =~ ^[Yy]$ ]]; then
  echo "Done. Run it later with:  $run_cmd \"$out_file\""
  exit 0
fi

attempt=1
current_file="$out_file"

while [[ $attempt -le $max_fix_attempts ]]; do
  echo ""
  echo "[Run attempt $attempt/$max_fix_attempts]"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ "$lang" == "bash" ]]; then
    chmod +x "$current_file"
  fi

  run_output="$($run_cmd "$current_file" 2>&1)" && run_exit=0 || run_exit=$?

  printf '%s\n' "$run_output"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ $run_exit -eq 0 ]]; then
    echo "Ran successfully."
    exit 0
  fi

  echo ""
  echo "Error detected (exit $run_exit)."

  if [[ $attempt -ge $max_fix_attempts ]]; then
    echo "Max fix attempts reached. Review the error above and ask Jarvis to debug."
    exit 1
  fi

  read -r -p "Auto-fix and retry? [y/N] " fix_choice
  if [[ ! "$fix_choice" =~ ^[Yy]$ ]]; then
    echo "Done. File is at: $current_file"
    exit 1
  fi

  # ── ask model to fix the error ────────────────────────────────────────────
  echo "Fixing..."
  current_code="$(cat "$current_file")"
  fix_prompt="$(cat <<EOF
You are an expert $lang programmer. The following $lang code has an error.

Original task: $task

Code:
\`\`\`$lang
$current_code
\`\`\`

Error output:
$run_output

Fix the code so it runs correctly. Output ONLY the corrected code block — nothing else.
EOF
)"

  tmp_fix="$(mktemp /tmp/jarvis-fix-XXXXXX.txt)"
  printf '%s\n' "$fix_prompt" > "$tmp_fix"

  fix_output="$("$venv_python" "$base_dir/scripts/generate.py" "$CODE_MODEL" "$host" "$tmp_fix")"
  rm -f "$tmp_fix"

  fixed_code="$(printf '%s\n' "$fix_output" | sed -n '/^```/,/^```/{/^```/d;p}')"
  [[ -z "$fixed_code" ]] && fixed_code="$fix_output"

  printf '%s\n' "$fixed_code" > "$current_file"
  echo "Fixed. Retrying..."
  (( attempt++ ))
done
