#!/usr/bin/env python3
"""funthink.py — fun creative thinking modes for Jarvis brainstorm menu"""
import sys, os, subprocess, tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
model           = os.environ.get("JARVIS_MODEL", "Jarvis")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

mode  = sys.argv[1] if len(sys.argv) > 1 else ""
topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

MODES = {
    "shower":    ("🚿  Shower Thoughts",    False),
    "whatif":    ("🤔  What If...",          True),
    "devil":     ("😈  Devil's Advocate",    True),
    "conspiracy":("🕵️   Conspiracy Generator",True),
    "invent":    ("🎲  Random Invention",    True),
    "opinion":   ("🌶️   Unpopular Opinion",  True),
    "fortune":   ("🔮  Fortune Teller",      False),
}

if mode not in MODES:
    print(f"Usage: Jarvis {mode} [topic]")
    sys.exit(1)

label, needs_topic = MODES[mode]

if needs_topic and not topic:
    try:
        topic = input(f"  {YELLOW}Topic: {RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
    if not topic:
        sys.exit(0)

# ── Build prompt per mode ─────────────────────────────────────────────────────

if mode == "shower":
    prompt = (
        "Generate 5 shower thoughts — the kind of random, absurd observations that "
        "pop into your head in the shower and make you go 'huh, actually...' "
        "They should be genuinely thought-provoking, weird, or oddly philosophical. "
        "Mix scales (cosmic to mundane), be specific, avoid clichés. "
        "Format: numbered list, one thought per item. No preamble."
    )

elif mode == "whatif":
    prompt = (
        f"Wild hypothetical premise: {topic}\n\n"
        "Take this completely seriously and explore it as if it were real. Cover:\n"
        "1. Immediate consequences (first 24 hours)\n"
        "2. Second-order effects (weeks/months later)\n"
        "3. How society eventually adapts\n"
        "4. One completely unexpected implication nobody would think of\n\n"
        "Be creative, specific, and fully commit to the premise. 4 short sections."
    )

elif mode == "devil":
    prompt = (
        f"Position to argue against: {topic}\n\n"
        "Argue the complete opposite as convincingly as possible. "
        "Do not hedge, do not agree at the end, do not acknowledge both sides. "
        "Commit fully. Make the strongest possible case for the opposing view. "
        "Be persuasive, sharp, and direct. 3-4 paragraphs."
    )

elif mode == "conspiracy":
    prompt = (
        f"Generate a ridiculous but internally consistent conspiracy theory about: {topic}\n\n"
        "Include:\n"
        "- Who's behind it and what they're hiding\n"
        "- The 'smoking gun' evidence\n"
        "- Why the mainstream narrative is wrong\n"
        "- Why it hasn't been exposed yet\n\n"
        "Make it absurd but internally logical. Commit to the bit. Have fun."
    )

elif mode == "invent":
    prompt = (
        f"Combine these two unrelated things into a product: {topic}\n\n"
        "Invent something that genuinely merges them. Include:\n"
        "- Product name and tagline\n"
        "- How it works\n"
        "- Who buys it and why\n"
        "- The problem it solves (even if the problem is absurd)\n"
        "- One unexpected use case\n\n"
        "Be specific, creative, and commit to the invention."
    )

elif mode == "opinion":
    prompt = (
        f"Topic: {topic}\n\n"
        "Give a genuinely spicy, unpopular opinion on this topic. "
        "State it confidently in one sentence, then defend it with 3 strong arguments. "
        "Don't hedge, don't apologize, don't acknowledge the other side until the very end "
        "— and even then, dismiss it briefly. Act like you've held this for years."
    )

elif mode == "fortune":
    prompt = (
        "You are a cryptic fortune teller. Give a fortune that sounds profound and "
        "eerily specific but is actually gloriously vague. Use mystical language — "
        "reference 'the stars aligning', 'a journey not yet begun', 'someone who knew you before'. "
        "Make it feel personal and slightly ominous. End with a single-line warning. "
        "One paragraph. Pure atmosphere. No topic."
    )

# ── Run ───────────────────────────────────────────────────────────────────────

tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-fun-", delete=False)
tmp.write(prompt)
tmp.close()

print()
print(f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
if topic:
    print(f"  {label}  {DIM}|  {topic[:45]}{RESET}")
else:
    print(f"  {label}")
print(f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
print()

subprocess.run([sys.executable, generate_script, model, host, tmp.name])
print()
os.unlink(tmp.name)
