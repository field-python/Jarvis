#!/usr/bin/env bash
# setup.sh — set up Jarvis on a new machine (Linux or macOS)
# Run this once after plugging in the ARCHIVE drive.
# Usage: bash /media/YOUR_USERNAME/ARCHIVE/jarvis/setup.sh   (Linux)
#    or: bash /Volumes/ARCHIVE/jarvis/setup.sh               (Mac)

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="$HOME/.jarvis-venv"
LAUNCHER="$HOME/Jarvis"
MODELFILE="$SCRIPT_DIR/Jarvis.Modelfile"

# ── detect OS ─────────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="mac"   ;;
  Linux)  PLATFORM="linux" ;;
  *)      PLATFORM="linux" ;;  # fallback
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jarvis Setup  |  $OS"
echo "  Drive: $SCRIPT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Python venv ────────────────────────────────────────────────────────────
echo "[1/4] Creating Python environment at $VENV_DIR..."
if [[ -d "$VENV_DIR" ]]; then
  echo "  already exists, skipping"
else
  python3 -m venv "$VENV_DIR"
  echo "  created"
fi

echo "[1/4] Installing Python packages..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "  done"

# ── 2. Ollama model ───────────────────────────────────────────────────────────
echo "[2/4] Checking Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  echo "  Ollama not found."
  echo ""
  if [[ "$PLATFORM" == "mac" ]]; then
    echo "  Install it with:"
    echo "    brew install ollama"
    echo "  Or download from: https://ollama.com/download/mac"
  else
    echo "  Install it with:"
    echo "    curl -fsSL https://ollama.com/install.sh | sh"
  fi
  echo ""
  echo "  Then re-run this script."
  exit 1
fi
echo "  found: $(ollama --version 2>/dev/null || echo 'ollama')"

if ollama list 2>/dev/null | grep -q "^Jarvis"; then
  echo "  Jarvis model already exists, skipping"
else
  echo "  Building Jarvis model from Modelfile..."
  ollama create Jarvis -f "$MODELFILE"
  echo "  done"
fi

# ── 3. Launcher stub ──────────────────────────────────────────────────────────
# The full launcher lives on the drive at ARCHIVE/jarvis/Jarvis.
# We write a tiny stub to ~/Jarvis that finds the drive and execs it.
echo "[3/4] Writing launcher stub to $LAUNCHER..."
cat > "$LAUNCHER" <<'LAUNCHEREOF'
#!/usr/bin/env bash
# Jarvis — finds your ARCHIVE drive and runs Jarvis from it.
# The full launcher lives at: ARCHIVE/jarvis/Jarvis
# To update Jarvis, edit that file — this stub never needs to change.

for _mount in /media/*/ARCHIVE /mnt/ARCHIVE /run/media/*/ARCHIVE /Volumes/ARCHIVE; do
  if [[ -x "$_mount/jarvis/Jarvis" ]]; then
    exec bash "$_mount/jarvis/Jarvis" "$@"
  fi
done

echo "Jarvis: ARCHIVE drive not found. Plug it in and try again."
exit 1
LAUNCHEREOF

chmod +x "$LAUNCHER"
echo "  done"

# ── 4. Shell alias ────────────────────────────────────────────────────────────
echo "[4/4] Adding alias to shell config..."

# Detect shell config file
if [[ "$PLATFORM" == "mac" ]]; then
  SHELL_RC="$HOME/.zshrc"
  [[ -f "$HOME/.bash_profile" && ! -f "$HOME/.zshrc" ]] && SHELL_RC="$HOME/.bash_profile"
else
  SHELL_RC="$HOME/.bashrc"
fi

if grep -q "alias Jarvis=" "$SHELL_RC" 2>/dev/null; then
  echo "  alias already exists in $SHELL_RC, skipping"
else
  echo "" >> "$SHELL_RC"
  echo "# Jarvis AI assistant" >> "$SHELL_RC"
  echo "alias Jarvis='$LAUNCHER'" >> "$SHELL_RC"
  echo "  added to $SHELL_RC"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Reload your shell:"
if [[ "$PLATFORM" == "mac" ]]; then
  echo "       source ~/.zshrc"
else
  echo "       source ~/.bashrc"
fi
echo ""
echo "  2. Start Jarvis:"
echo "       Jarvis"
echo ""
echo "  Jarvis will walk you through first-time setup."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
