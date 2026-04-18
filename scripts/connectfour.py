#!/usr/bin/env python3
"""connectfour.py — Connect Four vs AI"""
import os, sys, random, tty, termios, select

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"

HR   = "━" * 44
ROWS = 6
COLS = 7
EMPTY, PLAYER, AI = 0, 1, 2
P_TOKEN = f"{RD}{B}●{R}"
A_TOKEN = f"{YL}{B}●{R}"
E_TOKEN = f"{DIM}○{R}"

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd,1).decode("utf-8","replace")
        if ch == "\x1b":
            r,_,_ = select.select([fd],[],[],0.1)
            if r:
                seq = os.read(fd,2)
                if seq == b"[C": return "RIGHT"
                if seq == b"[D": return "LEFT"
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def make_board():
    return [[EMPTY]*COLS for _ in range(ROWS)]

def drop(board, col, piece):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return r
    return -1

def valid_cols(board):
    return [c for c in range(COLS) if board[0][c] == EMPTY]

def check_win(board, piece):
    for r in range(ROWS):
        for c in range(COLS-3):
            if all(board[r][c+i]==piece for i in range(4)): return True
    for r in range(ROWS-3):
        for c in range(COLS):
            if all(board[r+i][c]==piece for i in range(4)): return True
    for r in range(ROWS-3):
        for c in range(COLS-3):
            if all(board[r+i][c+i]==piece for i in range(4)): return True
    for r in range(3, ROWS):
        for c in range(COLS-3):
            if all(board[r-i][c+i]==piece for i in range(4)): return True
    return False

def score_window(window, piece):
    opp = AI if piece == PLAYER else PLAYER
    score = 0
    if window.count(piece) == 4: score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1: score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2: score += 2
    if window.count(opp) == 3 and window.count(EMPTY) == 1: score -= 4
    return score

def score_board(board, piece):
    score = 0
    center = [board[r][COLS//2] for r in range(ROWS)]
    score += center.count(piece) * 3
    for r in range(ROWS):
        for c in range(COLS-3):
            score += score_window([board[r][c+i] for i in range(4)], piece)
    for c in range(COLS):
        for r in range(ROWS-3):
            score += score_window([board[r+i][c] for i in range(4)], piece)
    for r in range(ROWS-3):
        for c in range(COLS-3):
            score += score_window([board[r+i][c+i] for i in range(4)], piece)
    for r in range(3,ROWS):
        for c in range(COLS-3):
            score += score_window([board[r-i][c+i] for i in range(4)], piece)
    return score

def minimax(board, depth, alpha, beta, maximizing):
    valid = valid_cols(board)
    is_terminal = check_win(board, PLAYER) or check_win(board, AI) or not valid
    if depth == 0 or is_terminal:
        if check_win(board, AI):    return None, 100000
        if check_win(board, PLAYER):return None, -100000
        if not valid:               return None, 0
        return None, score_board(board, AI)
    if maximizing:
        val = -float("inf")
        best_col = random.choice(valid)
        for c in valid:
            b2 = [row[:] for row in board]
            drop(b2, c, AI)
            _, sc = minimax(b2, depth-1, alpha, beta, False)
            if sc > val:
                val = sc; best_col = c
            alpha = max(alpha, val)
            if alpha >= beta: break
        return best_col, val
    else:
        val = float("inf")
        best_col = random.choice(valid)
        for c in valid:
            b2 = [row[:] for row in board]
            drop(b2, c, PLAYER)
            _, sc = minimax(b2, depth-1, alpha, beta, True)
            if sc < val:
                val = sc; best_col = c
            beta = min(beta, val)
            if alpha >= beta: break
        return best_col, val

def draw(board, cursor, msg="", scores=None):
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    s = f"  W:{scores['p']} L:{scores['l']} T:{scores['t']}" if scores else ""
    print(f"{B}{CY}  Jarvis  ⬤  Connect Four{R}{DIM}{s}{R}")
    print(f"{B}{CY}{HR}{R}\n")

    # Column indicator
    ind = "  " + "".join(f" {YL}▼{R} " if i==cursor else "   " for i in range(COLS))
    print(ind)

    # Board
    print(f"  ┌" + "───┬"*(COLS-1) + "───┐")
    for r, row in enumerate(board):
        cells = "│".join(f" {P_TOKEN if v==PLAYER else (A_TOKEN if v==AI else E_TOKEN)} " for v in row)
        print(f"  │{cells}│")
        if r < ROWS-1:
            print(f"  ├" + "───┼"*(COLS-1) + "───┤")
    print(f"  └" + "───┴"*(COLS-1) + "───┘")
    print("  " + "".join(f" {DIM}{i+1}{R}  " for i in range(COLS)))

    print(f"\n  {RD}●{R} You   {YL}●{R} Jarvis\n")
    if msg:
        print(f"  {msg}\n")
    else:
        print(f"  {DIM}← → move   Enter drop   Q quit{R}\n")

def play_game(scores):
    board  = make_board()
    cursor = 3

    while True:
        draw(board, cursor, scores=scores)
        # Player turn
        moved = False
        while not moved:
            ch = getch()
            if ch in ("q","\x1b","\x03"): return False
            if ch == "RIGHT": cursor = min(cursor+1, COLS-1)
            elif ch == "LEFT": cursor = max(cursor-1, 0)
            elif ch in ("\r","\n"," "):
                if cursor in valid_cols(board):
                    drop(board, cursor, PLAYER)
                    moved = True
                else:
                    draw(board, cursor, f"{RD}Column full!{R}", scores)
            draw(board, cursor, scores=scores)

        if check_win(board, PLAYER):
            scores["p"] += 1
            draw(board, cursor, f"{GR}{B}You win! 🎉{R}", scores)
            break
        if not valid_cols(board):
            scores["t"] += 1
            draw(board, cursor, f"{YL}It's a tie!{R}", scores)
            break

        # AI turn
        draw(board, cursor, f"{YL}Jarvis is thinking...{R}", scores)
        col, _ = minimax(board, 5, -float("inf"), float("inf"), True)
        if col is None: col = random.choice(valid_cols(board))
        drop(board, col, AI)
        cursor = col

        if check_win(board, AI):
            scores["l"] += 1
            draw(board, cursor, f"{RD}Jarvis wins!{R}", scores)
            break
        if not valid_cols(board):
            scores["t"] += 1
            draw(board, cursor, f"{YL}It's a tie!{R}", scores)
            break

    print(f"  {DIM}Any key to play again  |  Q to quit{R}", end="", flush=True)
    return getch().lower() not in ("q","\x1b","\x03")

def main():
    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  ⬤  Connect Four{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  Get {B}4 in a row{R} — horizontal, vertical, or diagonal.")
    print(f"  {RD}●{R} = You   {YL}●{R} = Jarvis\n")
    print(f"  {DIM}← → move column   Enter drop piece   Q quit{R}\n")
    print(f"  {DIM}Any key to start...{R}", end="", flush=True)
    getch()

    scores = {"p":0,"l":0,"t":0}
    while play_game(scores):
        pass

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}  Connect Four  |  Game Over{R}")
    print(f"{B}{CY}{HR}{R}\n")
    print(f"  {GR}Wins:  {scores['p']}{R}")
    print(f"  {RD}Losses:{scores['l']}{R}")
    print(f"  {YL}Ties:  {scores['t']}{R}\n")
    try:
        import sys as _sys; _sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
        from scores import record
        if record("connect-four", "Most wins in session", scores["p"]):
            print(f"  {GR}{B}🏆 New high score!{R}\n")
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
