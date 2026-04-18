#!/usr/bin/env python3
"""yahtzee.py — Full Yahtzee with all 13 categories"""
import os, sys, random, tty, termios, select
from collections import Counter

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
HR  = "━" * 52

CATEGORIES = [
    ("ones",   "Ones",          "Sum of all 1s"),
    ("twos",   "Twos",          "Sum of all 2s"),
    ("threes", "Threes",        "Sum of all 3s"),
    ("fours",  "Fours",         "Sum of all 4s"),
    ("fives",  "Fives",         "Sum of all 5s"),
    ("sixes",  "Sixes",         "Sum of all 6s"),
    ("3kind",  "3 of a Kind",   "Sum of all dice"),
    ("4kind",  "4 of a Kind",   "Sum of all dice"),
    ("fhouse", "Full House",    "25 pts"),
    ("sstr",   "Sm. Straight",  "30 pts (4 seq)"),
    ("lstr",   "Lg. Straight",  "40 pts (5 seq)"),
    ("yahtzee","Yahtzee",       "50 pts"),
    ("chance", "Chance",        "Sum of all dice"),
]

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd,1).decode("utf-8","replace")
        if ch == "\x1b":
            r,_,_ = select.select([fd],[],[],0.1)
            if r: os.read(fd,2)
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def roll_dice(dice, kept):
    return [dice[i] if kept[i] else random.randint(1,6) for i in range(5)]

def die_face(n):
    faces = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}
    return faces[n]

def calc_score(key, dice):
    c = Counter(dice)
    s = sum(dice)
    vals = sorted(set(dice))
    counts = sorted(c.values(), reverse=True)

    if key == "ones":   return c.get(1,0)*1
    if key == "twos":   return c.get(2,0)*2
    if key == "threes": return c.get(3,0)*3
    if key == "fours":  return c.get(4,0)*4
    if key == "fives":  return c.get(5,0)*5
    if key == "sixes":  return c.get(6,0)*6
    if key == "3kind":  return s if counts[0]>=3 else 0
    if key == "4kind":  return s if counts[0]>=4 else 0
    if key == "fhouse": return 25 if sorted(counts)==[2,3] else 0
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

def draw(dice, kept, rolls_left, scores, cat_cursor, phase):
    os.system("clear")
    total = sum(v for v in scores.values() if v is not None)
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎲  Yahtzee{R}  {DIM}Score: {total}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    # Dice
    dice_str = "  ".join(
        f"{GR}{die_face(d)}{R}" if kept[i] else f"{B}{die_face(d)}{R}"
        for i, d in enumerate(dice)
    )
    print(f"  {dice_str}\n")
    kept_str = "  ".join(
        f"{GR}[K]{R}" if kept[i] else f"{DIM}[ ]{R}"
        for i in range(5)
    )
    print(f"  {kept_str}   {DIM}Rolls left: {rolls_left}{R}\n")

    if phase == "roll":
        print(f"  {DIM}[1-5] toggle keep   [R] roll   [C] choose category   [Q] quit{R}\n")
    else:
        print(f"  {DIM}[↑↓] navigate   [Enter] select category   [Q] quit{R}\n")

    # Upper section
    upper_total = sum(scores.get(k,0) or 0 for k,_,_ in CATEGORIES[:6])
    bonus = 35 if upper_total >= 63 else 0
    print(f"  {B}Upper Section{R}  {DIM}(need 63 for +35 bonus, have {upper_total}){R}")
    for i, (key, name, desc) in enumerate(CATEGORIES[:6]):
        _draw_cat(i, key, name, desc, dice, scores, cat_cursor, phase)

    print(f"\n  {B}Lower Section{R}")
    for i, (key, name, desc) in enumerate(CATEGORIES[6:]):
        _draw_cat(i+6, key, name, desc, dice, scores, cat_cursor, phase)

    if bonus:
        print(f"\n  {GR}{B}Upper bonus: +35!{R}")
    print()

def _draw_cat(i, key, name, desc, dice, scores, cursor, phase):
    scored = scores.get(key)
    if scored is not None:
        val_str = f"{GR}{scored:>4}{R}"
        arrow = "  "
    else:
        potential = calc_score(key, dice)
        val_str = f"{DIM}{potential:>4}{R}"
        if phase == "choose" and i == cursor:
            arrow = f"{YL}►{R} "
            val_str = f"{YL}{B}{potential:>4}{R}"
        else:
            arrow = "  "
    print(f"  {arrow}{DIM}{i+1:>2}.{R} {name:<16} {DIM}{desc:<20}{R}  {val_str}")

def play_round(scores, round_num):
    dice = [random.randint(1,6) for _ in range(5)]
    kept = [False]*5
    rolls_left = 2

    phase = "roll"
    cat_cursor = next((i for i,(k,_,_) in enumerate(CATEGORIES) if scores.get(k) is None), 0)

    draw(dice, kept, rolls_left, scores, cat_cursor, phase)

    while True:
        ch = getch().lower()

        if ch in ("q","\x1b","\x03"):
            return False

        if phase == "roll":
            if ch in ("1","2","3","4","5"):
                idx = int(ch)-1
                kept[idx] = not kept[idx]
                draw(dice, kept, rolls_left, scores, cat_cursor, phase)

            elif ch == "r":
                if rolls_left > 0:
                    dice = roll_dice(dice, kept)
                    rolls_left -= 1
                    draw(dice, kept, rolls_left, scores, cat_cursor, phase)
                else:
                    phase = "choose"
                    draw(dice, kept, rolls_left, scores, cat_cursor, phase)

            elif ch == "c" or rolls_left == 0:
                phase = "choose"
                draw(dice, kept, rolls_left, scores, cat_cursor, phase)

        else:  # choose
            if ch == "\x1b":
                # arrow keys already consumed by getch returning string
                pass
            # Re-read for arrow simulation via raw chars
            if ch == "k" or ch == "\x1b[a":
                cat_cursor = max(0, cat_cursor-1)
                while scores.get(CATEGORIES[cat_cursor][0]) is not None and cat_cursor > 0:
                    cat_cursor -= 1
                draw(dice, kept, rolls_left, scores, cat_cursor, phase)

            elif ch == "j" or ch == "\x1b[b":
                cat_cursor = min(len(CATEGORIES)-1, cat_cursor+1)
                while scores.get(CATEGORIES[cat_cursor][0]) is not None and cat_cursor < len(CATEGORIES)-1:
                    cat_cursor += 1
                draw(dice, kept, rolls_left, scores, cat_cursor, phase)

            elif ch in ("\r","\n"," "):
                key = CATEGORIES[cat_cursor][0]
                if scores.get(key) is None:
                    scores[key] = calc_score(key, dice)
                    return True

    return True

def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎲  Yahtzee{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Roll 5 dice, keep what you want, score in 13 categories.")
    print(f"  Upper bonus: score ≥63 in ones-sixes → +35 points.\n")
    print(f"  {DIM}[1-5] keep dice   [R] roll   [C] choose category{R}\n")
    print(f"  {DIM}Any key to start...{R}", end="", flush=True)
    getch()

    scores = {k: None for k,_,_ in CATEGORIES}

    for rnd in range(13):
        if not play_round(scores, rnd+1):
            break

    # Final score
    upper = sum(scores.get(k,0) or 0 for k,_,_ in CATEGORIES[:6])
    lower = sum(scores.get(k,0) or 0 for k,_,_ in CATEGORIES[6:])
    bonus = 35 if upper >= 63 else 0
    total = upper + bonus + lower

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Yahtzee  |  Final Score{R}")
    print(f"{B}{CY}{HR}{R}\n")
    for key, name, _ in CATEGORIES:
        v = scores.get(key)
        print(f"  {name:<18} {GR if v else DIM}{v if v is not None else 0}{R}")
    print(f"\n  Upper total: {upper}  {'(+35 bonus!)' if bonus else '(need 63)'}")
    print(f"  {B}TOTAL: {GR}{total}{R}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
