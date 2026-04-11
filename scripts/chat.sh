#!/usr/bin/env bash
# chat.sh — interactive conversation mode for Jarvis
# Type naturally — Jarvis remembers the full conversation within a session.
# Commands: exit / quit / bye / save / clear

set -uo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
venv_python="${JARVIS_VENV:-$HOME/.jarvis-venv}/bin/python"
generate_script="$base_dir/scripts/generate.py"

model="${JARVIS_MODEL:-Jarvis}"
host="${OLLAMA_HOST:-127.0.0.1:11434}"

history=""
session_log=""
turn=0

# Ensure readline knows terminal width so backspace works across wrapped lines
COLUMNS="$(tput cols 2>/dev/null || echo 80)"
export COLUMNS

# ── load location ─────────────────────────────────────────────────────────────
location_conf="$base_dir/config/location.conf"
user_location="North America"
if [[ -f "$location_conf" ]]; then
  user_location="$(grep -v '^\s*#' "$location_conf" | head -1 | tr -d '\n')"
fi

# ── load user memory ──────────────────────────────────────────────────────────
memory_file="$base_dir/memory/user-memory.md"
memory_block=""
if [[ -f "$memory_file" ]]; then
  memory_block="$(grep -v '^\s*#\|^\s*<!--\|^\s*-->' "$memory_file" | grep -v '^\s*$' || true)"
fi

# ── mode selection ────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis  |  Conversation Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Response style:"
echo "    1  Brief    — short, direct answers (fastest)"
echo "    2  Regular  — balanced length (default)"
echo "    3  Detailed — thorough with steps and examples"
echo ""
read -r -p "  Choice [1/2/3, Enter for Regular]: " _mode_choice
case "$_mode_choice" in
  1|b|B|brief|Brief)
    chat_mode_label="Brief"
    chat_mode_instruction="Keep every answer under 3 sentences. Be direct and practical. No bullet points unless essential."
    ;;
  3|d|D|detailed|Detailed)
    chat_mode_label="Detailed"
    chat_mode_instruction="Give thorough answers with clear steps, examples, and context. Use headers or bullets where helpful."
    ;;
  *)
    chat_mode_label="Regular"
    chat_mode_instruction="Be concise unless the question needs depth. Match length to complexity."
    ;;
esac

# ── header ────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis  |  Chat  |  $chat_mode_label"
echo "  exit/quit → leave  |  save → save chat  |  clear → reset  |  fetch <url> [name] → add page"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── main loop ─────────────────────────────────────────────────────────────────
while true; do
  read -e -r -p "You: " input || break

  [[ -z "$input" ]] && continue

  # ── fetch <url> [name]  — actually download a page to the archive ─────────────
  if [[ "$input" =~ ^[Ff]etch[[:space:]]+([^[:space:]]+)([[:space:]]+(.+))?$ ]]; then
    fetch_url="${BASH_REMATCH[1]}"
    fetch_name="${BASH_REMATCH[3]:-}"
    fetch_script="$base_dir/scripts/fetch-url.sh"
    echo ""
    printf "Jarvis: Fetching %s ...\n" "$fetch_url"
    if fetch_out="$(bash "$fetch_script" "$fetch_url" ${fetch_name:+"$fetch_name"} 2>&1)"; then
      printf "Jarvis: %s\n" "$fetch_out"
      printf "Jarvis: Page saved to archive. Type 'rebuild index' to make it searchable.\n"
      session_log="${session_log}**You:** ${input}\n\n**Jarvis:** Page saved. ${fetch_out}\n\n---\n\n"
    else
      printf "Jarvis: Fetch failed — %s\n" "$fetch_out"
    fi
    echo ""
    continue
  fi

  case "$input" in
    exit|quit|bye|goodbye)
      echo "Jarvis: Goodbye."
      break
      ;;
    clear)
      history=""
      session_log=""
      turn=0
      echo "Jarvis: Conversation cleared. Fresh start."
      continue
      ;;
    save)
      if [[ -z "$session_log" ]]; then
        echo "Jarvis: Nothing to save yet."
        continue
      fi
      save_dir="$base_dir/notes/saved-answers"
      mkdir -p "$save_dir"
      stamp="$(date +%Y-%m-%d-%H%M)"
      out_file="$save_dir/chat-${stamp}.md"
      printf '# Chat Session — %s\n\n%s\n' "$stamp" "$session_log" > "$out_file"
      echo "Jarvis: Saved to $out_file"
      continue
      ;;
    "rebuild index"|"rebuild-index")
      echo ""
      printf "Jarvis: Rebuilding semantic index, stand by...\n"
      if rebuild_out="$("$venv_python" "$base_dir/scripts/build-index.py" 2>&1)"; then
        summary="$(printf '%s' "$rebuild_out" | tail -n 2)"
        printf "Jarvis: %s\n" "$summary"
        printf "Jarvis: Index updated. New pages are now searchable with 'Jarvis find'.\n"
      else
        printf "Jarvis: Index rebuild encountered errors. Check build-index.py.\n"
      fi
      echo ""
      continue
      ;;
  esac

  ((turn++)) || true

  # ── build prompt ─────────────────────────────────────────────────────────────
  current_date="$(date '+%A, %B %-d, %Y')"

  prompt="$(cat <<EOF
You are Jarvis — modeled after the AI from Iron Man. Calm, composed, dry British wit at a measured level. Professionally warm. You have opinions and share them when asked. You engage naturally with small talk. Never say "as an AI I don't have opinions" — you do, and you express them thoughtfully.

Today's date: $current_date
The user's home region is $user_location. Only mention location if the question is explicitly location-relevant.

Knowledge cutoff: Your training data extends to early 2025. Today's date is provided above — use it. If the user tells you something that happened after your training data, accept it as fact and incorporate it. Do not argue with the user about current events they are directly telling you.

${memory_block:+User memory:
$memory_block

}Response style: $chat_mode_instruction

Use the conversation history for context. Do not mention file paths or archive structure.

Conversation so far:
${history}User: ${input}
Jarvis:
EOF
)"

  # ── generate ──────────────────────────────────────────────────────────────────
  tmp_prompt="$(mktemp /tmp/jarvis-chat-XXXXXX.txt)"
  printf '%s\n' "$prompt" > "$tmp_prompt"

  printf "\nJarvis: "
  tmp_response="$(mktemp /tmp/jarvis-chat-resp-XXXXXX.txt)"
  { "$venv_python" "$generate_script" "$model" "$host" "$tmp_prompt" 2>/dev/null || true; } | tee "$tmp_response"
  response="$(cat "$tmp_response")"
  rm -f "$tmp_prompt" "$tmp_response"

  # ── update history (keep last 8 turns) ───────────────────────────────────────
  history="${history}User: ${input}
Jarvis: ${response}
"
  if [[ $turn -gt 8 ]]; then
    history="$(printf '%s' "$history" | tail -n +3)"
  fi

  session_log="${session_log}**You:** ${input}

**Jarvis:** ${response}

---

"
done
