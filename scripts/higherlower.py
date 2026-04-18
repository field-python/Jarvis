#!/usr/bin/env python3
"""higherlower.py — Higher or Lower card game"""
import os, sys, random, tty, termios, select

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
RS  = "\033[91m"

HR    = "━" * 44
SUITS = ["♠","♥","♦","♣"]
RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
VALUES = {r: i for i, r in enumerate(RANKS)}

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

def make_deck():
    d = [(r,s) for s in SUITS for r in RANKS]
    random.shuffle(d)
    return d

def fmt_card(rank, suit, hidden=False):
    if hidden: return f"{DIM}┌───┐\n  │ {B}???{R}{DIM} │\n  └───┘{R}"
    s = f"{RS}{suit}{R}" if suit in ("♥","♦") else suit
    pad = " " if rank != "10" else ""
    return f"┌───┐\n  │{B}{pad}{rank}{s}{R} │\n  └───┘"

def streak_bar(streak):
    filled = min(streak, 10)
    color  = GR if streak >= 5 else (YL if streak >= 3 else CY)
    return f"{color}{'▮'*filled}{DIM}{'▯'*(10-filled)}{R}  {streak}"

def draw(current, streak, score, msg="", show_next=None):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🃏  Higher or Lower{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Streak: {streak_bar(streak)}   Score: {B}{score}{R}\n")

    r, s = current
    s_str = f"{RS}{s}{R}" if s in ("♥","♦") else s
    pad   = " " if r != "10" else ""
    print(f"  Current card:")
    print(f"  ┌───┐")
    print(f"  │{B}{pad}{r}{s_str}{R} │")
    print(f"  └───┘\n")

    if show_next:
        nr, ns = show_next
        ns_str = f"{RS}{ns}{R}" if ns in ("♥","♦") else ns
        npad   = " " if nr != "10" else ""
        print(f"  Next card:")
        print(f"  ┌───┐")
        print(f"  │{B}{npad}{nr}{ns_str}{R} │")
        print(f"  └───┘\n")
    else:
        print(f"  Next card:")
        print(f"  ┌───┐")
        print(f"  │{DIM} ??? {R}│")
        print(f"  └───┘\n")

    if msg:
        print(f"  {msg}\n")
    else:
        print(f"  Is the next card {YL}[H]{R}igher or {YL}[L]{R}ower?  {YL}[Q]{R} Quit\n")
        print(f"  {DIM}Same value = counts as correct{R}\n")

def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🃏  Higher or Lower{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Guess if the next card is higher or lower.")
    print(f"  Same value counts as correct. Build your streak!\n")
    print(f"  {YL}[H]{R} Higher   {YL}[L]{R} Lower   {YL}[Q]{R} Quit\n")
    print(f"  {DIM}Any key to start...{R}", end="", flush=True)
    getch()

    best_streak = 0
    play_again  = True

    while play_again:
        deck    = make_deck()
        current = deck.pop()
        streak  = 0
        score   = 0

        draw(current, streak, score)

        while len(deck) > 0:
            ch = getch().lower()
            if ch in ("q", "\x1b", "\x03"):
                play_again = False
                break

            if ch not in ("h", "l"):
                continue

            next_card = deck.pop()
            cur_val   = VALUES[current[0]]
            nxt_val   = VALUES[next_card[0]]

            correct = (ch == "h" and nxt_val >= cur_val) or \
                      (ch == "l" and nxt_val <= cur_val)

            if correct:
                streak += 1
                bonus   = streak * 10
                score  += bonus
                best_streak = max(best_streak, streak)
                msg = f"{GR}{B}✓ Correct! +{bonus} pts{R}  {DIM}(streak bonus){R}"
            else:
                msg = f"{RD}✗ Wrong!{R}  {DIM}Streak lost ({streak}){R}"
                draw(current, streak, score, msg, show_next=next_card)
                import time; time.sleep(1.5)
                streak = 0

            draw(next_card, streak, score, msg if correct else "")
            current = next_card

            if not correct:
                draw(current, streak, score)

        if play_again:
            # End of deck
            os.system("clear")
            print(f"{B}{CY}{HR}{R}")
            print(f"{B}  Higher or Lower  |  Deck finished!{R}")
            print(f"{B}{CY}{HR}{R}\n")
            print(f"  Score:       {B}{score}{R}")
            print(f"  Best streak: {streak_bar(best_streak)}\n")
            print(f"  {YL}[Enter]{R} Play again   {YL}[Q]{R} Quit\n")
            ch = getch().lower()
            if ch in ("q", "\x1b", "\x03"):
                play_again = False

    # Final
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Higher or Lower  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Final score:  {B}{score}{R}")
    print(f"  Best streak:  {streak_bar(best_streak)}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
