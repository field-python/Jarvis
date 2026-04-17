#!/usr/bin/env python3
"""todo.py — to-do lists and checklists"""
import sys, os, re, tty, termios
from pathlib import Path
from datetime import datetime

base_dir  = Path(__file__).parent.parent.resolve()
todo_dir  = base_dir / "notes" / "todo"
todo_dir.mkdir(parents=True, exist_ok=True)

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def list_file(name):
    return todo_dir / f"{name}.txt"


def load_list(name):
    f = list_file(name)
    if not f.exists():
        return []
    items = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("[x] "):
            items.append((True, line[4:]))
        elif line.startswith("[ ] "):
            items.append((False, line[4:]))
    return items


def save_list(name, items):
    lines = [("[x] " if done else "[ ] ") + text for done, text in items]
    list_file(name).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def show_list(name, items):
    print()
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  {name.title()} List{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    if not items:
        print(f"\n  {DIM}(empty){RESET}\n")
        return
    print()
    done_count = sum(1 for d, _ in items if d)
    for i, (done, text) in enumerate(items, 1):
        if done:
            print(f"  {DIM}{i:>2}. ✓  {text}{RESET}")
        else:
            print(f"  {BOLD}{i:>2}. ☐  {text}{RESET}")
    print()
    print(f"  {DIM}{done_count}/{len(items)} done{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")


def all_lists():
    return sorted(f.stem for f in todo_dir.glob("*.txt"))


arg  = sys.argv[1].lower() if len(sys.argv) > 1 else ""
rest = sys.argv[2:]

# ── Jarvis todo                     → show default list ──────────────────────
# ── Jarvis todo shopping            → show shopping list ────────────────────
# ── Jarvis todo add "item"          → add to default ────────────────────────
# ── Jarvis todo shopping add "item" → add to shopping ───────────────────────
# ── Jarvis todo done 2              → check off item #2 in default ──────────
# ── Jarvis todo shopping done 2     → check off item #2 in shopping ─────────
# ── Jarvis todo clear               → remove all done items from default ────
# ── Jarvis todo lists               → show all list names ───────────────────

def resolve(arg, rest):
    """Figure out which list name and sub-command we're dealing with."""
    sub_cmds = {"add", "done", "check", "remove", "rm", "delete", "clear", "new", "lists"}
    if not arg:
        return "default", "view", []
    if arg == "lists":
        return None, "lists", []
    if arg in sub_cmds:
        return "default", arg, rest
    # arg is a list name — peek at rest
    if rest and rest[0].lower() in sub_cmds:
        return arg, rest[0].lower(), rest[1:]
    return arg, "view", rest

list_name, sub_cmd, args = resolve(arg, rest)

if sub_cmd == "lists":
    names = all_lists()
    print()
    if not names:
        print("  No lists yet. Try: Jarvis todo add \"buy milk\"")
    else:
        print(f"  {BOLD}Your lists:{RESET}")
        for n in names:
            items = load_list(n)
            done  = sum(1 for d, _ in items if d)
            print(f"    • {n}  {DIM}({done}/{len(items)} done){RESET}")
    print()
    sys.exit(0)

items = load_list(list_name)

if sub_cmd == "view":
    show_list(list_name, items)

elif sub_cmd == "add":
    text = " ".join(args).strip()
    if not text:
        try:
            text = input(f"  {YELLOW}Add to {list_name}: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    if text:
        items.append((False, text))
        save_list(list_name, items)
        print(f"  {GREEN}Added:{RESET} {text}")
        show_list(list_name, items)

elif sub_cmd in ("done", "check"):
    if not args:
        show_list(list_name, items)
        try:
            n_str = input(f"\n  {YELLOW}Check off item #: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    else:
        n_str = args[0]
    try:
        n = int(n_str) - 1
        if 0 <= n < len(items):
            done, text = items[n]
            items[n] = (not done, text)
            save_list(list_name, items)
            status = "✓ Done" if not done else "☐ Undone"
            print(f"  {GREEN}{status}:{RESET} {text}")
            show_list(list_name, items)
        else:
            print(f"  No item #{n+1}")
    except ValueError:
        print("  Please give a number.")

elif sub_cmd in ("remove", "rm", "delete"):
    if not args:
        show_list(list_name, items)
        try:
            n_str = input(f"\n  {YELLOW}Remove item #: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    else:
        n_str = args[0]
    try:
        n = int(n_str) - 1
        if 0 <= n < len(items):
            _, text = items.pop(n)
            save_list(list_name, items)
            print(f"  {RED}Removed:{RESET} {text}")
            show_list(list_name, items)
        else:
            print(f"  No item #{n+1}")
    except ValueError:
        print("  Please give a number.")

elif sub_cmd == "clear":
    before = len(items)
    items  = [(d, t) for d, t in items if not d]
    save_list(list_name, items)
    removed = before - len(items)
    print(f"  Cleared {removed} completed item(s).")
    show_list(list_name, items)

elif sub_cmd == "new":
    name = " ".join(args).strip().lower().replace(" ", "-")
    if not name:
        try:
            name = input(f"  {YELLOW}New list name: {RESET}").strip().lower().replace(" ", "-")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    if name:
        save_list(name, [])
        print(f"  {GREEN}Created list:{RESET} {name}")
