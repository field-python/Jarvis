#!/usr/bin/env python3
"""
legal.py — Jarvis legal analysis: case outcome predictions, rights questions,
           law lookups, and legal scenario breakdowns.

Usage:
  Jarvis legal "I was arrested without a warrant, what are my rights?"
  Jarvis legal analyze
  Jarvis legal rights
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")
search_script   = str(base_dir / "scripts" / "search.py")

model = os.environ.get("JARVIS_MODEL", "Jarvis")
host  = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

now          = datetime.now()
current_date = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

DISCLAIMER = (
    f"{DIM}  ─────────────────────────────────────────────────────────\n"
    f"  NOTE: Jarvis is not a lawyer. This is educational analysis\n"
    f"  based on general legal principles and case precedent. For\n"
    f"  real legal matters, consult a licensed attorney.\n"
    f"  ─────────────────────────────────────────────────────────{RESET}"
)

LEGAL_SYSTEM_PROMPT = """You are Jarvis, an AI assistant with deep knowledge of US law, legal history, constitutional law, criminal procedure, civil law, maritime law, corporate law, and landmark court cases. Today is {date}.

You have studied:
- Black's Law Dictionary (all editions)
- The US Constitution and all amendments
- The Magna Carta and foundational legal documents
- Hundreds of landmark Supreme Court cases
- Criminal defense strategies and legal technicalities
- Real case outcomes and why verdicts went the way they did

When analyzing a legal scenario:
1. Identify the key legal issues at stake
2. Cite relevant laws, amendments, or case precedents
3. Consider arguments for BOTH sides
4. Give an educated prediction on likely outcome with your reasoning
5. Mention any legal technicalities or defenses that could apply
6. Note what jurisdiction matters (federal vs. state)

Be direct and specific. Name real cases. Use actual legal terminology and explain it plainly."""


def hr(width=60):
    print(f"{CYAN}{'━' * width}{RESET}")


def run_analysis(scenario):
    """Analyze a legal scenario and predict outcome."""
    hr()
    print(f"{BOLD}{CYAN}  Jarvis Legal Analysis{RESET}")
    hr()
    print()
    print(DISCLAIMER)
    print()

    system = LEGAL_SYSTEM_PROMPT.format(date=current_date)

    prompt = (
        f"{system}\n\n"
        f"LEGAL SCENARIO:\n{scenario}\n\n"
        f"Provide a thorough legal analysis. Include:\n"
        f"- What laws/rights are relevant\n"
        f"- Strongest arguments for the person in question\n"
        f"- Strongest arguments against them\n"
        f"- Similar landmark cases or precedents\n"
        f"- Likely outcome prediction with reasoning\n"
        f"- Any legal technicalities or loopholes that apply\n"
        f"- Practical next steps if this were real"
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-legal-", delete=False
    )
    tmp.write(prompt)
    tmp.close()

    subprocess.run([sys.executable, generate_script, model, host, tmp.name])
    os.unlink(tmp.name)

    print()
    hr()


def explain_rights():
    """Explain key constitutional rights in plain language."""
    hr()
    print(f"{BOLD}{CYAN}  Constitutional Rights — Plain Language{RESET}")
    hr()
    print()

    prompt = (
        f"{LEGAL_SYSTEM_PROMPT.format(date=current_date)}\n\n"
        f"Give a plain-language breakdown of the most important rights "
        f"every American should know:\n"
        f"- First Amendment (speech, religion, press, assembly)\n"
        f"- Second Amendment (right to bear arms)\n"
        f"- Fourth Amendment (search and seizure, probable cause)\n"
        f"- Fifth Amendment (self-incrimination, double jeopardy, due process)\n"
        f"- Sixth Amendment (right to trial, attorney, speedy trial)\n"
        f"- Eighth Amendment (cruel and unusual punishment, bail)\n"
        f"- Fourteenth Amendment (equal protection, due process)\n\n"
        f"For each, include: what it means in plain English, a real case where "
        f"it mattered, and common misconceptions."
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-rights-", delete=False
    )
    tmp.write(prompt)
    tmp.close()

    subprocess.run([sys.executable, generate_script, model, host, tmp.name])
    os.unlink(tmp.name)
    print()
    hr()


def interactive_mode():
    """Interactive legal Q&A loop."""
    hr()
    print(f"{BOLD}{CYAN}  Jarvis Legal Assistant{RESET}")
    hr()
    print()
    print(DISCLAIMER)
    print()
    print(f"  {DIM}Describe a legal scenario, ask about your rights, or ask about a law.")
    print(f"  Jarvis will analyze it and predict likely outcomes based on precedent.")
    print(f"  Type 'rights' for a constitutional rights overview. ESC or Enter to exit.{RESET}")
    print()

    while True:
        try:
            q = input(f"  {YELLOW}Legal question (ESC/Enter to exit): {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not q:
            return

        if q.lower() in ("rights", "my rights", "constitution"):
            explain_rights()
            continue

        print()
        run_analysis(q)
        print()


# ── entry point ───────────────────────────────────────────────────────────────
args = sys.argv[1:]

if not args:
    interactive_mode()

elif args[0].lower() in ("rights", "constitution", "amendments"):
    explain_rights()

elif args[0].lower() in ("analyze", "analysis", "case"):
    if len(args) > 1:
        run_analysis(" ".join(args[1:]))
    else:
        interactive_mode()

else:
    # Treat all args as the scenario
    run_analysis(" ".join(args))
