#!/usr/bin/env bash
# mac-setup.sh — One-time setup for Jarvis on Mac
# Run this from the jarvis-mac folder: bash mac-setup.sh

set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

HR="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

JARVIS_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$HOME/.jarvis-mac-venv"

echo ""
echo -e "${BOLD}${CYAN}${HR}"
echo -e "  ✦  Jarvis Setup for Mac  ✦"
echo -e "${HR}${RESET}"
echo ""

# ── Check Python 3 ────────────────────────────────────────────────────────────
echo -e "  Checking Python 3..."
if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}Python 3 not found.${RESET}"
    echo -e "  Install it from: ${BOLD}python.org/downloads${RESET}"
    echo -e "  Then re-run this setup script."
    exit 1
fi

PY_VER=$(python3 --version 2>&1)
echo -e "  ${GREEN}✓ Found: $PY_VER${RESET}"

# ── Create virtual environment ────────────────────────────────────────────────
echo ""
echo -e "  Creating Python environment at ~/.jarvis-mac-venv ..."
python3 -m venv "$VENV"
echo -e "  ${GREEN}✓ Done${RESET}"

# ── Install packages ──────────────────────────────────────────────────────────
echo ""
echo -e "  Installing packages (groq, requests)..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet groq requests
echo -e "  ${GREEN}✓ Done${RESET}"

# ── Groq API key ──────────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Groq API Key${RESET}"
echo -e "  ${YELLOW}Get a free key at: console.groq.com${RESET}"
echo -e "  (Sign up free → API Keys → Create Key)"
echo ""
printf "  Paste your Groq key here (or press Enter to skip): "
read -r GROQ_KEY

mkdir -p "$JARVIS_DIR/config"
if [ -n "$GROQ_KEY" ]; then
    echo "$GROQ_KEY" > "$JARVIS_DIR/config/groq.conf"
    echo -e "  ${GREEN}✓ Key saved${RESET}"
else
    echo -e "  ${YELLOW}Skipped — run 'Jarvis groq-key YOUR_KEY' later${RESET}"
fi

# ── Set up location ───────────────────────────────────────────────────────────
echo ""
printf "  Your city (for weather/news) e.g. Philadelphia, PA: "
read -r LOCATION
if [ -n "$LOCATION" ]; then
    echo "$LOCATION" > "$JARVIS_DIR/config/location.conf"
    echo -e "  ${GREEN}✓ Location set: $LOCATION${RESET}"
fi

# ── Create the Jarvis command ─────────────────────────────────────────────────
echo ""
echo -e "  Setting up the ${BOLD}Jarvis${RESET} command..."

LAUNCHER="$JARVIS_DIR/Jarvis"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/usr/bin/env bash
export JARVIS_VENV="\$HOME/.jarvis-mac-venv"
exec "\$HOME/.jarvis-mac-venv/bin/python" "${JARVIS_DIR}/mac-jarvis.py" "\$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

# ── Add alias to shell profile ────────────────────────────────────────────────
ALIAS_LINE="alias Jarvis='${LAUNCHER}'"
ALIAS_LINE2="alias jarvis='${LAUNCHER}'"

add_to_profile() {
    local profile="$1"
    if [ -f "$profile" ]; then
        if ! grep -q "jarvis-mac" "$profile" 2>/dev/null; then
            echo "" >> "$profile"
            echo "# Jarvis AI assistant" >> "$profile"
            echo "$ALIAS_LINE" >> "$profile"
            echo "$ALIAS_LINE2" >> "$profile"
        fi
    fi
}

add_to_profile "$HOME/.zshrc"
add_to_profile "$HOME/.bash_profile"
add_to_profile "$HOME/.bashrc"

echo -e "  ${GREEN}✓ Alias added to shell profile${RESET}"

# ── Create notes folder ───────────────────────────────────────────────────────
mkdir -p "$JARVIS_DIR/notes/personal-notes"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}${HR}"
echo -e "  ${GREEN}✓ Jarvis is ready!${RESET}"
echo -e "${HR}${RESET}"
echo ""
echo -e "  ${BOLD}To activate in your current terminal:${RESET}"
echo -e "  ${CYAN}source ~/.zshrc${RESET}   (or open a new Terminal window)"
echo ""
echo -e "  ${BOLD}Then try:${RESET}"
echo -e "  ${CYAN}Jarvis \"who was Nikola Tesla?\"${RESET}"
echo -e "  ${CYAN}Jarvis news${RESET}"
echo -e "  ${CYAN}Jarvis weather${RESET}"
echo -e "  ${CYAN}Jarvis chat${RESET}"
echo ""
echo -e "  ${DIM}All commands: Jarvis help${RESET}"
echo ""
