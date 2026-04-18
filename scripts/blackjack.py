#!/usr/bin/env python3
"""blackjack.py — Blackjack with split, double down, and chips"""
import os, sys, random, tty, termios, select

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
RS  = "\033[91m"  # red suits

SUITS = ["♠","♥","♦","♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
HR    = "━" * 52
START_CHIPS = 500
MIN_BET     = 5


def make_deck():
    d = [(r,s) for s in SUITS for r in RANKS]
    random.shuffle(d)
    return d

def card_val(rank):
    if rank in ("J","Q","K"): return 10
    if rank == "A":            return 11
    return int(rank)

def hand_total(hand):
    total = sum(card_val(r) for r,_ in hand)
    aces  = sum(1 for r,_ in hand if r=="A")
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total

def is_pair(hand):
    return len(hand) == 2 and card_val(hand[0][0]) == card_val(hand[1][0])

def is_blackjack(hand):
    return len(hand) == 2 and hand_total(hand) == 21

def fmt_card(rank, suit, hidden=False):
    if hidden: return f"{DIM}[??]{R}"
    s = f"{RS}{suit}{R}" if suit in ("♥","♦") else suit
    return f"{B}[{rank}{s}]{R}"

def fmt_hand(hand, hide_idx=None):
    return "  ".join(fmt_card(r,s, i==hide_idx) for i,(r,s) in enumerate(hand))

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

def chips_bar(chips):
    pct   = min(chips / START_CHIPS, 1.0)
    filled = round(pct * 20)
    color  = GR if chips >= START_CHIPS else (YL if chips >= 200 else RD)
    return f"{color}{'█'*filled}{DIM}{'░'*(20-filled)}{R}  ${chips}"

def draw_table(hands, bets, active, dealer, hide_dealer, msg="", chips=0, bet=0):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ♠  Blackjack{R}  {DIM}Chips: {chips_bar(chips)}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    # Dealer
    d_label = f"{hand_total([dealer[0]])}+?" if hide_dealer else str(hand_total(dealer))
    print(f"  {B}Dealer{R}  {fmt_hand(dealer, hide_idx=1 if hide_dealer else None)}  {DIM}({d_label}){R}\n")

    # Player hand(s)
    for i, hand in enumerate(hands):
        tot   = hand_total(hand)
        color = RD if tot > 21 else (GR if tot >= 18 else R)
        label = f"{B}You   {R}" if len(hands)==1 else (f"{B}Hand {i+1}{R}")
        arrow = f" {YL}◄{R}" if i == active and len(hands) > 1 else ""
        print(f"  {label}  {fmt_hand(hand)}  {DIM}({color}{tot}{R}{DIM}){R}  {DIM}Bet:${bets[i]}{R}{arrow}")
    print()

    if msg:
        print(f"  {msg}\n")

def get_bet(chips):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ♠  Blackjack{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Chips: {chips_bar(chips)}\n")
    print(f"  {DIM}Min bet: ${MIN_BET}{R}")
    print(f"  {YL}[Enter]{R} = $10   {YL}[1-9]{R} × $10   {YL}[A]{R} = all-in   {YL}[Q]{R} = quit\n")
    print(f"  Bet: ", end="", flush=True)

    bet = 0
    while True:
        ch = getch()
        if ch in ("q", "\x1b", "\x03"):
            return None
        if ch == "\r" or ch == "\n":
            bet = min(10, chips)
            break
        if ch.lower() == "a":
            bet = chips
            break
        if ch.isdigit() and ch != "0":
            bet = min(int(ch) * 10, chips)
            break

    bet = max(MIN_BET, min(bet, chips))
    return bet

def play_hand(deck, chips):
    if len(deck) < 20:
        deck[:] = make_deck()

    bet = get_bet(chips)
    if bet is None:
        return chips, False

    hands  = [[deck.pop(), deck.pop()]]
    bets   = [bet]
    dealer = [deck.pop(), deck.pop()]
    results = []

    # Natural blackjack check
    if is_blackjack(hands[0]):
        payout = int(bet * 1.5)
        draw_table(hands, bets, 0, dealer, False,
                   f"{GR}{B}★ Blackjack! +${payout} ★{R}", chips + payout, bet)
        print(f"  {DIM}Any key for next hand  |  Q to quit{R}", end="", flush=True)
        cont = getch().lower() not in ("q","\x1b","\x03")
        return chips + payout, cont

    # Play each hand
    h = 0
    while h < len(hands):
        hand = hands[h]
        b    = bets[h]
        first_action = True

        while True:
            tot = hand_total(hand)

            if tot > 21:
                results.append(("bust", h))
                break
            if tot == 21:
                results.append(("stand", h))
                break

            # Build prompt
            opts = [f"{YL}[H]{R} Hit", f"{YL}[S]{R} Stand"]
            can_double = first_action and chips - sum(bets) >= b
            can_split  = first_action and is_pair(hand) and chips - sum(bets) >= b and len(hands) < 4
            if can_double: opts.append(f"{YL}[D]{R} Double")
            if can_split:  opts.append(f"{YL}[P]{R} Split")
            opts.append(f"{YL}[Q]{R} Quit")

            draw_table(hands, bets, h, dealer, True, "   ".join(opts), chips, bet)
            key = getch().lower()

            if key in ("q","\x1b","\x03"):
                return chips - sum(bets), False

            if key == "h":
                hand.append(deck.pop())
                first_action = False

            elif key == "s":
                results.append(("stand", h))
                break

            elif key == "d" and can_double:
                bets[h] *= 2
                hand.append(deck.pop())
                draw_table(hands, bets, h, dealer, True,
                           f"{YL}Doubled down!{R}  Drew: {fmt_card(*hand[-1])}", chips, bet)
                results.append(("stand", h))
                break

            elif key == "p" and can_split:
                # Split the pair into two hands
                card2 = hand.pop()
                hands.insert(h+1, [card2, deck.pop()])
                bets.insert(h+1, b)
                hand.append(deck.pop())
                first_action = True  # can double after split

        h += 1

    # Dealer plays
    while hand_total(dealer) <= 16:
        dealer.append(deck.pop())

    d_val = hand_total(dealer)

    # Settle all hands
    total_delta = 0
    result_msgs = []
    for i, hand in enumerate(hands):
        p_val = hand_total(hand)
        b     = bets[i]
        if p_val > 21:
            total_delta -= b
            result_msgs.append(f"{RD}Hand {i+1}: Bust  -${b}{R}")
        elif d_val > 21 or p_val > d_val:
            total_delta += b
            result_msgs.append(f"{GR}Hand {i+1}: Win   +${b}{R}")
        elif p_val < d_val:
            total_delta -= b
            result_msgs.append(f"{RD}Hand {i+1}: Lose  -${b}{R}")
        else:
            result_msgs.append(f"{YL}Hand {i+1}: Push  $0{R}")

    sign = "+" if total_delta >= 0 else ""
    color = GR if total_delta > 0 else (RD if total_delta < 0 else YL)
    summary = f"{color}{B}{sign}${total_delta}{R}  {DIM}Dealer: {d_val}{R}"
    msg = "   ".join(result_msgs) + f"\n\n  {summary}"

    draw_table(hands, bets, -1, dealer, False, msg, chips + total_delta, bet)
    print(f"\n  {DIM}Any key for next hand  |  Q to quit{R}", end="", flush=True)
    cont = getch().lower() not in ("q","\x1b","\x03")
    return chips + total_delta, cont


def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ♠  Blackjack{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Get closest to {B}21{R} without going over.")
    print(f"  Dealer hits on ≤16. Blackjack pays 3:2.\n")
    print(f"  {YL}[H]{R} Hit  {YL}[S]{R} Stand  {YL}[D]{R} Double  {YL}[P]{R} Split  {YL}[Q]{R} Quit\n")
    print(f"  Starting chips: {B}${START_CHIPS}{R}\n")
    print(f"  {DIM}Any key to start...{R}", end="", flush=True)
    getch()

    deck  = make_deck()
    chips = START_CHIPS
    hands_played = 0

    while chips >= MIN_BET:
        chips, cont = play_hand(deck, chips)
        hands_played += 1
        if not cont:
            break

    # Summary
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Blackjack  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Hands played:  {hands_played}")
    delta = chips - START_CHIPS
    sign  = "+" if delta >= 0 else ""
    color = GR if delta >= 0 else RD
    print(f"  Final chips:   {chips_bar(chips)}")
    print(f"  Net result:    {color}{B}{sign}${delta}{R}\n")
    if chips < MIN_BET:
        print(f"  {RD}Busted out!{R}\n")
    try:
        import sys as _sys; _sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        new1 = record("blackjack", "Best chip total ($)", chips)
        if delta > 0: record("blackjack", "Best net win ($)", delta)
        if new1: print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
