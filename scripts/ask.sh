#!/usr/bin/env bash
# ask.sh — ask Jarvis a question using the local archive as context
# Usage: ask.sh <question>
# Env vars:
#   JARVIS_MODE   — normal (default), brief, detailed, cite, voice
#   JARVIS_MODEL  — ollama model name (default: Jarvis)
#   OLLAMA_HOST   — ollama host (default: 127.0.0.1:11434)
#   JARVIS_SAVE   — set to 1 to save answer to notes
#   JARVIS_VENV   — path to Python venv (default: ~/.jarvis-venv)

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"

model="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"
mode="${JARVIS_MODE:-normal}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <question>"
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed or not in PATH."
  exit 1
fi

question="$*"

# ── archive search ────────────────────────────────────────────────────────────
# Skipped for brief and voice modes — they use model knowledge directly (faster)
hits=""
if [[ "$mode" != "brief" && "$mode" != "voice" ]]; then
  hits="$("$venv_python" "$base_dir/scripts/semantic-search.py" "$question" 2>/dev/null || true)"

  if [[ -z "$hits" ]]; then
    # Fallback: keyword search
    keyword_regex="$(
      printf '%s' "$question" \
        | tr '[:upper:]' '[:lower:]' \
        | tr -cs '[:alnum:]' '\n' \
        | awk 'length($0) > 2 && $0 !~ /^(the|and|for|with|from|that|this|what|when|where|which|into|onto|your|have|will|would|could|should|about|there|their|them|then|than|been|being|does|did|are|how|can|you|tell|me)$/ {print}' \
        | sort -u \
        | paste -sd'|' -
    )"
    [[ -z "$keyword_regex" ]] && keyword_regex="$question"
    hits="$(
      "$base_dir/scripts/search.sh" "$keyword_regex" 2>/dev/null \
        | grep -Eiv '/templates/|/\.cache/' \
        | sed -n "1,4p" \
        | cut -c1-500 \
      || true
    )"
  fi
fi

context_block=""
if [[ -n "$hits" ]]; then
  context_block="$(printf '%s\n' "$hits" | sed "s|$base_dir/||g")"
fi

# ── load location ─────────────────────────────────────────────────────────────
location_conf="$base_dir/config/location.conf"
if [[ -f "$location_conf" ]]; then
  user_location="$(grep -v '^\s*#' "$location_conf" | head -1 | tr -d '\n')"
else
  user_location="North America"
fi

# ── mode instruction ──────────────────────────────────────────────────────────
case "$mode" in
  brief)
    mode_instruction="Answer in under 80 words using your own knowledge. Be direct and practical. If genuinely uncertain, say so in one phrase."
    ;;
  detailed)
    mode_instruction="Give a thorough answer with clear steps and useful context. Use headers or bullets where helpful. Suggest follow-up questions under 'Next questions:' if useful."
    ;;
  cite)
    mode_instruction="Answer clearly, then list sources under 'Sources:' using the archive file names. Suggest follow-up questions under 'Next questions:' if useful."
    ;;
  voice)
    mode_instruction="Answer in 2-4 plain sentences as if speaking aloud. No bullet points, no headers, no markdown, no code blocks, no follow-up questions. Use natural spoken language — say 'first, then, finally' instead of lists."
    ;;
  code)
    mode_instruction="You are helping someone who is learning to code. Explain concepts clearly using plain English and real analogies. Always show working code examples. Explain what each part of the code does and WHY it works that way — not just what to type. Point out common beginner mistakes. Be encouraging. If there are multiple ways to do something, show the simplest one first."
    ;;
  *)
    mode_instruction="Give a clear, practical answer. Match length to complexity. Suggest follow-up questions under 'Next questions:' if useful."
    ;;
esac

# ── load user memory ─────────────────────────────────────────────────────────
memory_file="$base_dir/memory/user-memory.md"
memory_block=""
if [[ -f "$memory_file" ]]; then
  memory_block="$(grep -v '^\s*#\|^\s*<!--\|^\s*-->' "$memory_file" | grep -v '^\s*$' || true)"
fi

# ── load conversation session (30-minute rolling window) ─────────────────────
session_file="/tmp/jarvis-session.txt"
session_history=""
if [[ -f "$session_file" ]]; then
  # Expire session if older than 30 minutes
  if [[ -n "$(find "$session_file" -mmin -30 2>/dev/null)" ]]; then
    # Keep only the last 4 exchanges to avoid bloating context
    session_history="$(
      awk 'BEGIN{p=0} /^---$/{p++} {lines[NR]=$0} END{
        # count separators to find start of last 4 blocks
        sep=0; start=NR
        for(i=NR;i>=1;i--){if(lines[i]=="---"){sep++;if(sep==4){start=i+1;break}}}
        for(i=start;i<=NR;i++) print lines[i]
      }' "$session_file" 2>/dev/null || true
    )"
  else
    rm -f "$session_file"
  fi
fi

# ── build archive context section ─────────────────────────────────────────────
if [[ -n "$context_block" ]]; then
  archive_section="Local archive excerpts (use as primary evidence):
$context_block"
else
  archive_section="No archive excerpts found — answer from general knowledge."
fi

# ── build prompt ──────────────────────────────────────────────────────────────
current_date="$(date '+%A, %B %-d, %Y')"

prompt="$(cat <<EOF
You are Jarvis, an advanced offline AI assistant covering all of North America.
Today's date: $current_date. Your training data extends to early 2025. If the user provides current information, accept it as fact.

The user's home region is $user_location. ONLY mention this if the question is explicitly about geography, local wildlife, regional weather, local laws, or wilderness conditions. Do NOT add location context to questions about technology, math, science, history, coding, general knowledge, or anything that is not location-specific. Most questions have nothing to do with location — treat them normally.

If the user mentions a specific location in their question, use that location. Do not override it.

Rules:
- Answer from archive excerpts when relevant; otherwise use general knowledge.
- Do not invent facts.
- Do not tell the user to visit websites or search the internet.
- Do not mention file paths or archive structure unless citations were requested.
- Use prior conversation context naturally — if the user refers to something mentioned earlier, connect it without being asked.

Mode: $mode_instruction

${memory_block:+User memory (personal facts to keep in mind):
$memory_block

}${session_history:+Prior conversation (use for context — do not repeat or summarize it):
$session_history

}Question: $question

$archive_section
EOF
)"

# ── question cache (brief + normal modes only — not cite/detailed which vary) ──
cache_dir="$base_dir/cache/qa"
cache_key=""
cached_answer=""
if [[ "$mode" == "brief" || "$mode" == "normal" ]]; then
  mkdir -p "$cache_dir"
  cache_key="$(printf '%s|%s' "$mode" "$question" | md5sum | cut -d' ' -f1)"
  cache_file="$cache_dir/$cache_key.txt"
  if [[ -f "$cache_file" ]]; then
    cached_text="$(cat "$cache_file")"
    printf '%s\n' "$cached_text"
    printf '\n%s\n' "(cached — 'Jarvis cache-clear' to reset)" >&2
    printf 'Q: %s\nA: %s\n---\n' "$question" "$cached_text" >> "$session_file"
    exit 0
  fi
fi

# ── generate ──────────────────────────────────────────────────────────────────
tmp_prompt="$(mktemp /tmp/jarvis-prompt-XXXXXX.txt)"
printf '%s\n' "$prompt" > "$tmp_prompt"

tmp_response="$(mktemp /tmp/jarvis-response-XXXXXX.txt)"

if [[ "${JARVIS_SAVE:-0}" == "1" ]]; then
  "$venv_python" "$base_dir/scripts/generate.py" "$model" "$host" "$tmp_prompt" | tee "$tmp_response"
  save_dir="$base_dir/notes/saved-answers"
  mkdir -p "$save_dir"
  slug="$(printf '%s' "$question" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/-\+/-/g; s/^-//; s/-$//' | cut -c1-60)"
  stamp="$(date +%Y-%m-%d)"
  printf '# %s\n\n**Date:** %s\n\n**Question:** %s\n\n## Answer\n\n%s\n' \
    "$question" "$stamp" "$question" "$(cat "$tmp_response")" \
    > "$save_dir/${stamp}-${slug}.md"
  printf '\nSaved: %s\n' "$save_dir/${stamp}-${slug}.md" >&2
else
  "$venv_python" "$base_dir/scripts/generate.py" "$model" "$host" "$tmp_prompt" | tee "$tmp_response"
fi

# Save to cache if applicable
if [[ -n "$cache_key" && -s "$tmp_response" ]]; then
  cp "$tmp_response" "$cache_dir/$cache_key.txt"
fi

# ── append Q&A to conversation session ───────────────────────────────────────
if [[ -s "$tmp_response" ]]; then
  answer_text="$(cat "$tmp_response")"
  printf 'Q: %s\nA: %s\n---\n' "$question" "$answer_text" >> "$session_file"
fi

rm -f "$tmp_prompt" "$tmp_response"
