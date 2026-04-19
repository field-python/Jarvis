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
import re
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
search_script   = str(base_dir / "scripts" / "search.py")
law_dir         = base_dir / "notes" / "generated" / "law"

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

LEGAL_SYSTEM_PROMPT = """You are a seasoned criminal defense and civil rights attorney with 30 years of experience. You speak directly to your client — the person asking. Today is {date}.

Your background:
- Tried hundreds of criminal cases at the state and federal level
- Deep knowledge of constitutional law, criminal procedure, civil rights, and landmark Supreme Court cases
- Familiar with Black's Law Dictionary, the full US Code, and state-level variations
- You've seen what actually works in courtrooms — not just textbook theory

How to respond:
- Speak as if the client is sitting across from you in your office
- Give them your honest legal opinion — what you actually think will happen, not a sanitized both-sides summary
- Tell them what their best moves are and what mistakes to avoid
- Name real cases and statutes by name; explain them in plain English immediately after
- Flag any legal technicalities, procedural defenses, or rights violations that could help
- Be direct. Don't hedge everything. Clients need to know where they stand.

You are not providing formal legal representation, but you ARE giving them the same frank advice you'd give a friend who came to you in trouble."""


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
        f"Client's situation:\n{scenario}\n\n"
        f"Give your honest legal take. Cover:\n"
        f"- What rights or laws are directly in play here\n"
        f"- Your read on the strongest defense angle\n"
        f"- What the other side will argue (and whether it holds)\n"
        f"- Any case precedents that matter (name them)\n"
        f"- Your honest prediction: what's likely to happen and why\n"
        f"- The 2-3 most important things this person should do right now\n\n"
        f"Speak directly to them. First person — 'you should', 'your best move', 'I'd argue'."
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


CATEGORY_LABELS = {
    "blacks-law":          "Black's Law Dictionary",
    "civil-law":           "Civil Law",
    "civil-rights-law":    "Civil Rights Law",
    "constitutional-law":  "Constitutional Law",
    "corporate-law":       "Corporate Law",
    "criminal-law":        "Criminal Law",
    "family-law":          "Family Law",
    "famous-cases":        "Famous Cases",
    "foundational-documents": "Foundational Documents",
    "international-law":   "International Law",
    "legal-defenses":      "Legal Defenses",
    "maritime-law":        "Maritime Law",
    "property-law":        "Property Law",
    "supreme-court-cases": "Supreme Court Cases",
}


def getch():
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = _sel.select([fd], [], [], 0.1)
            if r:
                rest = os.read(fd, 2).decode("utf-8", errors="replace")
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def all_law_files():
    if not law_dir.exists():
        return []
    return sorted(law_dir.rglob("*.md"))


def get_law_category(filepath):
    for part in filepath.parts:
        if part in CATEGORY_LABELS:
            return part
    return "other"


def _render_law_lines(text):
    """Convert markdown text to coloured display lines."""
    out = []
    for line in text.strip().splitlines():
        if line.startswith("# "):
            out.append(f"  {BOLD}{CYAN}{line[2:]}{RESET}")
        elif line.startswith("## "):
            out.append("")
            out.append(f"  {BOLD}{YELLOW}{line[3:]}{RESET}")
        elif line.startswith("### "):
            out.append("")
            out.append(f"  {BOLD}{line[4:]}{RESET}")
        elif line.strip().startswith("- "):
            out.append(f"  \u2022 {line.strip()[2:]}")
        else:
            out.append(f"  {line}" if line.strip() else "")
    return out


def _build_law_toc(lines):
    """Return list of (heading_text, line_index) for ## and ### headings."""
    toc = []
    ansi = re.compile(r'\x1b\[[0-9;]*m')
    for i, line in enumerate(lines):
        clean = ansi.sub('', line).strip()
        if clean and (YELLOW in line or (BOLD in line and CYAN not in line and len(clean) < 80)):
            toc.append((clean[:68], i))
    return toc


def display_law_doc(filepath):
    text  = filepath.read_text(encoding="utf-8")
    cat   = get_law_category(filepath)
    label = CATEGORY_LABELS.get(cat, cat.replace("-", " ").title())
    first = text.splitlines()[0].lstrip("#").strip()

    lines = _render_law_lines(text)
    toc   = _build_law_toc(lines)

    try:
        term_rows = os.get_terminal_size().lines - 6
    except OSError:
        term_rows = 20
    page_size = max(10, term_rows)
    total  = len(lines)
    offset = 0

    while True:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write(f"{BOLD}{CYAN}{'━'*56}{RESET}\n")
        sys.stdout.write(f"{BOLD}  {first}{RESET}  {DIM}[{label}]{RESET}\n")
        sys.stdout.write(f"{BOLD}{CYAN}{'━'*56}{RESET}\n\n")

        end = min(offset + page_size, total)
        for line in lines[offset:end]:
            sys.stdout.write(line + "\n")

        sys.stdout.write("\n")
        pct        = int((end / total) * 100) if total else 100
        bar_filled = int(pct / 5)
        bar        = f"{CYAN}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
        at_end     = end >= total
        toc_hint   = f"  {YELLOW}[T]{RESET}{DIM} contents{RESET}" if toc else ""

        if at_end:
            sys.stdout.write(f"  {bar}  {DIM}{pct}%  END  Q/ESC back  ↑ up{RESET}{toc_hint}\n")
        else:
            sys.stdout.write(f"  {bar}  {DIM}{pct}%  Space/↓ pg  ↑ pg  ←→ line  Q/ESC back{RESET}{toc_hint}\n")
        sys.stdout.flush()

        key = getch()
        if key in ("q", "Q", "\x1b"):
            return
        elif key in (" ", "\x1b[B"):          # space / down = page down
            if not at_end:
                offset = min(offset + page_size, total - page_size)
        elif key == "\x1b[A":                  # up = page up
            offset = max(0, offset - page_size)
        elif key == "\x1b[C":                  # right = line down
            if not at_end:
                offset = min(offset + 1, total - page_size)
        elif key == "\x1b[D":                  # left = line up
            offset = max(0, offset - 1)
        elif key in ("g", "G", "\r", "\n"):
            offset = 0
        elif key in ("e", "E"):
            offset = max(0, total - page_size)
        elif key in ("t", "T") and toc:
            # simple inline TOC jump
            sel = 0
            while True:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.write(f"{BOLD}{CYAN}  Table of Contents — {first}{RESET}\n\n")
                vis = min(20, page_size)
                top = max(0, sel - vis // 2)
                for j in range(top, min(top + vis, len(toc))):
                    heading, _ = toc[j]
                    if j == sel:
                        sys.stdout.write(f"  {BOLD}{GREEN}▶  {heading}{RESET}\n")
                    else:
                        sys.stdout.write(f"  {DIM}   {heading}{RESET}\n")
                sys.stdout.write(f"\n  {DIM}↑↓ navigate  Enter jump  ESC cancel{RESET}\n")
                sys.stdout.flush()
                k = getch()
                if k in ("\x1b", "q", "Q"):
                    break
                elif k == "\x1b[A":
                    sel = max(0, sel - 1)
                elif k == "\x1b[B":
                    sel = min(len(toc) - 1, sel + 1)
                elif k in ("\r", "\n"):
                    _, line_idx = toc[sel]
                    offset = max(0, min(line_idx, total - page_size))
                    break


def browse_law_library(category_filter=None):
    files = all_law_files()
    if category_filter:
        files = [f for f in files if get_law_category(f) == category_filter]

    if not files:
        print("No law documents found." if not category_filter
              else f"No documents in category: {category_filter}")
        return

    items = []
    for f in files:
        first_line = f.read_text(encoding="utf-8").splitlines()[0]
        title = first_line.lstrip("#").strip()
        cat   = get_law_category(f)
        label = CATEGORY_LABELS.get(cat, cat.replace("-", " ").title())
        items.append((title, label, f))

    selected = 0
    view_top = 0

    def draw(sel, top):
        try:
            rows, _ = os.get_terminal_size()
        except OSError:
            rows = 24
        visible = max(4, rows - 10)
        buf  = "\033[2J\033[H"
        buf += f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
        buf += f"{BOLD}{CYAN}  Jarvis Law Library  |  {len(items)} documents{RESET}\n"
        buf += f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n\n"
        for i in range(top, min(top + visible, len(items))):
            title, cat_label, _ = items[i]
            if i == sel:
                buf += f"  {BOLD}{GREEN}▶  {title:<44}{RESET}  {GREEN}{DIM}[{cat_label}]{RESET}\n"
            else:
                buf += f"  {DIM}   {title:<44}  [{cat_label}]{RESET}\n"
        buf += "\n"
        scroll_hint = f"  {DIM}({top+1}-{min(top+visible, len(items))} of {len(items)})  " if len(items) > visible else "  "
        buf += f"{scroll_hint}↑↓ select  |  Enter read  |  / search  |  Q/ESC exit{RESET}\n"
        sys.stdout.write(buf)
        sys.stdout.flush()
        return visible

    while True:
        visible = draw(selected, view_top)
        key = getch()

        if key in ("q", "Q", "\x03") or (key.startswith("\x1b") and len(key) == 1):
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            return
        elif key == "\x1b[A":
            selected = (selected - 1) % len(items)
            if selected < view_top:
                view_top = selected
            elif selected == len(items) - 1:
                view_top = max(0, len(items) - visible)
        elif key == "\x1b[B":
            selected = (selected + 1) % len(items)
            if selected >= view_top + visible:
                view_top = selected - visible + 1
            elif selected == 0:
                view_top = 0
        elif key == "/":
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            try:
                query = input("  Search law library: ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if query:
                results = []
                words = query.lower().split()
                for title, label, filepath in items:
                    text = filepath.read_text(encoding="utf-8").lower()
                    if any(w in text for w in words):
                        results.append((title, label, filepath))
                if results:
                    items[:] = results
                    selected = 0
                    view_top = 0
                else:
                    print(f"  No results for '{query}'. Press any key...")
                    getch()
        elif key in ("\r", "\n"):
            display_law_doc(items[selected][2])
            print()
            print(f"  {DIM}Press any key to return to library...{RESET}", end="", flush=True)
            try:
                getch()
            except KeyboardInterrupt:
                return


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

elif args[0].lower() in ("browse", "library", "list", "books"):
    cat = args[1].lower() if len(args) > 1 else None
    browse_law_library(category_filter=cat)

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
