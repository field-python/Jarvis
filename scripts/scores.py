#!/usr/bin/env python3
"""scores.py — shared high score system for Jarvis games"""
import json, os, sys
from pathlib import Path
from datetime import datetime

BASE_DIR    = Path(__file__).parent.parent.resolve()
SCORES_FILE = BASE_DIR / "config" / "game-scores.json"

CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
B   = "\033[1m"
DIM = "\033[2m"
R   = "\033[0m"
HR  = "━" * 48


def load():
    if SCORES_FILE.exists():
        try:
            return json.loads(SCORES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save(data):
    SCORES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record(game, metric, value, label=""):
    """Record a score. Keeps top 5 per game/metric."""
    data   = load()
    key    = f"{game}:{metric}"
    board  = data.get(key, [])
    entry  = {
        "value": value,
        "label": label,
        "date":  datetime.now().strftime("%Y-%m-%d"),
    }
    board.append(entry)
    # Sort — higher is better for most games
    board.sort(key=lambda x: x["value"], reverse=True)
    data[key] = board[:5]
    save(data)
    return board[0]["value"] == value and board.index(entry) == 0  # True if new #1


def get_best(game, metric):
    data  = load()
    board = data.get(f"{game}:{metric}", [])
    return board[0]["value"] if board else None


def show_all():
    data = load()
    if not data:
        print(f"\n  {DIM}No scores recorded yet.{R}\n")
        return

    os.system("clear")
    print(f"{B}{CY}{HR}{R}")
    print(f"{B}{CY}  Jarvis  🏆  High Scores{R}")
    print(f"{B}{CY}{HR}{R}\n")

    games_seen = {}
    for key, board in data.items():
        game, metric = key.split(":", 1)
        if game not in games_seen:
            games_seen[game] = {}
        games_seen[game][metric] = board

    medals = [f"{GR}{B}🥇{R}", f"{YL}🥈{R}", f"{DIM}🥉{R}"]

    for game, metrics in sorted(games_seen.items()):
        print(f"  {B}{game.upper()}{R}")
        for metric, board in metrics.items():
            print(f"  {DIM}{metric}{R}")
            for i, entry in enumerate(board[:3]):
                medal = medals[i] if i < 3 else "  "
                label = f"  {DIM}{entry['label']}{R}" if entry.get("label") else ""
                print(f"    {medal}  {B}{entry['value']}{R}{label}  {DIM}{entry['date']}{R}")
        print()


if __name__ == "__main__":
    show_all()
