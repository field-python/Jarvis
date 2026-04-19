#!/usr/bin/env python3
"""hangman.py — Terminal Hangman for Jarvis."""
import sys, os, random, tty, termios
from pathlib import Path

BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

# Word list with hints
WORDS = [
    ("PYTHON",     "A popular programming language"),
    ("SURVIVAL",   "Staying alive in the wild"),
    ("SATELLITE",  "Orbits above the Earth"),
    ("AVALANCHE",  "Snow disaster on a mountain"),
    ("FJORD",      "Norwegian coastal inlet"),
    ("ECLIPSE",    "Moon blocks the sun"),
    ("ALGORITHM",  "Step-by-step problem solution"),
    ("WILDERNESS", "Untamed natural land"),
    ("TELESCOPE",  "Used to see distant stars"),
    ("COMPASS",    "Navigation tool with a needle"),
    ("FIREARM",    "Ranged weapon"),
    ("TUNDRA",     "Frozen treeless biome"),
    ("PERMAFROST", "Permanently frozen ground"),
    ("BUSHCRAFT",  "Living off the land skills"),
    ("FERMENTING", "Preserving food with bacteria"),
    ("HYPOTHESIS", "A testable scientific guess"),
    ("MERIDIAN",   "Longitude line on a globe"),
    ("CROSSBOW",   "Medieval ranged weapon"),
    ("GENERATOR",  "Converts mechanical to electrical"),
    ("CAMOUFLAGE", "Blend into surroundings"),
    ("BARRICADE",  "A defensive barrier"),
    ("DEHYDRATE",  "Remove water from food"),
    ("STALACTITE", "Hangs from cave ceiling"),
    ("STALAGMITE", "Grows from cave floor"),
    ("ENCRYPTION", "Scrambling data for security"),
    ("METABOLISM", "Body's energy processing"),
    ("RESERVOIR",  "Large stored water supply"),
    ("TOURNIQUET", "Stops blood flow to a limb"),
    ("FLINTLOCK",  "Old-style firearm ignition"),
    ("SHORTWAVE",  "Long-range radio frequency"),
    ("LATITUDE",   "North-south coordinate"),
    ("LONGITUDE",  "East-west coordinate"),
    ("TOPOGRAPHY", "Terrain shape and features"),
    ("PHOSPHORUS", "Glows in the dark element"),
    ("BALLISTICS", "Science of projectile motion"),
    ("DEADFALL",   "A primitive trap"),
    ("SNARE",      "Wire animal trap"),
    ("KINDLING",   "Small sticks to start a fire"),
    ("POTASSIUM",  "Element symbol K"),
    ("HOMESTEAD",  "Self-sufficient rural property"),
    ("FREQUENCY",  "Cycles per second in radio"),
    ("CALLSIGN",   "Ham radio identifier"),
    ("BANDWIDTH",  "Data transmission capacity"),
    ("LOCKPICK",   "Tool to open locks"),
    ("BIVOUAC",    "Temporary outdoor shelter"),
    ("PARACORD",   "Strong nylon rope"),
    ("TINDER",     "Catches a spark for fire"),
    ("MACHETE",    "Large chopping blade"),
    ("FORAGING",   "Gathering wild food"),
    ("AURORA",     "Northern lights display"),
    ("MUSHER",     "Sled dog racer"),
    ("SALMON",     "Pacific fish"),
    ("CARIBOU",    "Arctic reindeer"),
    ("DENALI",     "Highest US peak"),
    ("KAYAK",      "Inuit paddling craft"),
    ("HALIBUT",    "Large flat fish"),
]

GALLOWS = [
    # 0 wrong
    ["      ",
     "      ",
     "      ",
     "      ",
     "      ",
     "══════"],
    # 1 wrong
    ["  ╔═══",
     "  ║   ",
     "  ║   ",
     "  ║   ",
     "  ║   ",
     "══╩═══"],
    # 2 wrong
    ["  ╔═══",
     "  ║  O",
     "  ║   ",
     "  ║   ",
     "  ║   ",
     "══╩═══"],
    # 3 wrong
    ["  ╔═══",
     "  ║  O",
     "  ║  |",
     "  ║   ",
     "  ║   ",
     "══╩═══"],
    # 4 wrong
    ["  ╔═══",
     "  ║  O",
     "  ║ /|",
     "  ║   ",
     "  ║   ",
     "══╩═══"],
    # 5 wrong
    ["  ╔═══",
     "  ║  O",
     "  ║ /|\\",
     "  ║   ",
     "  ║   ",
     "══╩═══"],
    # 6 wrong
    ["  ╔═══",
     "  ║  O",
     "  ║ /|\\",
     "  ║  | ",
     "  ║   ",
     "══╩═══"],
    # 7 wrong — dead
    ["  ╔═══",
     "  ║  O",
     "  ║ /|\\",
     "  ║  | ",
     "  ║ / \\",
     "══╩═══"],
]

MAX_WRONG = 7

# Difficulty: (name, min_len, max_len)
DIFFICULTIES = [
    ("Easy",   3, 6),
    ("Medium", 7, 9),
    ("Hard",  10, 99),
]


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
                _os.read(fd, 2)   # drain arrow/function key sequence
                return "\x1b[_"   # sentinel — not ESC, not a letter
            return "\x1b"         # plain ESC
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


_draw_lines = 0

def draw(word, guessed, wrong_letters, hint, wins, losses):
    global _draw_lines
    n_wrong = len(wrong_letters)
    stage   = GALLOWS[min(n_wrong, MAX_WRONG)]

    rows = []
    rows.append("")
    rows.append(f"  {BOLD}{CYAN}══════════ HANGMAN ══════════{RESET}  {DIM}W:{wins}  L:{losses}{RESET}")
    rows.append("")

    # Gallows — red when danger (5+ wrong), dim otherwise
    for line in stage:
        if n_wrong >= MAX_WRONG:
            rows.append(f"  {RED}{line}{RESET}")
        elif n_wrong >= 5:
            rows.append(f"  {RED}{line}{RESET}")
        else:
            rows.append(f"  {DIM}{line}{RESET}")

    # Word display
    rows.append("")
    display = ""
    for ch in word:
        if ch in guessed:
            display += f"{BOLD}{GREEN}{ch}{RESET} "
        else:
            display += f"{YELLOW}_{RESET} "
    rows.append(f"  {display}")

    # Hint
    rows.append(f"\n  {DIM}Hint: {hint}{RESET}")

    # Wrong letters — dim red
    if wrong_letters:
        wrong_str = "  ".join(f"{DIM}{RED}{c}{RESET}" for c in sorted(wrong_letters))
        rows.append(f"\n  Wrong: {wrong_str}")
    else:
        rows.append(f"\n  {DIM}No wrong guesses yet{RESET}")

    # Remaining
    remaining = MAX_WRONG - n_wrong
    if remaining <= 2:
        rows.append(f"\n  {RED}{BOLD}⚠  Only {remaining} guess{'es' if remaining!=1 else ''} left!{RESET}")
    else:
        rows.append(f"\n  {DIM}Guesses left: {remaining}{RESET}")

    rows.append(f"\n  {DIM}Type a letter to guess  |  Q to quit{RESET}")

    buf = ""
    if _draw_lines > 0:
        buf += f"\033[{_draw_lines}A\033[J"
    buf += "\n".join(rows)
    sys.stdout.write(buf)
    sys.stdout.flush()
    _draw_lines = len(rows)


def diff_menu():
    sel = 1  # default Medium
    while True:
        clear()
        print(f"\n  {BOLD}{CYAN}══════════ HANGMAN ══════════{RESET}\n")
        print(f"  {DIM}Select difficulty:{RESET}\n")
        for i, (name, mn, mx) in enumerate(DIFFICULTIES):
            mx_label = f"{mx}+" if mx == 99 else str(mx)
            desc = f"{mn}-{mx_label} letter words"
            if i == sel:
                print(f"  {BOLD}{CYAN}▶ {name:<8}{DIM}  {desc}{RESET}")
            else:
                print(f"  {DIM}  {name:<8}  {desc}{RESET}")
        print(f"\n  {DIM}↑↓ to navigate  |  Enter to start  |  Q to quit{RESET}")
        ch = getch()
        if ch in ("\x1b[A", "\x1bOA"):   sel = (sel - 1) % len(DIFFICULTIES)
        elif ch in ("\x1b[B", "\x1bOB"): sel = (sel + 1) % len(DIFFICULTIES)
        elif ch in ("\r", "\n"):          return sel
        elif ch in ("\x1b", "Q", "q"):    return None


def main():
    global _draw_lines
    wins = 0
    losses = 0

    diff_idx = diff_menu()
    if diff_idx is None:
        clear()
        return

    diff_name, min_len, max_len = DIFFICULTIES[diff_idx]
    pool = [(w, h) for w, h in WORDS if min_len <= len(w) <= max_len]
    if not pool:
        pool = WORDS[:]

    while True:
        try:
            word, hint = random.choice(pool)
            guessed   = set()
            wrong     = set()
            won       = False
            quit_game = False
            _draw_lines = 0

            clear()
            while True:
                draw(word, guessed, wrong, hint, wins, losses)
                all_revealed = all(c in guessed for c in word)
                if all_revealed:
                    won = True; break
                if len(wrong) >= MAX_WRONG:
                    break
                ch = getch().upper()
                if ch in ('Q', '\x1b'):
                    quit_game = True; break
                if ch == '\x03':
                    raise KeyboardInterrupt
                if ch.isalpha() and len(ch) == 1:
                    if ch not in guessed and ch not in wrong:
                        if ch in word: guessed.add(ch)
                        else: wrong.add(ch)

            if quit_game:
                break

            # Show result
            _draw_lines = 0
            clear()
            print(f"\n  {BOLD}{CYAN}══════════ HANGMAN ══════════{RESET}\n")
            stage = GALLOWS[min(len(wrong), MAX_WRONG)]
            color = GREEN if won else RED
            for line in stage:
                print(f"  {color}{line}{RESET}")
            revealed = " ".join(f"{BOLD}{GREEN}{c}{RESET}" for c in word)
            print(f"\n  {revealed}\n")
            if won:
                wins += 1
                print(f"  {GREEN}{BOLD}You got it! 🎉{RESET}")
            else:
                losses += 1
                print(f"  {RED}{BOLD}Hanged! The word was: {word}{RESET}")
            print(f"  {DIM}{hint}{RESET}")
            print(f"\n  {DIM}W:{wins}  L:{losses}{RESET}")
            print(f"\n  {DIM}Play again? (Y/N){RESET}", end="", flush=True)
            ch = getch().upper()
            print()
            if ch != 'Y':
                break

        except KeyboardInterrupt:
            break

    clear()
    if wins + losses > 0:
        print(f"\n  {BOLD}{CYAN}Session complete!{RESET}  Wins: {GREEN}{wins}{RESET}  Losses: {RED}{losses}{RESET}\n")
    else:
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        sys.exit(0)
