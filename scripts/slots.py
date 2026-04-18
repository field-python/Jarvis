#!/usr/bin/env python3
"""slots.py — Slot machine with chips"""
import os, sys, random, time, tty, termios, select

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
MG  = "\033[95m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"

HR          = "━" * 44
START_CHIPS = 200
REELS = ["🍒","🍋","🍊","🍇","⭐","🔔","💎","7️⃣ "]

# (symbol, weight, payout_3x, payout_2x)
SYMBOLS = [
    ("🍒", 30, 5,   2),
    ("🍋", 25, 8,   2),
    ("🍊", 20, 10,  0),
    ("🍇", 15, 15,  0),
    ("⭐", 6,  30,  0),
    ("🔔", 3,  75,  0),
    ("💎", 1,  200, 0),
]
WEIGHTS  = [s[1] for s in SYMBOLS]
SYM_LIST = [s[0] for s in SYMBOLS]

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

def chips_bar(chips):
    pct    = min(chips / START_CHIPS, 2.0) / 2
    filled = round(pct * 20)
    color  = GR if chips >= START_CHIPS else (YL if chips >= 50 else RD)
    return f"{color}{'█'*filled}{DIM}{'░'*(20-filled)}{R}  ${chips}"

def spin():
    return random.choices(SYM_LIST, weights=WEIGHTS, k=3)

def calc_payout(result, bet):
    counts = {s: result.count(s) for s in set(result)}
    for sym, _, pay3, pay2 in SYMBOLS:
        if counts.get(sym, 0) == 3:
            return bet * pay3, f"3× {sym}  {GR}×{pay3}{R}"
        if counts.get(sym, 0) == 2 and pay2:
            return bet * pay2, f"2× {sym}  {YL}×{pay2}{R}"
    return 0, f"{RD}No match{R}"

def draw(result=None, msg="", chips=0, bet=0, reel=None):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎰  Slots{R}  {DIM}Chips: {chips_bar(chips)}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    # Reel — always at top
    print(f"  {DIM}┏━━━━━━━━━━━━━━━┓{R}")
    if reel:
        print(f"  {B}┃  {reel[0]}  {reel[1]}  {reel[2]}  ┃{R}")
    elif result:
        print(f"  {B}┃  {result[0]}  {result[1]}  {result[2]}  ┃{R}")
    else:
        print(f"  ┃ {DIM}?   ?   ?{R}  ┃")
    print(f"  {DIM}┗━━━━━━━━━━━━━━━┛{R}\n")

    print(f"  {DIM}Paytable:{R}")
    for sym, _, pay3, pay2 in SYMBOLS:
        line = f"  {sym}  3×={GR}${pay3*bet}{R}"
        if pay2: line += f"  2×={YL}${pay2*bet}{R}"
        print(line)
    print()

    if msg:
        print(f"  {msg}\n")

    print(f"  Bet: {B}${bet}{R}  {DIM}[↑↓] change{R}")
    print(f"  {YL}[Space/Enter]{R} Spin   {YL}[Q]{R} Quit\n")


def animate_spin(chips, bet):
    for _ in range(10):
        reel = [random.choice(SYM_LIST) for _ in range(3)]
        draw(reel=reel, chips=chips, bet=bet)
        time.sleep(0.07)

def main():
    chips = START_CHIPS
    bet   = 10
    result = None
    msg    = ""

    draw(result, f"{DIM}Press Space to spin!{R}", chips, bet)

    while chips > 0:
        ch = getch()

        if ch in ("q", "\x1b", "\x03"):
            break

        if ch == "\x1b[A" or ch == "k":  # up
            bet = min(bet + 5, chips, 100)
            draw(result, msg, chips, bet)
            continue

        if ch == "\x1b[B" or ch == "j":  # down
            bet = max(5, bet - 5)
            draw(result, msg, chips, bet)
            continue

        if ch in (" ", "\r", "\n"):
            if bet > chips:
                bet = chips

            chips -= bet
            animate_spin(chips, bet)

            result = spin()
            payout, msg_txt = calc_payout(result, bet)
            chips += payout

            if payout > 0:
                msg = f"{GR}{B}+${payout}{R}  {msg_txt}"
            else:
                msg = f"{RD}-${bet}{R}  {msg_txt}"

            draw(result, msg, chips, bet)

            if chips < 5:
                print(f"  {RD}Out of chips!{R}\n")
                time.sleep(1.5)
                break

    # Summary
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Slots  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    delta = chips - START_CHIPS
    sign  = "+" if delta >= 0 else ""
    color = GR if delta >= 0 else RD
    print(f"  Final chips: {chips_bar(chips)}")
    print(f"  Net result:  {color}{B}{sign}${delta}{R}\n")
    try:
        import sys as _sys; _sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        if record("slots", "Best chip total ($)", chips) or (delta > 0 and record("slots", "Best net win ($)", delta)):
            print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
