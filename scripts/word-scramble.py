#!/usr/bin/env python3
"""word-scramble.py — Terminal Word Scramble for Jarvis."""
import sys, os, random, time, tty, termios
from pathlib import Path

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

# (word, hint, category)
WORDS = [
    # Survival / outdoors
    ("TINDER",     "Catches a spark",              "Survival"),
    ("SNARE",      "Wire animal trap",             "Survival"),
    ("COMPASS",    "Navigation tool",              "Survival"),
    ("SHELTER",    "Protection from elements",     "Survival"),
    ("FORAGING",   "Finding wild food",            "Survival"),
    ("BIVOUAC",    "Temporary camp",               "Survival"),
    ("DEADFALL",   "Primitive trap",               "Survival"),
    ("KINDLING",   "Fire-starting sticks",         "Survival"),
    ("PARACORD",   "550-lb nylon rope",            "Survival"),
    ("SIGNALING",  "Calling for rescue",           "Survival"),
    # Nature / geography
    ("TUNDRA",     "Frozen biome",                 "Nature"),
    ("FJORD",      "Norwegian water inlet",        "Nature"),
    ("GLACIER",    "Slow-moving ice mass",         "Nature"),
    ("PLATEAU",    "Flat elevated land",           "Nature"),
    ("ESTUARY",    "River meets the sea",          "Nature"),
    ("STALACTITE", "Hangs from cave ceiling",      "Nature"),
    ("STALAGMITE", "Grows from cave floor",        "Nature"),
    ("VOLCANO",    "Mountain with magma",          "Nature"),
    ("AQUIFER",    "Underground water layer",      "Nature"),
    ("CREVASSE",   "Crack in a glacier",           "Nature"),
    # Science / tech
    ("FREQUENCY",  "Cycles per second",            "Science"),
    ("ALGORITHM",  "Step-by-step solution",        "Science"),
    ("SATELLITE",  "Orbits the Earth",             "Science"),
    ("ELECTRON",   "Negative atomic particle",     "Science"),
    ("ENCRYPTION", "Scrambling data",              "Science"),
    ("BANDWIDTH",  "Data capacity",                "Science"),
    ("TELESCOPE",  "Views distant stars",          "Science"),
    ("PHOTON",     "Light particle",               "Science"),
    ("ISOTOPE",    "Different atomic mass",        "Science"),
    ("CATALYST",   "Speeds up reactions",          "Science"),
    # History / culture
    ("ARMISTICE",  "Ceasefire agreement",          "History"),
    ("FLINTLOCK",  "Old gun mechanism",            "History"),
    ("MANIFEST",   "Destiny or document",          "History"),
    ("COLONIZE",   "Settle a new territory",       "History"),
    ("REPUBLIC",   "Representative government",    "History"),
    ("CRUSADES",   "Medieval holy wars",           "History"),
    ("AZTEC",      "Ancient Mexican empire",       "History"),
    ("SAMURAI",    "Japanese warrior class",       "History"),
    ("GLADIATOR",  "Roman arena fighter",          "History"),
    ("PHARAOH",    "Ancient Egyptian ruler",       "History"),
    # Alaska-themed
    ("PERMAFROST", "Frozen ground layer",          "Alaska"),
    ("AURORA",     "Northern lights",              "Alaska"),
    ("MUSHER",     "Sled dog racer",               "Alaska"),
    ("SALMON",     "Pacific fish",                 "Alaska"),
    ("CARIBOU",    "Arctic reindeer",              "Alaska"),
    ("DENALI",     "Highest US peak",              "Alaska"),
    ("SOLSTICE",   "Longest or shortest day",      "Alaska"),
    ("KAYAK",      "Inuit paddling craft",         "Alaska"),
    ("TUNDRA",     "Flat frozen biome",            "Alaska"),
    ("HALIBUT",    "Large flat fish",              "Alaska"),
]

DIFFICULTIES = [
    ("Easy",   4, 6,  60),   # word length range, time limit
    ("Medium", 6, 9,  45),
    ("Hard",   8, 12, 30),
]

def scramble(word):
    letters = list(word)
    for _ in range(20):
        random.shuffle(letters)
        if "".join(letters) != word:
            return "".join(letters)
    return "".join(letters)

def getch():
    """Read one keypress; returns full escape sequence for arrow keys."""
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
                return "\x1b" + rest   # e.g. "\x1b[A"
            return "\x1b"              # plain ESC
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def read_line(prompt):
    """Read a line with visible echo (no raw mode)."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        return input().strip().upper()
    except EOFError:
        return ""

def clear():
    os.system("clear")

# In-place redraw: track lines printed so we can overwrite without scrollback
_draw_lines = 0

def draw_game(scrambled, hint, category, time_left, time_limit, guess, score, streak, q_num, total_q):
    global _draw_lines
    pct = time_left / time_limit
    bar_len = 20
    bar_filled = int(pct * bar_len)
    if pct > 0.5:   bar_color = GREEN
    elif pct > 0.25: bar_color = YELLOW
    else:            bar_color = RED

    rows = [
        "",
        f"  {BOLD}{CYAN}══════════ WORD SCRAMBLE ══════════{RESET}",
        "",
        f"  {DIM}Question {q_num}/{total_q}  |  Score: {BOLD}{score}{RESET}{DIM}  |  Streak: {streak}🔥{RESET}",
        "",
        f"  {bar_color}{'█'*bar_filled}{'░'*(bar_len-bar_filled)}{RESET}  {bar_color}{BOLD}{int(time_left)}s{RESET}",
        "",
        f"  {DIM}Category: {category}{RESET}",
        f"  {DIM}Hint: {hint}{RESET}",
        "",
        f"  {BOLD}{CYAN}{'  '.join(scrambled)}{RESET}",
        "",
        f"  Your answer: {BOLD}{guess}{RESET}_",
        "",
        f"  {DIM}Type letters · Backspace · Enter to submit · Q to quit{RESET}",
    ]

    buf = ""
    if _draw_lines > 0:
        # Move cursor up to start of last frame, clear to end of screen
        buf += f"\033[{_draw_lines}A\033[J"
    buf += "\n".join(rows)
    sys.stdout.write(buf)
    sys.stdout.flush()
    _draw_lines = len(rows)

def diff_menu():
    sel = 1  # default medium
    while True:
        clear()
        print(f"\n  {BOLD}{CYAN}══════════ WORD SCRAMBLE ══════════{RESET}\n")
        print(f"  {DIM}Select difficulty:{RESET}\n")
        for i, (name, mn, mx, t) in enumerate(DIFFICULTIES):
            desc = f"{mn}-{mx} letter words, {t}s each"
            if i == sel:
                print(f"  {BOLD}{CYAN}▶ {name:<8}{DIM}  {desc}{RESET}")
            else:
                print(f"  {DIM}  {name:<8}  {desc}{RESET}")
        print(f"\n  {DIM}↑↓ to navigate  |  Enter to start  |  Q to quit{RESET}")
        ch = getch()
        if ch in ("\x1b[A", "\x1bOA"):    sel = (sel - 1) % 3
        elif ch in ("\x1b[B", "\x1bOB"): sel = (sel + 1) % 3
        elif ch in ("\r", "\n"):          return sel
        elif ch == "\x1b" or ch.lower() == 'q': return None   # plain ESC or Q

def play_round(diff_idx, num_q=8):
    diff_name, min_len, max_len, time_limit = DIFFICULTIES[diff_idx]
    pool = [(w, h, c) for w, h, c in WORDS if min_len <= len(w) <= max_len]
    if not pool:
        pool = WORDS[:]
    random.shuffle(pool)
    questions = pool[:num_q]

    score  = 0
    streak = 0
    max_streak = 0

    for qi, (word, hint, cat) in enumerate(questions):
        global _draw_lines
        _draw_lines = 0   # fresh in-place redraw for each question
        clear()
        sc_word = scramble(word)
        guess   = ""
        start   = time.monotonic()
        result  = None  # 'correct', 'timeout', 'wrong', 'quit'

        while True:
            elapsed    = time.monotonic() - start
            time_left  = max(0.0, time_limit - elapsed)
            draw_game(sc_word, hint, cat, time_left, time_limit, guess, score, streak, qi+1, num_q)

            if time_left <= 0:
                result = 'timeout'; break

            # Non-blocking key read with 0.25s poll
            import select
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                r, _, _ = select.select([fd], [], [], 0.25)
                if r:
                    ch = os.read(fd, 1).decode("utf-8", errors="replace")
                    if ch == '\x03':
                        raise KeyboardInterrupt
                    elif ch == '\x1b':
                        # Drain arrow/function key sequence — don't treat as quit
                        r2, _, _ = select.select([fd], [], [], 0.05)
                        if r2:
                            os.read(fd, 2)   # discard [A / [B etc.
                        else:
                            result = 'quit'; break   # plain ESC
                    elif ch.lower() == 'q':
                        result = 'quit'; break
                    elif ch in ('\r', '\n'):
                        result = 'correct' if guess == word else 'wrong'
                        break
                    elif ch in ('\x7f', '\x08'):
                        guess = guess[:-1]
                    elif ch.isalpha() and len(guess) < len(word):
                        letter = ch.upper()
                        # Only accept letters actually in the scramble
                        available = list(sc_word)
                        for used in guess:
                            if used in available:
                                available.remove(used)
                        if letter in available:
                            guess += letter
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

        if result == 'quit':
            break

        # Score calculation
        if result == 'correct':
            streak += 1
            max_streak = max(max_streak, streak)
            bonus     = streak * 5 if streak > 1 else 0
            pts       = 10 + bonus + int(time_left / time_limit * 10)
            score    += pts
            msg       = f"{GREEN}{BOLD}Correct! +{pts}{RESET}"
            if streak > 1:
                msg += f"  {YELLOW}(streak x{streak}){RESET}"
        elif result == 'timeout':
            streak = 0
            msg    = f"{RED}Time's up!{RESET}  The word was: {BOLD}{word}{RESET}"
        else:
            streak = 0
            msg    = f"{RED}Wrong!{RESET}  The word was: {BOLD}{word}{RESET}"

        # Show result briefly
        clear()
        print(f"\n  {BOLD}{CYAN}══════════ WORD SCRAMBLE ══════════{RESET}\n")
        sc_display = "  ".join(sc_word)
        print(f"  Scramble: {CYAN}{BOLD}{sc_display}{RESET}")
        print(f"  Answer:   {GREEN}{BOLD}{word}{RESET}")
        print(f"  {DIM}{hint}{RESET}\n")
        print(f"  {msg}")
        print(f"\n  {DIM}Score: {score}  |  Press any key…{RESET}", flush=True)
        time.sleep(0.3)
        getch()

        if result == 'quit':
            break

    # Results screen
    clear()
    print(f"\n  {BOLD}{CYAN}══ ROUND COMPLETE ══{RESET}\n")
    print(f"  Difficulty:  {diff_name}")
    print(f"  Score:       {BOLD}{score}{RESET}")
    print(f"  Best streak: {YELLOW}{max_streak}🔥{RESET}")
    print(f"\n  {DIM}Press any key…{RESET}", flush=True)
    getch()
    return score

def main():
    total = 0
    rounds = 0
    while True:
        d = diff_menu()
        if d is None:
            break
        s = play_round(d)
        total  += s
        rounds += 1

        clear()
        print(f"\n  {BOLD}{CYAN}Play again?{RESET}  {DIM}(Y/N){RESET}", end=" ", flush=True)
        ch = getch().upper()
        print()
        if ch != 'Y':
            break

    clear()
    if rounds > 0:
        print(f"\n  {BOLD}{CYAN}Session over!{RESET}  Total score: {YELLOW}{total}{RESET}  Rounds: {rounds}\n")
    else:
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
