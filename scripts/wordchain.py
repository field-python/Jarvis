#!/usr/bin/env python3
"""wordchain.py — Word Chain: each word must start with the last letter of the previous."""
import sys
import os
import re
import random
import tty
import termios
import select
from pathlib import Path

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
HR     = "━" * 52

# Minimum built-in word list (used if system dictionary unavailable)
BUILTIN = [
    "apple","enter","reveal","loose","every","youth","height","table","eager","rail",
    "label","light","trust","tiger","radio","order","river","range","event","travel",
    "listen","noble","early","youth","grape","elder","dream","maple","power","ruby",
    "young","green","north","happy","yodel","level","talon","nymph","heard","dance",
    "eager","reply","angry","press","ebony","groan","niche","exact","twist","total",
    "lemon","extra","alarm","marry","lotus","solid","dagger","round","divide","event",
    "tower","wonder","remind","dental","arrive","eagle","laugh","heavy","yard","digit",
    "travel","lunar","rally","youth","oblong","gravel","local","atlas","sunset","train",
    "noble","elbow","walnut","temple","escape","equal","laser","rainy","yellow","wafer",
    "ruler","raven","night","glass","snail","label","latch","harsh","hotel","linear",
    "rogue","engine","east","topic","crown","nurse","echo","ocean","north","hatch",
    "habit","twist","water","rebel","lantern","nerve","vapor","rival","alarm","mental",
    "topic","carrot","tremble","eagle","elbow","wander","rapid","demon","north","heat",
    "tutor","rattle","exit","torch","hedge","extend","decide","earth","hunt","think",
    "kneel","lunar","ramp","pivot","trail","lever","relic","crawl","wider","revert",
]


def load_words():
    """Load word list from system dict or fall back to built-in."""
    for path in ("/usr/share/dict/words", "/usr/dict/words"):
        p = Path(path)
        if p.exists():
            words = [
                w.strip().lower() for w in p.read_text(encoding="utf-8",
                                                        errors="ignore").splitlines()
                if 4 <= len(w.strip()) <= 10
                and w.strip().isalpha()
                and w.strip() == w.strip().lower()   # exclude proper nouns
            ]
            if len(words) > 500:
                return set(words), words
    return set(BUILTIN), list(set(BUILTIN))


def getch():
    import os as _os
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                _os.read(fd, 2)
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_word(prompt_str):
    """Accept letters only. Returns lowercased string or None on ESC."""
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
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf.pop()
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = (total - 1) // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
                    sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ch.isalpha():
                c = ch.lower()
                buf.append(c)
                sys.stdout.write(c)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def jarvis_pick(words_list, start_letter, used):
    """Pick Jarvis's next word. Returns word or None if Jarvis can't continue."""
    candidates = [w for w in words_list if w[0] == start_letter and w not in used]
    return random.choice(candidates) if candidates else None


def draw_chain(chain, next_letter, score, msg=""):
    os.system("clear")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Word Chain{RESET}  {DIM}Score: {score}{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()

    display = chain[-7:] if len(chain) > 7 else chain
    for speaker, word in display:
        if speaker == "Jarvis":
            print(f"  {CYAN}Jarvis ▸{RESET} {BOLD}{word}{RESET}"
                  f"  {DIM}(ends in '{word[-1].upper()}'){RESET}")
        else:
            print(f"  {GREEN}You    ▸{RESET} {BOLD}{word}{RESET}"
                  f"  {DIM}(ends in '{word[-1].upper()}'){RESET}")

    print()
    print(f"  {YELLOW}Next word must start with: {BOLD}{next_letter.upper()}{RESET}")
    print()
    if msg:
        print(f"  {msg}")
        print()


def play_game(words_set, words_list):
    """Returns (score, outcome_str)."""
    chain = []
    used  = set()
    score = 0

    # Jarvis starts with a random 4-7 letter word
    starters = [w for w in words_list if 4 <= len(w) <= 7]
    start = random.choice(starters if starters else words_list)
    chain.append(("Jarvis", start))
    used.add(start)
    next_letter = start[-1]

    while True:
        draw_chain(chain, next_letter, score)
        print(f"  {DIM}Type a word starting with '{next_letter.upper()}'  |  ESC to quit{RESET}")

        raw = input_word(f"  {GREEN}Your word: {RESET}")
        if raw is None:
            return score, "quit"

        word = raw.strip().lower()

        if not word:
            draw_chain(chain, next_letter, score, f"{DIM}(enter a word){RESET}")
            getch()
            continue

        # Wrong starting letter
        if word[0] != next_letter:
            draw_chain(chain, next_letter, score,
                       f"{RED}✗  '{word}' doesn't start with '{next_letter.upper()}'. You lose.{RESET}")
            getch()
            return score, "wrong_letter"

        # Already used
        if word in used:
            draw_chain(chain, next_letter, score,
                       f"{RED}✗  '{word}' was already used. You lose.{RESET}")
            getch()
            return score, "repeated"

        # Validate against word list (only if we have a real dictionary)
        if len(words_set) > 500 and word not in words_set:
            draw_chain(chain, next_letter, score,
                       f"{RED}✗  '{word}' isn't in the word list. You lose.{RESET}")
            getch()
            return score, "invalid"

        # Good word
        score += 1
        chain.append(("You", word))
        used.add(word)
        next_letter = word[-1]

        # Jarvis responds
        jarvis_word = jarvis_pick(words_list, next_letter, used)
        if jarvis_word is None:
            draw_chain(chain, next_letter, score,
                       f"{GREEN}{BOLD}Jarvis has no valid word — you win!{RESET}")
            getch()
            return score, "win"

        chain.append(("Jarvis", jarvis_word))
        used.add(jarvis_word)
        next_letter = jarvis_word[-1]


def main():
    words_set, words_list = load_words()
    dict_note = f"{len(words_set):,} words" if len(words_set) > 500 else "built-in word list"

    os.system("clear")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Word Chain{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()
    print("  Each word must start with the LAST letter of the previous.")
    print("  No repeated words. Invalid words lose the round.")
    print(f"  {DIM}Dictionary: {dict_note}{RESET}")
    print()
    print(f"  {DIM}Any key to start  |  Q to quit{RESET}", end="", flush=True)

    if getch().lower() in ("q", "\x1b", "\x03"):
        return

    best = 0
    while True:
        score, outcome = play_game(words_set, words_list)
        best = max(best, score)

        os.system("clear")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print(f"{BOLD}  Word Chain  |  Round Over{RESET}")
        print(f"{BOLD}{CYAN}{HR}{RESET}")
        print()
        print(f"  Words this round:  {score}")
        print(f"  Personal best:     {best}")
        print()

        messages = {
            "win":          (GREEN, "You beat Jarvis — no words left for them!"),
            "wrong_letter": (RED,   "Wrong starting letter."),
            "repeated":     (RED,   "Word already used."),
            "invalid":      (RED,   "Not a valid word."),
            "quit":         (DIM,   "Quit."),
        }
        color, text = messages.get(outcome, (DIM, ""))
        print(f"  {color}{text}{RESET}")
        print()

        print(f"  {DIM}[Enter] Play again  |  [Q] Quit{RESET}", end="", flush=True)
        if getch().lower() in ("q", "\x1b", "\x03"):
            break

    os.system("clear")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
