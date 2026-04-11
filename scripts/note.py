#!/usr/bin/env python3
"""note.py — save a quick note to the Jarvis archive"""
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
notes_dir  = base_dir / "notes" / "personal-notes"
notes_dir.mkdir(parents=True, exist_ok=True)

now        = datetime.now()
stamp      = now.strftime("%Y-%m-%d")
ts         = now.strftime("%H:%M")
daily_file = notes_dir / f"{stamp}.md"

if not daily_file.exists():
    daily_file.write_text(f"# Notes — {stamp}\n\n", encoding="utf-8")

if len(sys.argv) >= 2:
    note_text = " ".join(sys.argv[1:])
    with daily_file.open("a", encoding="utf-8") as f:
        f.write(f"**{ts}** {note_text}\n\n")
    print(f"Note saved: {daily_file}")
else:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", prefix="jarvis-note-", delete=False
    )
    tmp.write("<!-- Type your note below, save and close to save it -->\n\n")
    tmp.close()

    editor = os.environ.get("VISUAL", os.environ.get("EDITOR", "nano"))
    subprocess.run([editor, tmp.name])

    content = Path(tmp.name).read_text(encoding="utf-8")
    os.unlink(tmp.name)

    lines = [ln for ln in content.splitlines() if not ln.startswith("<!--")]
    while lines and not lines[0].strip():
        lines.pop(0)
    note_text = "\n".join(lines).strip()

    if not note_text:
        print("Empty note — nothing saved.")
        sys.exit(0)

    with daily_file.open("a", encoding="utf-8") as f:
        f.write(f"**{ts}**\n\n{note_text}\n\n")
    print(f"Note saved: {daily_file}")
