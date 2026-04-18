#!/usr/bin/env python3
"""yahtzee.py — Full Yahtzee with redesigned layout"""
import os, sys, random, tty, termios, select
from collections import Counter

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
MG  = "\033[95m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
HR  = "━" * 58

CATEGORIES = [
    ("ones",    "Ones",         "Sum of 1s",          "upper"),
    ("twos",    "Twos",         "Sum of 2s",          "upper"),
    ("threes",  "Threes",       "Sum of 3s",          "upper"),
    ("fours",   "Fours",        "Sum of 4s",          "upper"),
    ("fives",   "Fives",        "Sum of 5s",          "upper"),
    ("sixes",   "Sixes",        "Sum of 6s",          "upper"),
    ("3kind",   "3 of a Kind",  "Sum all dice",       "lower"),
    ("4kind",   "4 of a Kind",  "Sum all dice",       "lower"),
    ("fhouse",  "Full House",   "25 pts",             "lower"),
    ("sstr",    "Sm. Straight", "30 pts (4 seq)",     "lower"),
    ("lstr",    "Lg. Straight", "40 pts (5 seq)",     "lower"),
    ("yahtzee", "Yahtzee!",     "50 pts",             "lower"),
    ("chance",  "Chance",       "Sum all dice",       "lower"),
]
UPPER = [(k,n,d) for k,n,d,s in CATEGORIES if s=="upper"]
LOWER = [(k,n,d) for k,n,d,s in CATEGORIES if s=="lower"]
ALL_KEYS = [k for k,_,_,_ in CATEGORIES]

DIE_TOP    = "╔═══╗"
DIE_BOT    = "╚═══╝"

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd,1).decode("utf-8","replace")
        if ch == "\x1b":
            r,_,_ = select.select([fd],[],[],0.1)
            if r:
                rest = os.read(fd,2).decode("utf-8","replace")
                return "\x1b" + rest
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def roll_dice(dice, kept):
    return [dice[i] if kept[i] else random.randint(1,6) for i in range(5)]

def calc_score(key, dice):
    c      = Counter(dice)
    s      = sum(dice)
    vals   = sorted(set(dice))
    counts = sorted(c.values(), reverse=True)
    if key == "ones":    return c.get(1,0)
    if key == "twos":    return c.get(2,0)*2
    if key == "threes":  return c.get(3,0)*3
    if key == "fours":   return c.get(4,0)*4
    if key == "fives":   return c.get(5,0)*5
    if key == "sixes":   return c.get(6,0)*6
    if key == "3kind":   return s if counts[0]>=3 else 0
    if key == "4kind":   return s if counts[0]>=4 else 0
    if key == "fhouse":  return 25 if sorted(counts)==[2,3] else 0
    if key == "sstr":
        for seq in [[1,2,3,4],[2,3,4,5],[3,4,5,6]]:
            if all(v in vals for v in seq): return 30
        return 0
    if key == "lstr":
        for seq in [[1,2,3,4,5],[2,3,4,5,6]]:
            if all(v in vals for v in seq): return 40
        return 0
    if key == "yahtzee": return 50 if counts[0]==5 else 0
    if key == "chance":  return s
    return 0

def rolls_bar(left):
    filled = left
    empty  = 2 - left
    return f"{GR}{'█'*filled}{DIM}{'░'*empty}{R}"

def upper_bar(total):
    pct    = min(total, 63)
    filled = round(pct / 63 * 10)
    color  = GR if total >= 63 else YL
    return f"{color}{'█'*filled}{DIM}{'░'*(10-filled)}{R} {total}/63"

def cat_line(idx, key, name, dice, scores, cursor, phase, col_idx):
    """Render one scorecard row."""
    scored = scores.get(key)
    num    = f"{col_idx:>2}."

    if scored is not None:
        val  = f"{GR}{B}{scored:>3}{R}"
        mark = f"{GR}✓{R}"
        return f"  {DIM}{num}{R} {DIM}{name:<14}{R} {val} {mark}"
    else:
        pot = calc_score(key, dice)
        if phase == "choose" and idx == cursor:
            val  = f"{YL}{B}{pot:>3}{R}"
            mark = f"{YL}◄{R}"
            return f"  {YL}▶{R} {B}{name:<14}{R} {val} {mark}"
        elif pot > 0:
            val  = f"{CY}{pot:>3}{R}"
            return f"  {DIM}{num}{R} {name:<14} {val}  "
        else:
            return f"  {DIM}{num} {name:<14}   0  {R}"

def draw(dice, kept, rolls_left, scores, cursor, phase, round_num):
    os.system("clear")
    total       = sum(v for v in scores.values() if v is not None)
    upper_total = sum(scores.get(k,0) or 0 for k,_,_ in UPPER)
    bonus       = 35 if upper_total >= 63 else 0

    # Header
    print(f"{B}{CY}{HR}{R}")
    phase_lbl = f"{YL}ROLL{R}" if phase=="roll" else f"{MG}SCORE{R}"
    print(f"{B}{CY}  Jarvis  🎲  Yahtzee{R}  "
          f"{DIM}Round {round_num}/13{R}  {phase_lbl}  {DIM}Total:{R} {B}{GR}{total+bonus}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    # ── Dice row ──────────────────────────────────────────────────────────────
    tops  = "  ".join(DIE_TOP for _ in range(5))
    mids  = "  ".join(
        f"║ {GR}{B}{d}{R} ║" if kept[i] else f"║ {B}{d}{R} ║"
        for i,d in enumerate(dice)
    )
    bots  = "  ".join(DIE_BOT for _ in range(5))
    print(f"  {tops}")
    print(f"  {mids}")
    print(f"  {bots}")

    # Keep indicators
    keep_row = "  ".join(
        f"  {GR}{B}K{R}  " if kept[i] else f"  {DIM}_{R}  "
        for i in range(5)
    )
    print(f"  {keep_row}")
    print(f"   1     2     3     4     5\n")

    # Controls
    if phase == "roll":
        print(f"  {DIM}[1-5]{R} keep/unkeep   "
              f"{YL}[R]{R} roll ({rolls_bar(rolls_left)} left)   "
              f"{MG}[C]{R} go to scorecard   {DIM}[Q]{R} quit\n")
    else:
        print(f"  {MG}[↑↓]{R} navigate scorecard   "
              f"{YL}[Enter]{R} lock score   "
              f"{DIM}[Q]{R} quit\n")

    # ── Scorecard — two columns ───────────────────────────────────────────────
    divider = f"  {'─'*27}  {'─'*27}"

    # Upper header
    ub = upper_bar(upper_total)
    print(f"  {B}UPPER SECTION{R} {ub}   {B}LOWER SECTION{R}")
    print(divider)

    upper_idx = list(range(6))
    lower_idx = list(range(6, 13))

    rows = max(len(upper_idx), len(lower_idx))
    for r in range(rows):
        left_str  = ""
        right_str = ""

        if r < len(upper_idx):
            ui = upper_idx[r]
            k,n,_ = UPPER[r]
            left_str = cat_line(ui, k, n, dice, scores, cursor, phase, r+1)

        if r < len(lower_idx):
            li = lower_idx[r]
            k,n,_ = LOWER[r]
            right_str = cat_line(li, k, n, dice, scores, cursor, phase, r+7)

        # Pad left column to fixed width
        import re as _re
        plain_left = _re.sub(r"\033\[[0-9;]*m","",left_str)
        pad = max(0, 30 - len(plain_left))
        print(f"{left_str}{' '*pad}  {right_str}")

    print(divider)
    bonus_str = f"{GR}{B}Bonus: +35{R}" if bonus else f"{DIM}Bonus: need {63-upper_total} more{R}"
    lower_total = sum(scores.get(k,0) or 0 for k,_,_ in LOWER)
    print(f"  {bonus_str}{'':>18}  {DIM}Lower: {lower_total}{R}\n")

def play_round(scores, round_num):
    dice       = [random.randint(1,6) for _ in range(5)]
    kept       = [False]*5
    rolls_left = 2
    phase      = "roll"
    cursor     = next((i for i,k in enumerate(ALL_KEYS) if scores.get(k) is None), 0)

    draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

    while True:
        ch = getch()

        if ch in ("q", "\x1b", "\x03"):
            return False

        if phase == "roll":
            if ch in ("1","2","3","4","5"):
                kept[int(ch)-1] = not kept[int(ch)-1]
                draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

            elif ch in ("r","R"):
                if rolls_left > 0:
                    dice = roll_dice(dice, kept)
                    rolls_left -= 1
                    draw(dice, kept, rolls_left, scores, cursor, phase, round_num)
                if rolls_left == 0:
                    phase = "choose"
                    draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

            elif ch in ("c","C"):
                phase = "choose"
                draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

        else:  # choose
            if ch == "\x1b[A":  # up
                cursor = max(0, cursor-1)
                while scores.get(ALL_KEYS[cursor]) is not None and cursor > 0:
                    cursor -= 1
                draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

            elif ch == "\x1b[B":  # down
                cursor = min(len(ALL_KEYS)-1, cursor+1)
                while scores.get(ALL_KEYS[cursor]) is not None and cursor < len(ALL_KEYS)-1:
                    cursor += 1
                draw(dice, kept, rolls_left, scores, cursor, phase, round_num)

            elif ch in ("\r", "\n", " "):
                key = ALL_KEYS[cursor]
                if scores.get(key) is None:
                    scores[key] = calc_score(key, dice)
                    return True

    return True

def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎲  Yahtzee{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Roll 5 dice up to 3 times per turn, score in 13 categories.\n")
    print(f"  {DIM}[1-5]{R} keep/unkeep dice   {YL}[R]{R} roll   {MG}[C]{R} go to scorecard\n")
    print(f"  Upper bonus: score ≥63 in Ones–Sixes = {GR}+35 points{R}\n")
    print(f"  {DIM}Any key to start...{R}", end="", flush=True)
    getch()

    scores = {k: None for k,_,_,_ in CATEGORIES}

    for rnd in range(1, 14):
        if not play_round(scores, rnd):
            break

    # Final score
    upper = sum(scores.get(k,0) or 0 for k,_,_ in UPPER)
    lower = sum(scores.get(k,0) or 0 for k,_,_ in LOWER)
    bonus = 35 if upper >= 63 else 0
    total = upper + bonus + lower

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Yahtzee  |  Final Scorecard{R}")
    print(f"{B}{CY}{HR}{R}\n")

    print(f"  {B}UPPER SECTION{R}               {B}LOWER SECTION{R}")
    print(f"  {'─'*26}   {'─'*26}")
    for i in range(max(len(UPPER), len(LOWER))):
        lft = rgt = ""
        if i < len(UPPER):
            k,n,_ = UPPER[i]; v = scores.get(k) or 0
            lft = f"  {n:<14} {GR if v>0 else DIM}{v:>3}{R}"
        if i < len(LOWER):
            k,n,_ = LOWER[i]; v = scores.get(k) or 0
            rgt = f"  {n:<14} {GR if v>0 else DIM}{v:>3}{R}"
        import re as _re
        pad = max(0, 30 - len(_re.sub(r"\033\[[0-9;]*m","",lft)))
        print(f"{lft}{' '*pad}   {rgt}")

    print(f"\n  Upper: {upper}  +  Bonus: {GR if bonus else DIM}{bonus}{R}  +  Lower: {lower}")
    print(f"  {B}TOTAL: {GR}{total}{R}\n")

    try:
        import sys as _s; _s.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        if record("yahtzee", "Best score", total):
            print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
