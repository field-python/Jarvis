#!/usr/bin/env python3
"""roulette.py — Roulette with multiple bet types and chip system"""
import os, sys, random, time, tty, termios, select

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"

HR          = "━" * 52
START_CHIPS = 500

WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,
         5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]

REDS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}

BET_TYPES = [
    ("Red",       "Red numbers",        2),
    ("Black",     "Black numbers",      2),
    ("Odd",       "Odd numbers",        2),
    ("Even",      "Even numbers 1-36",  2),
    ("Low",       "Numbers 1-18",       2),
    ("High",      "Numbers 19-36",      2),
    ("1st Dozen", "Numbers 1-12",       3),
    ("2nd Dozen", "Numbers 13-24",      3),
    ("3rd Dozen", "Numbers 25-36",      3),
    ("Single",    "Pick one number",   36),
]

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
    filled = round(pct * 18)
    color  = GR if chips >= START_CHIPS else (YL if chips >= 100 else RD)
    return f"{color}{'█'*filled}{DIM}{'░'*(18-filled)}{R}  ${chips}"

def num_color(n):
    if n == 0: return f"{GR}{B}0{R}"
    return f"{RD}{B}{n}{R}" if n in REDS else f"{B}{n}{R}"

def spin_animation(result):
    ball = ["◉","○","●","◎"]
    for i in range(16):
        idx = (WHEEL.index(result) + (16-i)) % len(WHEEL)
        shown = WHEEL[idx]
        c = RD if shown in REDS else (GR if shown == 0 else DIM)
        print(f"\r  🎡  {c}{shown:>2}{R}  {ball[i%4]}", end="", flush=True)
        time.sleep(0.05 + i*0.02)
    print(f"\r  🎡  {num_color(result):>10}   ", flush=True)

def check_win(bet_type, single_num, result):
    if bet_type == "Red":      return result in REDS
    if bet_type == "Black":    return result != 0 and result not in REDS
    if bet_type == "Odd":      return result != 0 and result % 2 == 1
    if bet_type == "Even":     return result != 0 and result % 2 == 0
    if bet_type == "Low":      return 1 <= result <= 18
    if bet_type == "High":     return 19 <= result <= 36
    if bet_type == "1st Dozen":return 1 <= result <= 12
    if bet_type == "2nd Dozen":return 13 <= result <= 24
    if bet_type == "3rd Dozen":return 25 <= result <= 36
    if bet_type == "Single":   return result == single_num
    return False

def pick_bet(chips):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎡  Roulette{R}  {DIM}Chips: {chips_bar(chips)}{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  {B}Choose your bet:{R}\n")
    for i, (name, desc, payout) in enumerate(BET_TYPES):
        print(f"  {YL}[{i+1}]{R}  {name:<12} {DIM}{desc:<22}{R}  pays {GR}{payout}×{R}")
    print(f"\n  {YL}[Q]{R}  Quit\n")
    print(f"  > ", end="", flush=True)

    while True:
        ch = getch()
        if ch in ("q","\x1b","\x03"): return None, None, None
        if ch.isdigit() and 1 <= int(ch) <= len(BET_TYPES):
            idx = int(ch) - 1
            break
    bet_type, _, payout = BET_TYPES[idx]

    single_num = None
    if bet_type == "Single":
        os.system("clear")
        print(f"{B}{CY}{HR}{R}")
        print(f"{B}{CY}  Roulette  |  Pick a number (0-36){R}")
        print(f"{B}{CY}{HR}{R}\n")
        print(f"  {DIM}Red: {sorted(REDS)}{R}\n")
        print(f"  Number: ", end="", flush=True)
        import readline
        try:
            n = int(input())
            single_num = max(0, min(36, n))
        except:
            single_num = 7

    # Bet amount
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Roulette  |  {bet_type}{R}  {DIM}(pays {payout}×){R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Chips: {chips_bar(chips)}\n")
    print(f"  {YL}[1-9]{R} × $10   {YL}[Enter]{R} = $10   {YL}[A]{R} = all-in\n")
    print(f"  Bet: ", end="", flush=True)
    ch = getch()
    if ch in ("q","\x1b","\x03"): return None, None, None
    if ch.lower() == "a":
        bet = chips
    elif ch.isdigit() and ch != "0":
        bet = min(int(ch)*10, chips)
    else:
        bet = min(10, chips)
    bet = max(5, bet)

    return bet_type, single_num, bet

def main():
    chips = START_CHIPS
    spins = 0

    while chips >= 5:
        bet_type, single_num, bet = pick_bet(chips)
        if bet_type is None:
            break

        chips -= bet
        result = random.choice(WHEEL)
        spins += 1

        os.system("clear")
        print(f"{B}{CY}{HR}{R}")
        print(f"{B}{CY}  Jarvis  🎡  Roulette{R}  {DIM}Bet: {bet_type} ${bet}{R}")
        print(f"{B}{CY}{HR}{R}\n")
        print(f"  Spinning...\n")
        spin_animation(result)

        won = check_win(bet_type, single_num, result)
        payout = next(p for n,_,p in BET_TYPES if n==bet_type)

        if won:
            winnings = bet * payout
            chips += winnings
            msg = f"\n  {GR}{B}✓ Win! +${winnings}{R}  {DIM}({bet_type}  |  rolled {result}){R}"
        else:
            msg = f"\n  {RD}✗ Lose  -${bet}{R}  {DIM}({bet_type}  |  rolled {result}){R}"

        print(msg)
        print(f"\n  Chips: {chips_bar(chips)}")
        print(f"\n  {DIM}Any key to continue  |  Q to quit{R}", end="", flush=True)
        if getch().lower() in ("q","\x1b","\x03"):
            break

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Roulette  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    delta = chips - START_CHIPS
    sign = "+" if delta >= 0 else ""
    color = GR if delta >= 0 else RD
    print(f"  Spins:       {spins}")
    print(f"  Final chips: {chips_bar(chips)}")
    print(f"  Net result:  {color}{B}{sign}${delta}{R}\n")
    try:
        import sys as _sys; _sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        if delta > 0 and record("roulette", "Best net win ($)", delta):
            print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
