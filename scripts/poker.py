#!/usr/bin/env python3
"""poker.py — Texas Hold'em vs Jarvis AI with chips"""
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
RS  = "\033[91m"

HR          = "━" * 52
START_CHIPS = 500
BLIND       = 10

SUITS = ["♠","♥","♦","♣"]
RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
RANK_VAL = {r:i for i,r in enumerate(RANKS)}

def make_deck():
    d = [(r,s) for s in SUITS for r in RANKS]
    random.shuffle(d)
    return d

def fmt_card(r, s, hidden=False):
    if hidden: return f"{DIM}[??]{R}"
    sc = f"{RS}{s}{R}" if s in ("♥","♦") else s
    return f"{B}[{r}{sc}]{R}"

def fmt_hand(hand, hidden=False):
    return "  ".join(fmt_card(r,s,hidden) for r,s in hand)

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd,1).decode("utf-8","replace")
        if ch == "\x1b":
            r2,_,_ = select.select([fd],[],[],0.1)
            if r2: os.read(fd,2)
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ── Hand evaluation ────────────────────────────────────────────────────────────
def best_hand(cards):
    from itertools import combinations
    best = None
    for combo in combinations(cards, 5):
        s = score_hand(list(combo))
        if best is None or s > best:
            best = s
    return best

def score_hand(hand):
    ranks = sorted([RANK_VAL[r] for r,_ in hand], reverse=True)
    suits = [s for _,s in hand]
    c     = Counter(ranks)
    counts= sorted(c.values(), reverse=True)
    flush = len(set(suits))==1
    straight = (len(set(ranks))==5 and ranks[0]-ranks[4]==4) or ranks==[12,3,2,1,0]
    if straight and ranks[0]==3 and 12 in ranks:
        ranks = [3,2,1,0,-1]

    if flush and straight:  return (8, ranks)
    if counts[0]==4:        return (7, ranks)
    if counts[:2]==[3,2]:   return (6, ranks)
    if flush:               return (5, ranks)
    if straight:            return (4, ranks)
    if counts[0]==3:        return (3, ranks)
    if counts[:2]==[2,2]:   return (2, ranks)
    if counts[0]==2:        return (1, ranks)
    return (0, ranks)

HAND_NAMES = ["High Card","One Pair","Two Pair","Three of a Kind",
               "Straight","Flush","Full House","Four of a Kind","Straight Flush"]

def hand_name(cards):
    s = best_hand(cards)
    return HAND_NAMES[s[0]] if s else "?"

def chips_bar(chips, total=START_CHIPS):
    pct    = min(chips / total, 2.0)/2
    filled = round(pct*16)
    color  = GR if chips >= total else (YL if chips >= total//4 else RD)
    return f"{color}{'█'*filled}{DIM}{'░'*(16-filled)}{R} ${chips}"

# ── AI decision ────────────────────────────────────────────────────────────────
def ai_action(ai_hand, community, pot, to_call, ai_chips, stage):
    all_cards = ai_hand + community
    sc = best_hand(all_cards)[0] if len(all_cards)>=5 else 0
    # Rough hand strength pre-flop
    rv = [RANK_VAL[r] for r,_ in ai_hand]
    pre = (max(rv) + (5 if rv[0]==rv[1] else 0)) / 14.0
    strength = sc/8.0 if community else pre

    if to_call == 0:
        if strength > 0.5: return "raise", min(pot, ai_chips)
        return "check", 0
    if strength > 0.7:  return "raise", min(to_call*2, ai_chips)
    if strength > 0.35: return "call",  min(to_call, ai_chips)
    if random.random() < 0.15: return "call", min(to_call, ai_chips)
    return "fold", 0

# ── Draw ───────────────────────────────────────────────────────────────────────
def draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
               stage, msg="", show_ai=False, p_bet=0, ai_bet=0):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ♠  Texas Hold'em{R}  {DIM}Pot: ${pot}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    print(f"  {B}Jarvis{R}  {fmt_hand(ai_hand, hidden=not show_ai)}  "
          f"{DIM}(${ai_chips}){R}"
          + (f"  {DIM}bet ${ai_bet}{R}" if ai_bet else ""))
    print()

    if community:
        comm_str = "  ".join(fmt_card(r,s) for r,s in community)
        label = {"flop":"Flop","turn":"Turn","river":"River"}.get(stage, stage)
        print(f"  {DIM}{label}:{R}  {comm_str}")
        if show_ai and len(community)>=3:
            print(f"  {DIM}Jarvis: {hand_name(ai_hand+community)}{R}")
    else:
        print(f"  {DIM}Waiting for community cards...{R}")
    print()

    print(f"  {B}You   {R}  {fmt_hand(p_hand)}  "
          f"{DIM}(${p_chips}){R}"
          + (f"  {DIM}bet ${p_bet}{R}" if p_bet else ""))
    if len(p_hand)+len(community)>=5:
        print(f"  {DIM}Your hand: {hand_name(p_hand+community)}{R}")
    print()

    if msg:
        print(f"  {msg}\n")

def player_action(p_chips, ai_chips, pot, to_call, p_hand, ai_hand, community, stage, p_bet, ai_bet):
    opts = []
    if to_call == 0:
        opts = [f"{YL}[C]{R} Check", f"{YL}[R]{R} Raise", f"{YL}[F]{R} Fold"]
    else:
        call_amt = min(to_call, p_chips)
        opts = [f"{YL}[C]{R} Call ${call_amt}", f"{YL}[R]{R} Raise", f"{YL}[F]{R} Fold"]

    draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
               stage, "   ".join(opts), p_bet=p_bet, ai_bet=ai_bet)

    while True:
        ch = getch().lower()
        if ch in ("q","\x1b","\x03"): return "quit", 0
        if ch == "f": return "fold", 0
        if ch == "c":
            amt = min(to_call, p_chips)
            return "call", amt
        if ch == "r":
            raise_amt = min(max(to_call*2, BLIND*2), p_chips)
            return "raise", raise_amt

# ── Play one hand ──────────────────────────────────────────────────────────────
def play_hand(p_chips, ai_chips, hands_played):
    deck = make_deck()
    p_hand  = [deck.pop(), deck.pop()]
    ai_hand = [deck.pop(), deck.pop()]

    # Blinds
    p_chips  -= BLIND; ai_chips -= BLIND
    pot = BLIND * 2
    p_bet = BLIND; ai_bet = BLIND

    community = []
    stages = ["pre-flop","flop","turn","river"]

    for stage in stages:
        if stage == "flop":
            community += [deck.pop(), deck.pop(), deck.pop()]
        elif stage in ("turn","river"):
            community.append(deck.pop())

        to_call_p  = max(0, ai_bet - p_bet)
        to_call_ai = max(0, p_bet - ai_bet)

        # Player acts first (except pre-flop AI acts first as "dealer")
        if stage == "pre-flop":
            # AI acts first pre-flop
            action, amt = ai_action(ai_hand, community, pot, to_call_ai, ai_chips, stage)
            if action == "fold":
                draw_table(p_hand, ai_hand, community, pot+ai_bet, p_chips, ai_chips,
                           stage, f"{GR}{B}Jarvis folds — You win! +${pot}{R}", show_ai=True,
                           p_bet=p_bet, ai_bet=ai_bet)
                print(f"\n  {DIM}Any key...{R}", end="", flush=True); getch()
                return p_chips + pot, ai_chips, True
            elif action == "raise":
                ai_chips -= amt; ai_bet += amt; pot += amt
                draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
                           stage, f"{YL}Jarvis raises ${amt}{R}", p_bet=p_bet, ai_bet=ai_bet)
            elif action == "call":
                ai_chips -= amt; pot += amt; ai_bet += amt
            to_call_p = max(0, ai_bet - p_bet)

        action, amt = player_action(p_chips, ai_chips, pot, to_call_p,
                                    p_hand, ai_hand, community, stage, p_bet, ai_bet)
        if action == "quit": return p_chips, ai_chips, False
        if action == "fold":
            draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
                       stage, f"{RD}You fold — Jarvis wins! -${p_bet}{R}", show_ai=True,
                       p_bet=p_bet, ai_bet=ai_bet)
            print(f"\n  {DIM}Any key...{R}", end="", flush=True); getch()
            return p_chips, ai_chips + pot, True
        elif action == "call":
            p_chips -= amt; pot += amt; p_bet += amt
        elif action == "raise":
            p_chips -= amt; pot += amt; p_bet += amt
            # AI responds
            to_call_ai = max(0, p_bet - ai_bet)
            action2, amt2 = ai_action(ai_hand, community, pot, to_call_ai, ai_chips, stage)
            if action2 == "fold":
                draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
                           stage, f"{GR}{B}Jarvis folds — You win! +${pot}{R}", show_ai=True,
                           p_bet=p_bet, ai_bet=ai_bet)
                print(f"\n  {DIM}Any key...{R}", end="", flush=True); getch()
                return p_chips + pot, ai_chips, True
            elif action2 in ("call","raise"):
                ai_chips -= min(to_call_ai, ai_chips)
                pot += min(to_call_ai, ai_chips)

        if stage != "pre-flop":
            p_bet = 0; ai_bet = 0

    # Showdown
    p_score  = best_hand(p_hand + community)
    ai_score = best_hand(ai_hand + community)
    p_name   = hand_name(p_hand + community)
    ai_name  = hand_name(ai_hand + community)

    if p_score > ai_score:
        msg = f"{GR}{B}You win! +${pot}{R}  {DIM}{p_name} beats {ai_name}{R}"
        p_chips += pot
    elif ai_score > p_score:
        msg = f"{RD}Jarvis wins! -${pot//2}{R}  {DIM}{ai_name} beats {p_name}{R}"
        ai_chips += pot
    else:
        msg = f"{YL}Split pot!{R}  {DIM}{p_name}{R}"
        p_chips += pot//2; ai_chips += pot//2

    draw_table(p_hand, ai_hand, community, pot, p_chips, ai_chips,
               "river", msg, show_ai=True)
    print(f"\n  {DIM}Any key for next hand  |  Q to quit{R}", end="", flush=True)
    cont = getch().lower() not in ("q","\x1b","\x03")
    return p_chips, ai_chips, cont

def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ♠  Texas Hold'em{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Heads-up poker vs Jarvis. Blind: ${BLIND}. Start: ${START_CHIPS} each.\n")
    print(f"  {YL}[C]{R} Check/Call   {YL}[R]{R} Raise   {YL}[F]{R} Fold   {YL}[Q]{R} Quit\n")
    print(f"  {DIM}Any key to deal...{R}", end="", flush=True)
    getch()

    p_chips  = START_CHIPS
    ai_chips = START_CHIPS
    hands    = 0

    while p_chips >= BLIND and ai_chips >= BLIND:
        p_chips, ai_chips, cont = play_hand(p_chips, ai_chips, hands)
        hands += 1
        if not cont: break
        # Refill AI if busted (so game continues)
        if ai_chips < BLIND:
            ai_chips = START_CHIPS

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Poker  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    delta = p_chips - START_CHIPS
    sign  = "+" if delta >= 0 else ""
    color = GR if delta >= 0 else RD
    print(f"  Hands played: {hands}")
    print(f"  Final chips:  {chips_bar(p_chips)}")
    print(f"  Net result:   {color}{B}{sign}${delta}{R}\n")
    try:
        import sys as _sys; _sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        n1 = record("poker", "Best chip total ($)", p_chips)
        if delta > 0: record("poker", "Best net win ($)", delta)
        if n1: print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass
    if p_chips < BLIND:
        print(f"  {RD}You went bust!{R}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
