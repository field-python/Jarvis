#!/usr/bin/env python3
"""trivia.py — AI-powered trivia game for Jarvis terminal."""
import sys, os, subprocess, tty, termios, json, random, tempfile
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent
generate   = str(base_dir / "scripts" / "generate.py")
model      = os.environ.get("JARVIS_MODEL", "Jarvis")
host       = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
PURPLE = "\033[95m"
RESET  = "\033[0m"

CATEGORIES = [
    ("🌍 World History",    "world history, ancient civilizations, wars, empires"),
    ("🔬 Science",          "physics, chemistry, biology, astronomy, inventions"),
    ("🐾 Nature & Animals", "animals, plants, ecosystems, evolution, wildlife"),
    ("🗺️  Geography",       "countries, capitals, mountains, rivers, flags"),
    ("🎬 Pop Culture",      "movies, music, TV shows, celebrities, video games"),
    ("🪖 Survival & Prep",  "wilderness survival, first aid, bushcraft, prepping"),
    ("💻 Tech & Computers", "computers, internet, programming, gadgets, AI"),
    ("🏛️  US History",      "American history, presidents, constitution, civil war"),
    ("🥩 Food & Cooking",   "cuisine, ingredients, recipes, food history"),
    ("🔢 Mixed Trivia",     "random mix of all topics"),
]

def getch():
    import select as _sel, os as _os
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = _sel.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", errors="replace")
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def clear():
    os.system("clear")

def generate_questions(category_desc, n=5):
    """Ask the AI to generate n trivia questions as JSON."""
    prompt = (
        f"Generate exactly {n} multiple-choice trivia questions about: {category_desc}.\n\n"
        "Respond with ONLY a JSON array (no markdown, no explanation) in this exact format:\n"
        '[\n'
        '  {"q": "Question text?", "a": ["Correct answer", "Wrong 1", "Wrong 2", "Wrong 3"], "fact": "Short interesting fact"}\n'
        ']\n\n'
        "Rules:\n"
        "- First element of 'a' array is ALWAYS the correct answer\n"
        "- Make questions moderately challenging but not obscure\n"
        "- Keep questions under 100 characters\n"
        "- Keep each answer option under 40 characters\n"
        "- The 'fact' is a bonus interesting detail (under 80 chars)\n"
        f"- Generate EXACTLY {n} questions\n"
        "- Output ONLY the JSON array, nothing else"
    )
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="jarvis-trivia-", delete=False
        )
        tmp.write(prompt)
        tmp.close()
        result = subprocess.run(
            [sys.executable, generate, model, host, tmp.name],
            capture_output=True, text=True, timeout=90,
            env={**os.environ, "JARVIS_THINK": "0"}
        )
        raw = result.stdout.strip()
        # Extract JSON array — model may wrap it in markdown fences
        start = raw.find('[')
        end   = raw.rfind(']') + 1
        if start == -1 or end == 0:
            return None
        data = json.loads(raw[start:end])
        valid = [item for item in data
                 if 'q' in item and 'a' in item and len(item['a']) == 4]
        return valid if valid else None
    except Exception as e:
        return None  # caller handles error display
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except OSError: pass

Q_COUNTS = [5, 10, 25]

def show_count_menu():
    """Select number of questions before picking a category."""
    sel = 0
    while True:
        clear()
        print(f"\n  {BOLD}{CYAN}══════════ JARVIS TRIVIA ══════════{RESET}\n")
        print(f"  {DIM}How many questions?{RESET}\n")
        for i, n in enumerate(Q_COUNTS):
            if i == sel:
                print(f"  {BOLD}{CYAN}▶  {n} questions{RESET}")
            else:
                print(f"  {DIM}   {n} questions{RESET}")
        print(f"\n  {DIM}↑↓ to select  |  Enter to continue  |  Q to quit{RESET}")
        ch = getch()
        if ch in ("\x1b[A", "\x1bOA"):
            sel = (sel - 1) % len(Q_COUNTS)
        elif ch in ("\x1b[B", "\x1bOB"):
            sel = (sel + 1) % len(Q_COUNTS)
        elif ch in ("\r", "\n"):
            return Q_COUNTS[sel]
        elif ch.lower() in ("q", "\x1b"):
            return None


def show_category_menu():
    sel = 0
    while True:
        clear()
        print(f"\n  {BOLD}{CYAN}══════════ JARVIS TRIVIA ══════════{RESET}\n")
        print(f"  {DIM}Pick a category:{RESET}\n")
        for i, (name, _) in enumerate(CATEGORIES):
            if i == sel:
                print(f"  {BOLD}{CYAN}▶ {name}{RESET}")
            else:
                print(f"  {DIM}  {name}{RESET}")
        print(f"\n  {DIM}↑↓ to navigate  |  Enter to start  |  Q to quit{RESET}")

        ch = getch()
        if ch in ("\x1b[A", "\x1bOA"):  # up
            sel = (sel - 1) % len(CATEGORIES)
        elif ch in ("\x1b[B", "\x1bOB"):  # down
            sel = (sel + 1) % len(CATEGORIES)
        elif ch in ("\r", "\n"):
            return sel
        elif ch.lower() in ("q", "\x1b"):
            return None

def play_round(category_idx, num_q=5):
    cat_name, cat_desc = CATEGORIES[category_idx]
    clear()
    print(f"\n  {BOLD}{CYAN}══ {cat_name} ══{RESET}")
    print(f"\n  {YELLOW}Generating {num_q} questions…{RESET}", flush=True)

    questions = generate_questions(cat_desc, num_q)
    if not questions:
        clear()
        print(f"\n  {RED}Could not generate questions.{RESET}")
        print(f"  {DIM}Make sure Ollama is running:  ollama serve{RESET}")
        print(f"\n  {DIM}Press any key to return…{RESET}", flush=True)
        getch()
        return

    score = 0
    for qi, item in enumerate(questions[:num_q]):
        q      = item['q']
        answers = item['a'][:]
        correct = answers[0]
        random.shuffle(answers)
        correct_idx = answers.index(correct)
        fact   = item.get('fact', '')

        sel = 0
        answered = None
        while answered is None:
            clear()
            print(f"\n  {BOLD}{CYAN}══ JARVIS TRIVIA ══{RESET}  {DIM}{cat_name}{RESET}")
            print(f"\n  {DIM}Question {qi+1}/{min(num_q,len(questions))}  |  Score: {score}{RESET}\n")
            # Draw progress bar
            bar_filled = int((qi / num_q) * 20)
            bar = f"  {CYAN}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}"
            print(bar + "\n")
            print(f"  {BOLD}{q}{RESET}\n")
            labels = ['A', 'B', 'C', 'D']
            for i, ans in enumerate(answers):
                if i == sel:
                    print(f"  {BOLD}{CYAN}▶ {labels[i]}) {ans}{RESET}")
                else:
                    print(f"  {DIM}  {labels[i]}) {ans}{RESET}")
            print(f"\n  {DIM}↑↓ to select  |  Enter to answer{RESET}")

            ch = getch()
            if ch in ("\x1b[A", "\x1bOA"):
                sel = (sel - 1) % 4
            elif ch in ("\x1b[B", "\x1bOB"):
                sel = (sel + 1) % 4
            elif ch in ("\r", "\n"):
                answered = sel

        # Show result
        clear()
        print(f"\n  {BOLD}{CYAN}══ JARVIS TRIVIA ══{RESET}  {DIM}{cat_name}{RESET}")
        print(f"\n  {DIM}Question {qi+1}/{min(num_q,len(questions))}{RESET}\n")
        print(f"  {BOLD}{q}{RESET}\n")
        for i, ans in enumerate(answers):
            if i == correct_idx:
                marker = f"{GREEN}✓{RESET}"
                color  = GREEN
            elif i == answered and i != correct_idx:
                marker = f"{RED}✗{RESET}"
                color  = RED
            else:
                marker = " "
                color  = DIM
            print(f"  {marker} {color}{labels[i]}) {ans}{RESET}")

        if answered == correct_idx:
            score += 1
            print(f"\n  {GREEN}{BOLD}Correct! +1{RESET}")
        else:
            print(f"\n  {RED}{BOLD}Wrong!{RESET}  Correct: {GREEN}{correct}{RESET}")

        if fact:
            print(f"\n  {DIM}💡 {fact}{RESET}")

        print(f"\n  {DIM}Press any key for next…{RESET}", flush=True)
        getch()

    # Final score screen
    clear()
    pct = int(score / num_q * 100)
    if pct == 100:
        grade = f"{GREEN}{BOLD}PERFECT! 🏆{RESET}"
    elif pct >= 80:
        grade = f"{GREEN}Excellent! 🌟{RESET}"
    elif pct >= 60:
        grade = f"{YELLOW}Good job! 👍{RESET}"
    elif pct >= 40:
        grade = f"{YELLOW}Not bad! 📚{RESET}"
    else:
        grade = f"{RED}Keep studying! 💪{RESET}"

    print(f"\n  {BOLD}{CYAN}══ ROUND COMPLETE ══{RESET}\n")
    print(f"  {BOLD}Score: {score}/{num_q}  ({pct}%){RESET}")
    print(f"  {grade}")
    # ASCII score bar
    bar_filled = int(pct / 5)
    print(f"\n  {CYAN}{'█' * bar_filled}{'░' * (20 - bar_filled)}{RESET}")
    print(f"\n  {DIM}Press any key to return to menu…{RESET}", flush=True)
    getch()
    return score

def main():
    total_score = 0
    total_q     = 0
    rounds      = 0

    while True:
        num_q = show_count_menu()
        if num_q is None:
            break
        cat_idx = show_category_menu()
        if cat_idx is None:
            break
        score = play_round(cat_idx, num_q=num_q)
        if score is not None:
            total_score += score
            total_q     += num_q
            rounds      += 1

    if rounds > 0:
        clear()
        pct = int(total_score / total_q * 100)
        print(f"\n  {BOLD}{CYAN}══ SESSION COMPLETE ══{RESET}\n")
        print(f"  Rounds played: {rounds}")
        print(f"  Total score:   {total_score}/{total_q}  ({pct}%)")
        print(f"\n  {DIM}Thanks for playing Jarvis Trivia!{RESET}\n")
    else:
        clear()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
