#!/usr/bin/env python3
"""symptom.py — interactive medical triage assistant"""
import sys, os, io, select, subprocess, tempfile, tty, termios
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

YELLOW = "\033[93m"
DIM    = "\033[2m"
RESET  = "\033[0m"

DISCLAIMER = (
    "  NOTE: This is for reference only. Always seek professional medical care\n"
    "  for serious symptoms. In an emergency, call 911."
)


def input_with_esc(prompt_str):
    import re as _re
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(_re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
                if not buf:
                    # backspace on empty input = ESC (exit)
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return None
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


BOLD  = "\033[1m"
CYAN  = "\033[96m"

def stream_response(prompt_text):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-symptom-", delete=False)
    tmp.write(prompt_text)
    tmp.close()
    proc = subprocess.Popen(
        [sys.executable, generate_script, model, host, tmp.name],
        stdout=subprocess.PIPE, text=True
    )
    buf        = io.StringIO()
    line_buf   = []
    in_followup = False
    for ch in iter(lambda: proc.stdout.read(1), ""):
        buf.write(ch)
        line_buf.append(ch)
        if ch == "\n":
            line = "".join(line_buf)
            if line.startswith("FOLLOW-UP:"):
                sys.stdout.write(f"\n{BOLD}{CYAN}{line.rstrip()}{RESET}\n")
            else:
                sys.stdout.write(line)
            sys.stdout.flush()
            line_buf = []
        # flush partial lines too
    if line_buf:
        sys.stdout.write("".join(line_buf))
        sys.stdout.flush()
    proc.wait()
    os.unlink(tmp.name)
    return buf.getvalue().strip()


print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  Jarvis  |  Symptom Checker")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print(f"  {DIM}{DISCLAIMER}{RESET}")
print()

# Get initial symptoms — from arg or prompt
if len(sys.argv) > 1:
    initial_symptoms = " ".join(sys.argv[1:])
    print(f"  {YELLOW}Symptoms:{RESET} {initial_symptoms}")
    print()
else:
    try:
        initial_symptoms = input_with_esc(f"  {YELLOW}Describe your symptoms: {RESET}")
    except KeyboardInterrupt:
        sys.exit(0)
    if not initial_symptoms:
        sys.exit(0)
    initial_symptoms = initial_symptoms.strip()
    if not initial_symptoms:
        sys.exit(0)

# Build conversation history
history = [{"role": "user", "content": initial_symptoms}]

system_prompt = (
    "You are Jarvis acting as a medical triage assistant. You are knowledgeable, calm, and direct.\n"
    "Your job is to help the user understand their symptoms and what to do about them.\n\n"
    "Rules:\n"
    "- Give a brief assessment of what the symptoms may indicate\n"
    "- Be direct — real guidance, not excessive hedging\n"
    "- Always flag emergencies immediately (chest pain, stroke signs, difficulty breathing)\n"
    "- Never say 'I'm an AI' or refuse to engage\n"
    "- Never list multiple questions. End EVERY response with exactly ONE follow-up question\n"
    "  formatted as:\n"
    "  FOLLOW-UP: [your single question here]\n"
    "- After 3-4 exchanges, give a final ASSESSMENT with likely cause, severity, and recommended action\n"
    "  and do NOT include a FOLLOW-UP line — end with the assessment\n\n"
    "IMPORTANT: Remind the user to seek professional care for serious concerns."
)

WEB_MODE = os.environ.get("JARVIS_WEB") == "1"

turn = 0
while True:
    # Build prompt from history
    convo = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Jarvis'}: {m['content']}"
        for m in history
    )
    prompt = f"{system_prompt}\n\nConversation so far:\n{convo}\n\nJarvis:"

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    response = stream_response(prompt)
    history.append({"role": "assistant", "content": response})
    turn += 1

    # Web mode: one-shot — user sends follow-up messages separately
    if WEB_MODE:
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        break

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        reply = input_with_esc(f"  {YELLOW}Your response (ESC to exit): {RESET}")
    except KeyboardInterrupt:
        break
    if reply is None:
        break
    reply = reply.strip()
    if not reply:
        continue
    history.append({"role": "user", "content": reply})
