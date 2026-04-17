#!/usr/bin/env python3
"""blackjack.py — Blackjack against the dealer"""
import sys
import os
import random
import tty
import termios
import select

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
RED_S  = "\033[91m"   # hearts / diamonds

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
HR    = "━" * 48


def make_deck():
    d = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(d)
    return d


def card_val(rank):
    if rank in ("J", "Q", "K"): return 10
    if rank == "A":              return 11
    return int(rank)


def hand_total(hand):
    total = sum(card_val(r) for r, _ in hand)
    aces  = sum(1 for r, _ in hand if r == "A")
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total


def fmt_card(rank, suit, hidden=False):
    if hidden:
        return f"{DIM}[??]{RESET}"
    s = f"{RED_S}{suit}{RESET}" if suit in ("♥", "♦") else suit
    return f"{BOLD}[{rank}{s}]{RESET}"


def fmt_hand(hand, hide_idx=None):
    return "  ".join(
        fmt_card(r, s, hidden=(i == hide_idx))
        for i, (r, s) in enumerate(hand)
    )


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


def draw(player, dealer, hide_dealer, msg="", stats=None):
    os.system("clear")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    hdr = f"  Jarvis  |  Blackjack"
    if stats:
        hdr += f"  {DIM}W:{stats['w']} L:{stats['l']} P:{stats['p']}{RESET}{BOLD}{CYAN}"
    print(f"{BOLD}{CYAN}{hdr}{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()

    d_label = (f"{hand_total([dealer[0]])}+?" if hide_dealer
               else str(hand_total(dealer)))
    print(f"  {BOLD}Dealer{RESET}  {fmt_hand(dealer, hide_idx=1 if hide_dealer else None)}"
          f"  {DIM}({d_label}){RESET}")
    print()

    p_total = hand_total(player)
    p_color = RED if p_total > 21 else (GREEN if p_total >= 18 else RESET)
    print(f"  {BOLD}You   {RESET}  {fmt_hand(player)}"
          f"  {DIM}({p_color}{p_total}{RESET}{DIM}){RESET}")
    print()

    if msg:
        print(f"  {msg}")
        print()


def play_hand(deck, stats):
    """Play one hand. Returns True to continue, False to quit."""
    if len(deck) < 15:
        deck[:] = make_deck()

    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    # Natural blackjack
    if hand_total(player) == 21:
        stats["w"] += 1
        draw(player, dealer, False,
             f"{GREEN}{BOLD}★  Blackjack! You win!  ★{RESET}", stats)
        print(f"  {DIM}Any key for next hand  |  Q to quit{RESET}", end="", flush=True)
        return getch().lower() not in ("q", "\x1b", "\x03")

    # Player turn
    while True:
        p_val = hand_total(player)
        if p_val > 21:
            stats["l"] += 1
            draw(player, dealer, True,
                 f"{RED}Bust — over 21.{RESET}", stats)
            print(f"  {DIM}Any key for next hand  |  Q to quit{RESET}", end="", flush=True)
            return getch().lower() not in ("q", "\x1b", "\x03")

        draw(player, dealer, True,
             f"{YELLOW}[H] Hit   [S] Stand   [Q] Quit{RESET}", stats)
        key = getch().lower()
        if key in ("q", "\x1b", "\x03"):
            return False
        if key == "h":
            player.append(deck.pop())
        elif key == "s":
            break

    # Dealer turn — hits on ≤16
    while hand_total(dealer) <= 16:
        dealer.append(deck.pop())

    p_val = hand_total(player)
    d_val = hand_total(dealer)

    if d_val > 21 or p_val > d_val:
        msg = f"{GREEN}{BOLD}You win!{RESET}  {DIM}({p_val} vs {d_val}){RESET}"
        stats["w"] += 1
    elif d_val > p_val:
        msg = f"{RED}Dealer wins.{RESET}  {DIM}({d_val} vs {p_val}){RESET}"
        stats["l"] += 1
    else:
        msg = f"{YELLOW}Push.{RESET}  {DIM}({p_val}){RESET}"
        stats["p"] += 1

    draw(player, dealer, False, msg, stats)
    print(f"  {DIM}Any key for next hand  |  Q to quit{RESET}", end="", flush=True)
    return getch().lower() not in ("q", "\x1b", "\x03")


def main():
    os.system("clear")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Blackjack{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()
    print(f"  Get as close to {BOLD}21{RESET} as possible without going over.")
    print(f"  Dealer hits on 16, stands on 17.")
    print(f"  Natural blackjack ({BOLD}21 in 2 cards{RESET}) wins outright.")
    print()
    print(f"  {YELLOW}[H]{RESET} Hit    {YELLOW}[S]{RESET} Stand    {YELLOW}[Q]{RESET} Quit")
    print()
    print(f"  {DIM}Any key to deal...{RESET}", end="", flush=True)
    getch()

    deck  = make_deck()
    stats = {"w": 0, "l": 0, "p": 0}

    while play_hand(deck, stats):
        pass

    # Final summary
    os.system("clear")
    total = stats["w"] + stats["l"] + stats["p"]
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}  Blackjack  |  Game Over{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()
    print(f"  Hands played:  {total}")
    print(f"  {GREEN}Wins:          {stats['w']}{RESET}")
    print(f"  {RED}Losses:        {stats['l']}{RESET}")
    print(f"  {YELLOW}Pushes:        {stats['p']}{RESET}")
    if total:
        pct = round(stats["w"] / total * 100)
        bar_filled = round(pct / 5)
        bar = f"{GREEN}{'█' * bar_filled}{DIM}{'░' * (20 - bar_filled)}{RESET}"
        print(f"  Win rate:      {bar}  {pct}%")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
