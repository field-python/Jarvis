#!/usr/bin/env python3
"""speech.py — AI speech writer. Generates full speeches for any occasion."""
import sys
import os
import re
import readline
import subprocess
import tempfile
import tty
import termios
import select as _sel
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
speeches_dir    = base_dir / "notes" / "speeches"

CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

TONES = [
    ("Formal / Professional",    "formal and professional — polished, authoritative, structured"),
    ("Conversational / Warm",    "conversational and warm — approachable, natural, like talking to a friend"),
    ("Humorous / Light",         "humorous and light — wit, charm, a few well-placed laughs"),
    ("Inspirational / Motivating","inspirational and motivating — energetic, forward-looking, emotionally resonant"),
    ("Solemn / Ceremonial",      "solemn and ceremonial — respectful, dignified, weight of the occasion"),
]

# Words per minute at natural speaking pace
LENGTHS = [
    ("Short  (~3 min)",  400),
    ("Medium (~7 min)",  900),
    ("Long   (~15 min)", 2000),
]


def input_with_esc(prompt_str):
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = _sel.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                text = "".join(buf)
                if text.strip():
                    readline.add_history(text)
                return text
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf.pop()
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = total // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
                    sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def pick_option(prompt_label, options):
    """Display numbered options, return selected index."""
    print(f"  {BOLD}{prompt_label}{RESET}")
    print()
    for i, (label, _) in enumerate(options, 1):
        print(f"    {YELLOW}{i}{RESET}  {label}")
    print()
    while True:
        raw = input_with_esc(f"  Choice [1-{len(options)}]: ")
        if raw is None:
            return None
        raw = raw.strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        if not raw and len(options) >= 2:
            return 1   # default to second option (medium/warm)


def hr():
    print(f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")


def main():
    print()
    hr()
    print(f"  {BOLD}✍️  Jarvis Speech Writer{RESET}")
    hr()
    print()

    # ── Step 1: occasion / audience description ───────────────────────────────
    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])
        print(f"  {DIM}Occasion: {description}{RESET}")
        print()
    else:
        print(f"  Describe your speech — who's the audience and what's the occasion.")
        print(f"  {DIM}Examples: 'wedding toast for my best friend'")
        print(f"            'keynote to 500 college students about aerospace'")
        print(f"            'retirement speech for my boss of 10 years'{RESET}")
        print()
        description = input_with_esc(f"  {YELLOW}Occasion / audience: {RESET}")
        if not description or not description.strip():
            print("  Nothing entered. Exiting.")
            return
        description = description.strip()
        print()

    # ── Step 2: key points (optional) ────────────────────────────────────────
    print(f"  {DIM}Any specific points, stories, or themes to include? (Enter to skip){RESET}")
    key_points = input_with_esc(f"  {YELLOW}Key points (optional): {RESET}")
    if key_points is None:
        return
    key_points = key_points.strip()
    print()

    # ── Step 3: tone ─────────────────────────────────────────────────────────
    tone_idx = pick_option("Tone:", TONES)
    if tone_idx is None:
        return
    tone_label, tone_desc = TONES[tone_idx]
    print()

    # ── Step 4: length ────────────────────────────────────────────────────────
    length_idx = pick_option("Length:", LENGTHS)
    if length_idx is None:
        return
    length_label, word_count = LENGTHS[length_idx]
    print()

    # ── Generate ──────────────────────────────────────────────────────────────
    hr()
    print(f"  {DIM}Writing speech... (this may take a minute){RESET}")
    hr()
    print()

    key_section = f"\nKey points to include:\n{key_points}\n" if key_points else ""

    prompt = (
        f"You are a professional speechwriter. Write a complete, ready-to-deliver speech.\n\n"
        f"Occasion / audience: {description}\n"
        f"{key_section}\n"
        f"Tone: {tone_desc}\n"
        f"Target length: approximately {word_count} words.\n\n"
        f"Structure the speech with:\n"
        f"- A strong opening hook that grabs attention immediately\n"
        f"- A brief self-introduction if appropriate for the occasion\n"
        f"- 2-4 well-developed main points or sections\n"
        f"- At least one specific story, analogy, or vivid example\n"
        f"- A memorable closing that gives the audience something to take away\n\n"
        f"Format rules:\n"
        f"- Write the full speech as it would be spoken aloud — natural phrasing, not bullet points\n"
        f"- Use section headers (like [OPENING], [MAIN], [CLOSING]) so the speaker can navigate easily\n"
        f"- Include natural pause cues like (pause) where they add impact\n"
        f"- Match vocabulary and complexity to the audience\n"
        f"- Make it feel personal and specific — not generic or templated\n"
        f"- Do not include stage directions beyond (pause) — the speaker knows how to stand\n\n"
        f"Write the full speech now. Start directly with the opening line."
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-speech-", delete=False
    )
    tmp.write(prompt)
    tmp.close()

    result = subprocess.run(
        [sys.executable, generate_script, model, host, tmp.name],
        capture_output=True, text=True
    )
    os.unlink(tmp.name)
    speech_text = result.stdout.strip()

    if not speech_text:
        print("  Speech generation failed. Try again.")
        return

    # ── Display ───────────────────────────────────────────────────────────────
    print()
    hr()
    print(f"  {BOLD}Your Speech{RESET}  {DIM}| {description} | {tone_label} | {length_label}{RESET}")
    hr()
    print()

    # Color section headers
    for line in speech_text.splitlines():
        stripped = line.strip()
        if re.match(r'^\[.+\]$', stripped):
            print(f"\n{BOLD}{CYAN}{stripped}{RESET}")
        elif stripped.startswith("(") and stripped.endswith(")"):
            print(f"  {DIM}{stripped}{RESET}")
        else:
            print(f"  {line}")
    print()
    hr()

    # Word count
    actual_words = len(speech_text.split())
    est_minutes  = round(actual_words / 130)
    print(f"  {DIM}~{actual_words} words  |  ~{est_minutes} min at speaking pace{RESET}")
    print()

    # ── Save option ───────────────────────────────────────────────────────────
    save = input_with_esc(f"  {YELLOW}Save this speech? [y/N]: {RESET}")
    if save and save.strip().lower() in ("y", "yes"):
        speeches_dir.mkdir(parents=True, exist_ok=True)
        stamp    = datetime.now().strftime("%Y-%m-%d-%H%M")
        slug     = re.sub(r'[^a-z0-9]+', '-', description.lower())[:40].strip('-')
        out_file = speeches_dir / f"{stamp}-{slug}.md"
        header   = (
            f"# Speech: {description}\n\n"
            f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n"
            f"**Tone:** {tone_label}\n"
            f"**Length:** {length_label} (~{actual_words} words)\n\n"
            f"---\n\n"
        )
        out_file.write_text(header + speech_text + "\n", encoding="utf-8")
        print(f"\n  {GREEN}Saved to:{RESET} {out_file}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
