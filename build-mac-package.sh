#!/usr/bin/env bash
# build-mac-package.sh — Build the Jarvis Mac email package
# Run from: /media/field_python/ARCHIVE/jarvis/
# Output:   ~/Desktop/jarvis-mac.zip

set -e

JARVIS_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="/tmp/jarvis-mac-build"
ZIP_OUT="$HOME/Desktop/jarvis-mac.zip"

echo "Building Jarvis Mac package..."
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/jarvis-mac/scripts"
mkdir -p "$OUT_DIR/jarvis-mac/config"
mkdir -p "$OUT_DIR/jarvis-mac/notes/personal-notes"

# ── Core launcher + setup ─────────────────────────────────────────────────────
cp "$JARVIS_DIR/mac-setup.sh"   "$OUT_DIR/jarvis-mac/mac-setup.sh"
cp "$JARVIS_DIR/mac-jarvis.py"  "$OUT_DIR/jarvis-mac/mac-jarvis.py"

# ── AI engine ─────────────────────────────────────────────────────────────────
cp "$JARVIS_DIR/scripts/generate.py"    "$OUT_DIR/jarvis-mac/scripts/"

# ── Core features ─────────────────────────────────────────────────────────────
cp "$JARVIS_DIR/scripts/ask.py"         "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/chat.py"        "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/news.py"        "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/weather.py"     "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/web-search.py"  "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/timer.py"       "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/note.py"        "$OUT_DIR/jarvis-mac/scripts/"
cp "$JARVIS_DIR/scripts/daily.py"       "$OUT_DIR/jarvis-mac/scripts/"

# ── Make setup executable ─────────────────────────────────────────────────────
chmod +x "$OUT_DIR/jarvis-mac/mac-setup.sh"

# ── Write README ──────────────────────────────────────────────────────────────
cat > "$OUT_DIR/jarvis-mac/README.txt" << 'README'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Jarvis — AI Assistant for Mac
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE YOU START — get a free API key:
  1. Go to: console.groq.com
  2. Sign up (free)
  3. Click "API Keys" → "Create API Key"
  4. Copy the key (starts with "gsk_...")

INSTALL:
  1. Unzip jarvis-mac.zip  (double-click it)
  2. Open Terminal
  3. Drag the "jarvis-mac" folder into Terminal to get its path
  4. Type:  bash setup.sh  and press Enter
  5. Paste your Groq key when asked
  6. Type: source ~/.zshrc

COMMANDS:
  Jarvis "any question"        Ask anything
  Jarvis brief "question"      Short answer
  Jarvis chat                  Have a conversation
  Jarvis news                  Today's headlines
  Jarvis weather               Current weather
  Jarvis weather "New York"    Weather anywhere
  Jarvis daily                 Morning briefing
  Jarvis timer 10m             Set a timer
  Jarvis note "text"           Save a note
  Jarvis notes                 View today's notes
  Jarvis help                  Full command list

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
README

# ── Create zip ────────────────────────────────────────────────────────────────
cd "$OUT_DIR"
zip -r "$ZIP_OUT" jarvis-mac/ -x "*.pyc" -x "__pycache__/*" -x ".DS_Store" > /dev/null

SIZE=$(du -sh "$ZIP_OUT" | cut -f1)
echo ""
echo "✓ Package built: $ZIP_OUT  ($SIZE)"
echo ""
echo "Contents:"
cd "$OUT_DIR/jarvis-mac"
find . -type f | sort | sed 's/^/  /'
echo ""
