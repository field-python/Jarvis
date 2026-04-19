#!/usr/bin/env python3
"""stocks.py — Stock market viewer with ASCII charts and watchlist"""
import sys, os, json, readline
from pathlib import Path
from datetime import datetime

try:
    import yfinance as yf
    import plotext as plt
except ImportError:
    print("Missing libraries. Run: pip install yfinance plotext")
    sys.exit(1)

BASE_DIR     = Path(__file__).parent.parent.resolve()
WATCHLIST    = BASE_DIR / "config" / "watchlist.json"

# ── Colors ────────────────────────────────────────────────────────────────────
R  = "\033[0m"
B  = "\033[1m"
DIM= "\033[2m"
GR = "\033[32m"
RD = "\033[31m"
CY = "\033[36m"
YL = "\033[33m"
MG = "\033[35m"
BL = "\033[34m"
WH = "\033[97m"

PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"]
PERIOD_LABELS = {"1d":"1 Day","5d":"5 Days","1mo":"1 Month","3mo":"3 Months","6mo":"6 Months","1y":"1 Year","5y":"5 Years"}

def load_watchlist():
    if WATCHLIST.exists():
        try:
            return json.loads(WATCHLIST.read_text())
        except Exception:
            pass
    return ["SPY", "AAPL", "TSLA", "NVDA", "BTC-USD"]

def save_watchlist(wl):
    WATCHLIST.write_text(json.dumps(wl, indent=2))

def fmt_change(val, pct):
    sign  = "+" if val >= 0 else ""
    color = GR if val >= 0 else RD
    arrow = "▲" if val >= 0 else "▼"
    return f"{color}{arrow} {sign}{val:.2f} ({sign}{pct:.2f}%){R}"

def fmt_num(n):
    if n is None: return "N/A"
    if abs(n) >= 1e12: return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:  return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.2f}"

def get_ticker_data(symbol, period="1mo"):
    try:
        t    = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period=period)
        return t, info, hist
    except Exception as e:
        print(f"{RD}Error fetching {symbol}: {e}{R}")
        return None, {}, None

def draw_chart(symbol, hist, period):
    if hist is None or hist.empty:
        print(f"{RD}No chart data available.{R}")
        return

    prices = list(hist["Close"])
    dates  = [str(d.date()) for d in hist.index]
    if not prices:
        return

    start_p = prices[0]
    end_p   = prices[-1]
    color   = "green" if end_p >= start_p else "red"

    # terminal width
    try:
        cols = os.get_terminal_size().columns - 4
    except Exception:
        cols = 80
    rows = 18

    plt.clear_figure()
    plt.theme("dark")
    plt.plot_size(cols, rows)
    plt.plot(prices, color=color, marker="braille")
    plt.title(f"{symbol}  —  {PERIOD_LABELS.get(period, period)}")
    plt.xlabel("")
    plt.yfrequency(5)
    plt.xfrequency(0)
    plt.show()

def draw_info(symbol, info):
    price     = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    prev      = info.get("regularMarketPreviousClose") or info.get("previousClose")
    change    = (price - prev) if price and prev else None
    pct       = (change / prev * 100) if change is not None and prev else None
    name      = info.get("shortName") or info.get("longName") or symbol
    mkt_cap   = info.get("marketCap")
    vol       = info.get("volume")
    avg_vol   = info.get("averageVolume")
    hi52      = info.get("fiftyTwoWeekHigh")
    lo52      = info.get("fiftyTwoWeekLow")
    pe        = info.get("trailingPE")
    div_yield = info.get("dividendYield")
    sector    = info.get("sector", "")
    exchange  = info.get("exchange", "")

    print(f"\n{B}{WH}{name}{R}  {DIM}({symbol}){R}  {DIM}{exchange}{R}")
    if sector:
        print(f"{DIM}{sector}{R}")
    print()

    if price:
        print(f"  {B}{WH}${price:,.4f}{R}", end="  ")
        if change is not None and pct is not None:
            print(fmt_change(change, pct))
        else:
            print()
    print()

    col_w = 22
    rows = []
    if hi52:   rows.append(("52W High",    f"${hi52:,.2f}"))
    if lo52:   rows.append(("52W Low",     f"${lo52:,.2f}"))
    if mkt_cap:rows.append(("Market Cap",  fmt_num(mkt_cap)))
    if vol:    rows.append(("Volume",      f"{vol:,}"))
    if avg_vol:rows.append(("Avg Volume",  f"{avg_vol:,}"))
    if pe:     rows.append(("P/E Ratio",   f"{pe:.2f}"))
    if div_yield:
        dy = div_yield if div_yield < 1 else div_yield / 100
        rows.append(("Div Yield", f"{dy*100:.2f}%"))

    for i in range(0, len(rows), 2):
        left  = rows[i]
        right = rows[i+1] if i+1 < len(rows) else None
        line  = f"  {DIM}{left[0]:<14}{R}{CY}{left[1]:<{col_w}}{R}"
        if right:
            line += f"  {DIM}{right[0]:<14}{R}{CY}{right[1]}{R}"
        print(line)
    print()

def show_stock(symbol, period="1mo"):
    print(f"\n{DIM}Fetching {symbol}...{R}", end="\r")
    t, info, hist = get_ticker_data(symbol, period)
    if t is None:
        return
    print(" " * 30, end="\r")
    draw_chart(symbol, hist, period)
    draw_info(symbol, info)

def show_watchlist(period="1mo"):
    wl = load_watchlist()
    if not wl:
        print(f"{YL}Watchlist is empty. Add tickers with: Jarvis stocks add AAPL{R}")
        return
    print(f"\n{B}{WH}  Watchlist{R}  {DIM}({PERIOD_LABELS.get(period,'')}) — {datetime.now().strftime('%b %d %Y %H:%M')}{R}\n")

    for sym in wl:
        t, info, hist = get_ticker_data(sym, "5d")
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        prev  = info.get("regularMarketPreviousClose") or info.get("previousClose")
        name  = (info.get("shortName") or sym)[:22]
        change = (price - prev) if price and prev else None
        pct    = (change / prev * 100) if change is not None and prev else None

        sym_str  = f"{B}{sym:<8}{R}"
        name_str = f"{DIM}{name:<24}{R}"
        price_str= f"{WH}${price:>10,.4f}{R}" if price else f"{'N/A':>11}"
        chg_str  = fmt_change(change, pct) if change is not None else ""
        print(f"  {sym_str} {name_str} {price_str}  {chg_str}")
    print()

def interactive_mode(symbols, period="1mo"):
    idx = 0
    period_idx = PERIODS.index(period) if period in PERIODS else 2

    while True:
        sym = symbols[idx]
        p   = PERIODS[period_idx]
        os.system("clear")
        show_stock(sym, p)

        nav = []
        if len(symbols) > 1:
            nav.append(f"{DIM}◀ ▶  switch stock ({idx+1}/{len(symbols)}){R}")
        nav.append(f"{DIM}↑ ↓  timeframe ({PERIOD_LABELS[p]}){R}")
        nav.append(f"{DIM}W  watchlist  Q  quit{R}")
        print("  " + "   ".join(nav))

        import tty, termios, select
        fd  = sys.stdin.fileno()
        try:
            old = termios.tcgetattr(fd)
        except termios.error:
            break
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "C" and len(symbols) > 1:
                            idx = (idx + 1) % len(symbols)
                        elif ch3 == "D" and len(symbols) > 1:
                            idx = (idx - 1) % len(symbols)
                        elif ch3 == "A":
                            period_idx = (period_idx - 1) % len(PERIODS)
                        elif ch3 == "B":
                            period_idx = (period_idx + 1) % len(PERIODS)
                else:
                    break  # bare ESC = quit
            elif ch.lower() == "q":
                break
            elif ch.lower() == "w":
                os.system("clear")
                show_watchlist()
                sys.stdout.write(f"  {DIM}Press any key to continue...{R}")
                sys.stdout.flush()
                os.read(fd, 1)
                # drain any escape sequence bytes left from arrow keys
                import select as _sel
                while _sel.select([fd], [], [], 0.05)[0]:
                    os.read(fd, 1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def main():
    args = sys.argv[1:]

    if not args:
        wl = load_watchlist()
        if not wl:
            print(f"{YL}Watchlist is empty. Add tickers with: Jarvis stocks add AAPL{R}\n")
            return
        interactive_mode(wl)
        return

    cmd = args[0].lower()

    if cmd == "add":
        if len(args) < 2:
            print(f"{YL}Usage: Jarvis stocks add TICKER{R}")
            return
        sym = args[1].upper()
        wl  = load_watchlist()
        if sym not in wl:
            wl.append(sym)
            save_watchlist(wl)
            print(f"{GR}Added {sym} to watchlist.{R}")
        else:
            print(f"{YL}{sym} already in watchlist.{R}")
        return

    if cmd == "remove":
        if len(args) < 2:
            print(f"{YL}Usage: Jarvis stocks remove TICKER{R}")
            return
        sym = args[1].upper()
        wl  = load_watchlist()
        if sym in wl:
            wl.remove(sym)
            save_watchlist(wl)
            print(f"{GR}Removed {sym} from watchlist.{R}")
        else:
            print(f"{YL}{sym} not in watchlist.{R}")
        return

    if cmd == "watchlist":
        wl = load_watchlist()
        if wl:
            interactive_mode(wl)
        else:
            print(f"{YL}Watchlist is empty. Add tickers with: Jarvis stocks add AAPL{R}\n")
        return

    # ticker(s) passed — interactive viewer
    symbols = [a.upper() for a in args if not a.startswith("-")]
    period  = "1mo"
    for a in args:
        if a in PERIODS:
            period = a

    if not symbols:
        show_watchlist()
        return

    interactive_mode(symbols, period)

if __name__ == "__main__":
    main()
