#!/usr/bin/env python3
"""roulette.py — Roulette with full table layout and arrow-key controls"""
import os, sys, random, time, tty, termios, select, readline

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
RDB = "\033[41m"   # red background
BLB = "\033[40m"   # black background
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
INV = "\033[7m"    # inverse for selection

HR          = "━" * 54
START_CHIPS = 500

WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,
         5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]

REDS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}

BET_TYPES = [
    ("Red",          "All red numbers",     2),
    ("Black",        "All black numbers",   2),
    ("Odd",          "All odd numbers",     2),
    ("Even",         "All even numbers",    2),
    ("Low  (1-18)",  "Numbers 1 through 18",2),
    ("High (19-36)", "Numbers 19 through 36",2),
    ("1st Dozen",    "Numbers 1-12",        3),
    ("2nd Dozen",    "Numbers 13-24",       3),
    ("3rd Dozen",    "Numbers 25-36",       3),
    ("Single Number","Choose any number",  36),
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
    filled = round(pct * 16)
    color  = GR if chips >= START_CHIPS else (YL if chips >= 100 else RD)
    return f"{color}{'█'*filled}{DIM}{'░'*(16-filled)}{R} ${chips}"

def num_str(n):
    if n == 0:      return f"{GR}{B} 0 {R}"
    if n in REDS:   return f"{RDB}{B}{n:>2} {R}"
    return f"{BLB}{B}{n:>2} {R}"

def wheel_strip(center_idx, width=11):
    """Return a strip of wheel numbers centered on center_idx."""
    half = width // 2
    parts = []
    for i in range(-half, half+1):
        idx = (center_idx + i) % len(WHEEL)
        n   = WHEEL[idx]
        if i == 0:
            parts.append(f"{B}[{num_str(n)}{B}]{R}")
        else:
            dim_col = RD if n in REDS else (GR if n == 0 else DIM)
            parts.append(f"{dim_col}{n:>2}{R}")
    return "  ".join(parts)

def draw_table(sel, bet, chips, msg="", result=None, spinning_idx=None):
    os.system("clear")
    # Header
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🎰  Roulette{R}  {DIM}Chips:{R} {chips_bar(chips)}")
    print(f"{B}{CY}{HR}{R}\n")

    # Wheel display
    if spinning_idx is not None:
        strip = wheel_strip(spinning_idx)
        print(f"  {DIM}◄{R} {strip} {DIM}►{R}")
        print(f"  {DIM}{'─'*52}{R}\n")
    elif result is not None:
        n = result
        color = RD if n in REDS else (GR if n == 0 else B)
        suit  = "RED" if n in REDS else ("GREEN" if n == 0 else "BLACK")
        print(f"  {DIM}Result:{R}  {color}{B}  {n}  {R}  {DIM}({suit}){R}")
        print(f"  {DIM}{'─'*52}{R}\n")
    else:
        print(f"  {DIM}Place your bet then press Enter to spin{R}")
        print(f"  {DIM}{'─'*52}{R}\n")

    # Bet type menu
    print(f"  {'BET TYPE':<24} {'PAYS':>5}   {'DESCRIPTION'}")
    print(f"  {'─'*52}")
    for i, (name, desc, pays) in enumerate(BET_TYPES):
        pay_str = f"{GR}{pays}×{R}"
        if i == sel:
            print(f"  {YL}▶{R} {B}{name:<22}{R} {pay_str:>12}   {DIM}{desc}{R}")
        else:
            print(f"  {DIM}  {name:<22}  {pays}×          {desc}{R}")
    print()

    # Bet amount
    bet_color = YL if bet <= 50 else (RD if bet >= 200 else GR)
    print(f"  Bet: {bet_color}{B}${bet}{R}  {DIM}[←→] adjust{R}")
    print()

    # Message / controls
    if msg:
        print(f"  {msg}\n")
    else:
        print(f"  {DIM}[↑↓] select bet type   [←→] adjust bet amount{R}")
        print(f"  {YL}[Enter]{R} Spin   {YL}[Q]{R} Quit\n")

def check_win(bet_type, single_num, result):
    n = bet_type
    if n == "Red":           return result in REDS
    if n == "Black":         return result != 0 and result not in REDS
    if n == "Odd":           return result != 0 and result % 2 == 1
    if n == "Even":          return result != 0 and result % 2 == 0
    if n == "Low  (1-18)":   return 1 <= result <= 18
    if n == "High (19-36)":  return 19 <= result <= 36
    if n == "1st Dozen":     return 1 <= result <= 12
    if n == "2nd Dozen":     return 13 <= result <= 24
    if n == "3rd Dozen":     return 25 <= result <= 36
    if n == "Single Number": return result == single_num
    return False

def pick_single_number():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Roulette  |  Pick a Single Number (0-36){R}")
    print(f"{B}{CY}{HR}{R}\n")

    # Show the numbers in a grid
    print(f"  {GR}{B} 0 {R}  (green)\n")
    for row in range(3, 0, -1):
        line = "  "
        for col in range(1, 13):
            n = (col - 1) * 3 + row
            if n <= 36:
                c = RD if n in REDS else B
                line += f"{c}{n:>2}{R} "
        print(line)
    print()

    sys.stdout.write("  Number (0-36): ")
    sys.stdout.flush()
    # restore terminal for normal input
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        pass
    try:
        n = int(input())
        return max(0, min(36, n))
    except Exception:
        return 7

def spin_animation(result, chips, sel, bet):
    """Animate the wheel spinning using overwrite-in-place."""
    target_idx = WHEEL.index(result)
    total_steps = 30
    start_idx   = random.randint(0, len(WHEEL)-1)

    for step in range(total_steps):
        # Ease in: slow start, slow end
        t = step / total_steps
        speed = max(1, int(6 * (1 - (2*t-1)**2) + 1))  # parabolic ease
        idx = (start_idx + step * 2) % len(WHEEL)

        # Last few steps: lock toward target
        if step >= total_steps - 8:
            remaining = total_steps - step
            idx = (target_idx - remaining) % len(WHEEL)

        sys.stdout.write("\033[H")
        sys.stdout.flush()

        # Reprint header + wheel
        print(f"{B}{CY}{HR}{R}")
        print(f"{B}{CY}  Jarvis  🎰  Roulette{R}  {DIM}Chips:{R} {chips_bar(chips)}")
        print(f"{B}{CY}{HR}{R}\n")
        strip = wheel_strip(idx)
        print(f"  {DIM}◄{R} {strip} {DIM}►{R}")
        print(f"  {DIM}{'─'*52}{R}\n")

        # Static bet list below (no reprint — just pad)
        delay = 0.03 + (step / total_steps) * 0.12
        time.sleep(delay)

def main():
    chips    = START_CHIPS
    spins    = 0
    sel      = 0      # selected bet type index
    bet      = 10
    single   = None

    draw_table(sel, bet, chips)

    while chips >= 5:
        ch = getch()

        if ch in ("q", "\x1b", "\x03"):
            break

        elif ch == "\x1b[A":  # up
            sel = (sel - 1) % len(BET_TYPES)
            draw_table(sel, bet, chips)

        elif ch == "\x1b[B":  # down
            sel = (sel + 1) % len(BET_TYPES)
            draw_table(sel, bet, chips)

        elif ch == "\x1b[C":  # right — increase bet
            bet = min(bet + 10, chips, 500)
            draw_table(sel, bet, chips)

        elif ch == "\x1b[D":  # left — decrease bet
            bet = max(5, bet - 10)
            draw_table(sel, bet, chips)

        elif ch in ("\r", "\n", " "):
            bet_type = BET_TYPES[sel][0]
            payout   = BET_TYPES[sel][2]

            # Pick single number if needed
            if bet_type == "Single Number":
                single = pick_single_number()

            actual_bet = min(bet, chips)
            chips -= actual_bet
            result = random.choice(WHEEL)
            spins += 1

            # Draw initial frame then animate
            os.system("clear")
            draw_table(sel, actual_bet, chips)
            spin_animation(result, chips, sel, actual_bet)

            # Show result
            won = check_win(bet_type, single, result)
            if won:
                winnings = actual_bet * payout
                chips   += winnings
                n_str    = f"{RD if result in REDS else (GR if result==0 else B)}{B}{result}{R}"
                msg = f"{GR}{B}✓  WIN! +${winnings}{R}  {DIM}Rolled {n_str}  |  {bet_type}  pays {payout}×{R}"
            else:
                n_str = f"{RD if result in REDS else (GR if result==0 else B)}{B}{result}{R}"
                msg = f"{RD}✗  Lose  −${actual_bet}{R}  {DIM}Rolled {n_str}  |  {bet_type}{R}"

            draw_table(sel, actual_bet, chips, msg=msg, result=result)
            print(f"  {DIM}Any key for next spin  |  Q to quit{R}", end="", flush=True)

            if getch().lower() in ("q", "\x1b", "\x03"):
                break

            draw_table(sel, bet, chips)

    # Summary
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Roulette  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    delta = chips - START_CHIPS
    sign  = "+" if delta >= 0 else ""
    color = GR if delta >= 0 else RD
    print(f"  Spins:       {spins}")
    print(f"  Final chips: {chips_bar(chips)}")
    print(f"  Net result:  {color}{B}{sign}${delta}{R}\n")
    try:
        import sys as _s; _s.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
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
