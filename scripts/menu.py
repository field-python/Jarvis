#!/usr/bin/env python3
"""
menu.py — Interactive Jarvis command menu
Arrow keys or number to select, Enter to confirm, Q to quit.
"""

import sys
import os
import subprocess
import tty
import termios

JARVIS = os.environ.get("JARVIS_LAUNCHER", os.path.expanduser("~/Jarvis"))

MENU = [
    # (label, command_args, needs_input, input_prompt)
    ("🤖  AI",          ["__submenu__", "ai"],       False, ""),
    ("🔧  Tools",       ["__submenu__", "tools_main"], False, ""),
    ("🏠  Life",        ["__submenu__", "life"],     False, ""),
    ("📰  Info",        ["__submenu__", "info"],     False, ""),
    ("📚  Library",     ["__submenu__", "library"],  False, ""),
    ("🎮  Games",       ["__submenu__", "games"],    False, ""),
    ("⚙️  System",      ["__submenu__", "system"],   False, ""),
]

# ── Sub-menus ─────────────────────────────────────────────────────────────────
# Each entry: (label, cmd_args, needs_input, input_prompt) — same format as MENU.
SUBMENUS = {
    # ── Top-level sections ────────────────────────────────────────────────────
    "ai": [
        ("🤖  Ask Jarvis",        ["__submenu__", "ask"],    False, ""),
        ("💬  Chat mode",         ["chat"],                  False, ""),
        ("🎙️  Voice mode",        ["voice"],                 False, ""),
        ("🎯  Skill of the day",  ["skill"],                 False, ""),
    ],
    "tools_main": [
        ("💡  Brainstorm",        ["__submenu__", "tools"],  False, ""),
        ("💻  Code help",         ["code"],                  True,  "Describe what to build: "),
        ("📚  Learn to code",     ["learn"],                 True,  "Topic (e.g. Python for loops): "),
        ("🗣️  Language Hub",      ["language"],              False, ""),
        ("🧮  Calculator",        ["calc"],                  True,  "Expression (e.g. 180 lbs to kg): "),
        ("✏️  Edit / proofread",  ["edit"],                  True,  "Text to improve: "),
        ("🌐  Translate",         ["translate"],             True,  "Text (e.g. hello to Spanish): "),
        ("🩺  Symptom checker",   ["symptom"],               False, ""),
        ("⚖️  Interactive Law",   ["legal"],                 True,  "Legal scenario or question: "),
    ],
    "life": [
        ("🍳  Recipes",           ["__submenu__", "recipes"],  False, ""),
        ("⏱️  Set a timer",       ["timer"],                   True,  "Duration (e.g. 1h, 10m, 30s): "),
        ("🔔  Reminders",         ["__submenu__", "reminders"],False, ""),
        ("✅  To-do list",        ["__submenu__", "todo"],     False, ""),
        ("📝  Notes",             ["__submenu__", "notes"],    False, ""),
    ],
    "info": [
        ("🌤️  News & Weather",    ["__submenu__", "news"],    False, ""),
        ("📈  Stock Market",      ["__submenu__", "stocks"],  False, ""),
        ("🌐  Web search",        ["web"],                    True,  "Search: "),
        ("🔍  Search & Find",     ["__submenu__", "search"],  False, ""),
    ],
    "library": [
        ("📖  Holy Books",        ["__submenu__", "holy_books"], False, ""),
        ("🏛️  Classic Library",   ["__submenu__", "classics"],   False, ""),
        ("✍️  Speech Writer",      ["speech"],                    False, ""),
        ("📜  Law Library",       ["legal", "browse"],           False, ""),
        ("🧪  Erowid Reference",  ["erowid"],                    False, ""),
    ],
    # ── Ask submenu ───────────────────────────────────────────────────────────
    "ask": [
        ("💬  Ask a question",        ["ask"],      True,  "Question: "),
        ("⚡  Brief answer",          ["brief"],    True,  "Question: "),
        ("📖  Detailed answer",       ["detailed"], True,  "Question: "),
        ("📚  Cite sources",          ["cite"],     True,  "Question: "),
        ("🌐  Web search",            ["web"],      True,  "Search: "),
    ],
    "notes": [
        ("📝  Save a note",           ["note"],     True,  "Note: "),
        ("📋  View today's notes",    ["notes"],    False, ""),
        ("🧬  Tell Jarvis about yourself", ["remember"], True, "Tell Jarvis: "),
    ],
    "recipes": [
        ("🍳  Browse recipes",        ["recipe", "list"],    False, ""),
        ("🥘  Recipe from ingredients", ["recipe", "suggest"], True, "What do you have on hand: "),
    ],
    "news": [
        ("🌅  Morning daily briefing", ["daily"],   False, ""),
        ("📰  News briefing",          ["news"],    False, ""),
        ("🌤️  Weather",               ["weather"], True,  "Location (Enter for saved default): "),
    ],
    "stocks": [
        ("📊  Watchlist",             ["stocks"],                  False, ""),
        ("🔎  Look up ticker",        ["stocks"],                  True,  "Ticker (e.g. AAPL, TSLA): "),
        ("➕  Add to watchlist",      ["stocks", "add"],           True,  "Ticker to add: "),
        ("➖  Remove from watchlist", ["stocks", "remove"],        True,  "Ticker to remove: "),
    ],
    "search": [
        ("🌍  Wikipedia lookup",      ["wiki"],     True,  "Topic: "),
        ("🧪  Erowid substance browser", ["erowid"], False, ""),
        ("🔍  Search archive",        ["search"],   True,  "Search: "),
        ("🧠  Semantic find",         ["find"],     True,  "Topic: "),
        ("📂  List archive topics",   ["list"],     False, ""),
    ],
    "holy_books": [
        ("✝️  Bible (KJV)",          ["holybooks", "bible"],           False, ""),
        ("✡️  Torah (JPS)",          ["holybooks", "torah"],           False, ""),
        ("☪️  Quran",                ["holybooks", "quran"],           False, ""),
        ("⛪  Book of Mormon",       ["holybooks", "book of mormon"],  False, ""),
        ("🕉️  Bhagavad Gita",       ["holybooks", "bhagavad gita"],   False, ""),
        ("☯️  Tao Te Ching",         ["holybooks", "tao te ching"],    False, ""),
        ("🕍  Talmud / Mishnah",     ["holybooks", "talmud"],          False, ""),
        ("🔱  Rig Veda",             ["holybooks", "rig veda"],        False, ""),
        ("🕉️  Upanishads",           ["holybooks", "upanishads"],      False, ""),
        ("☸️  Dhammapada",           ["holybooks", "dhammapada"],      False, ""),
        ("📿  Analects of Confucius", ["holybooks", "analects"],       False, ""),
        ("📚  Other Books",          ["__submenu__", "holy_other"],    False, ""),
    ],
    "holy_other": [
        ("The Kybalion",             ["holybooks", "kybalion"],        False, ""),
        ("Avesta (Zoroastrian)",     ["holybooks", "avesta"],          False, ""),
        ("Book of Enoch",            ["holybooks", "book of enoch"],   False, ""),
        ("Book of Jubilees",         ["holybooks", "book of jubilees"],False, ""),
        ("Dead Sea Scrolls",         ["holybooks", "dead sea scrolls"],False, ""),
        ("Ethiopian Bible Overview", ["holybooks", "ethiopian"],       False, ""),
        ("Gospel of Thomas",         ["holybooks", "gospel of thomas"],False, ""),
        ("Guru Granth Sahib",        ["holybooks", "guru granth"],     False, ""),
        ("Pirkei Avot",              ["holybooks", "pirkei"],          False, ""),
    ],
    "system": [
        ("📱  Web UI (phone access)", ["web-ui"],                False, ""),
        ("🔬  System diagnostics",    ["diagnose"],              False, ""),
        ("📡  Diagnose WiFi",         ["diagnose", "--wifi"],    False, ""),
        ("🔄  Update current events", ["update"],                False, ""),
        ("🎭  Set personality level", ["personality"],           False, ""),
        ("📥  Downloads",             ["__submenu__", "downloads"], False, ""),
    ],
    "todo": [
        ("📋  Default list",         ["__submenu__", "todo_default"],   False, ""),
        ("🛒  Shopping list",        ["__submenu__", "todo_shopping"],  False, ""),
        ("📂  All lists",            ["todo", "lists"],                 False, ""),
    ],
    "todo_default": [
        ("📋  View list",            ["todo"],                  False, ""),
        ("➕  Add item",             ["todo", "add"],           True,  "Item: "),
        ("✅  Check off item",       ["todo", "done"],          True,  "Item #: "),
    ],
    "todo_shopping": [
        ("🛒  View shopping list",   ["todo", "shopping"],      False, ""),
        ("➕  Add to shopping",      ["todo", "shopping", "add"], True, "Item: "),
    ],
    "classics": [
        ("📚  Browse all books",              ["classics"],                        False, ""),
        ("⚔️  Adventure",                    ["__submenu__", "classics_adventure"],False, ""),
        ("🚀  Sci-Fi",                        ["__submenu__", "classics_scifi"],   False, ""),
        ("🦇  Gothic & Horror",              ["__submenu__", "classics_gothic"],  False, ""),
        ("🔎  Mystery",                       ["__submenu__", "classics_mystery"], False, ""),
        ("🏛️  Philosophy & Strategy",        ["__submenu__", "classics_phil"],    False, ""),
        ("🎭  Drama & Poetry",               ["__submenu__", "classics_drama"],   False, ""),
        ("💕  Romance & Classic",            ["__submenu__", "classics_romance"], False, ""),
    ],
    "classics_adventure": [
        ("The Mysterious Island",             ["classics", "mysterious island"],   False, ""),
        ("Twenty Thousand Leagues",           ["classics", "twenty thousand"],     False, ""),
        ("Journey to Center of the Earth",    ["classics", "journey to the"],      False, ""),
        ("Around the World in 80 Days",       ["classics", "around the world"],    False, ""),
        ("The Call of the Wild",              ["classics", "call of the wild"],    False, ""),
        ("White Fang",                        ["classics", "white fang"],          False, ""),
        ("Treasure Island",                   ["classics", "treasure island"],     False, ""),
        ("The Count of Monte Cristo",         ["classics", "monte cristo"],        False, ""),
        ("Robinson Crusoe",                   ["classics", "robinson crusoe"],     False, ""),
        ("Moby-Dick",                         ["classics", "moby"],                False, ""),
        ("Adventures of Huckleberry Finn",    ["classics", "huckleberry"],         False, ""),
        ("The Adventures of Tom Sawyer",      ["classics", "tom sawyer"],          False, ""),
    ],
    "classics_scifi": [
        ("The Time Machine",                  ["classics", "time machine"],        False, ""),
        ("The War of the Worlds",             ["classics", "war of the worlds"],   False, ""),
        ("The Invisible Man",                 ["classics", "invisible man"],       False, ""),
    ],
    "classics_gothic": [
        ("Frankenstein",                      ["classics", "frankenstein"],        False, ""),
        ("Dracula",                           ["classics", "dracula"],             False, ""),
        ("The Picture of Dorian Gray",        ["classics", "dorian gray"],         False, ""),
        ("Strange Case of Jekyll and Hyde",   ["classics", "jekyll"],              False, ""),
        ("Works of Edgar Allan Poe",          ["classics", "poe"],                 False, ""),
        ("Heart of Darkness",                 ["classics", "heart of darkness"],   False, ""),
    ],
    "classics_mystery": [
        ("Adventures of Sherlock Holmes",     ["classics", "sherlock"],            False, ""),
        ("The Hound of the Baskervilles",     ["classics", "hound"],               False, ""),
    ],
    "classics_phil": [
        ("The Art of War",                    ["classics", "art of war"],          False, ""),
        ("The Prince",                        ["classics", "the prince"],          False, ""),
        ("The Odyssey",                       ["classics", "odyssey"],             False, ""),
        ("The Iliad",                         ["classics", "iliad"],               False, ""),
        ("Crime and Punishment",              ["classics", "crime and punishment"],False, ""),
    ],
    "classics_drama": [
        ("Hamlet",                            ["classics", "hamlet"],              False, ""),
        ("Romeo and Juliet",                  ["classics", "romeo"],               False, ""),
    ],
    "classics_romance": [
        ("Pride and Prejudice",               ["classics", "pride and prejudice"], False, ""),
        ("Great Expectations",                ["classics", "great expectations"],  False, ""),
        ("A Tale of Two Cities",              ["classics", "tale of two cities"],  False, ""),
    ],
    "reminders": [
        ("🔔  Set a reminder",       ["remind"],                True,  "e.g. at 3pm to call dentist: "),
        ("📋  View reminders",       ["remind", "list"],        False, ""),
        ("🗑️  Delete a reminder",    ["remind", "delete"],      True,  "Reminder #: "),
        ("▶️  Start reminder daemon", ["remind-start"],         False, ""),
    ],
    "tools": [
        ("💡  Brainstorm ideas",     ["brainstorm"],  True,  "Topic or problem: "),
        ("⚖️  Pros & Cons",          ["pros"],        True,  "Decision or topic: "),
        ("🧒  Explain simply (ELI5)", ["eli5"],       True,  "Topic: "),
        ("🔀  Compare two things",   ["compare"],     True,  "X vs Y: "),
        ("🗺️  Action plan",          ["plan"],        True,  "Goal or project: "),
        ("🌐  Translate",            ["translate"],   True,  "Text (e.g. hello to Spanish): "),
        ("✏️  Edit / proofread",     ["edit"],        True,  "Text to improve: "),
    ],
    "games": [
        ("🃏  Blackjack",         ["blackjack"],     False, ""),
        ("♠️  Poker (Hold'em)",   ["poker"],         False, ""),
        ("🎰  Slots",             ["slots"],         False, ""),
        ("🎡  Roulette",          ["roulette"],      False, ""),
        ("🎲  Yahtzee",           ["yahtzee"],       False, ""),
        ("⬤   Connect Four",     ["connectfour"],   False, ""),
        ("🃏  Higher or Lower",   ["higherlower"],   False, ""),
        ("🧠  Trivia",            ["trivia"],        False, ""),
        ("💀  Hangman",           ["hangman"],       False, ""),
        ("🔀  Word Scramble",     ["word-scramble"], False, ""),
        ("➕  Math Quiz",         ["mathquiz"],      False, ""),
        ("🔗  Word Chain",        ["wordchain"],     False, ""),
        ("🏆  High Scores",       ["scores"],        False, ""),
    ],
    "downloads": [
        ("General knowledge",        ["download-general"],           False, ""),
        ("Culture & occult",         ["download-culture"],           False, ""),
        ("Linux & tech",             ["download-tech"],              False, ""),
        ("Pop culture",              ["download-pop-culture"],       False, ""),
        ("Misc knowledge",           ["download-misc"],              False, ""),
        ("Law & legal reference",    ["download-law"],               False, ""),
        ("Fringe & esoteric",        ["download-fringe"],            False, ""),
        ("Sacred texts",             ["download-sacred"],            False, ""),
        ("Sacred texts (extended)",  ["download-sacred-extended"],   False, ""),
        ("Declassified documents",   ["download-declassified"],      False, ""),
        ("Regional content",         ["download-regions"],           False, ""),
        ("Coding reference",         ["download-coding"],            False, ""),
        ("Survival & wilderness",    ["download-survival"],          False, ""),
        ("Homesteading & farming",   ["download-homesteading"],      False, ""),
        ("Food preservation",        ["download-food-preservation"], False, ""),
        ("Medical reference",        ["download-medical"],           False, ""),
        ("Ham radio & comms",        ["download-ham-radio"],         False, ""),
    ],
}

HELP = {
    "Ask Jarvis":              "Ask questions with multiple answer styles",
    "Web search":              "Search DuckDuckGo and summarize results",
    "Code help":               "Generate working code in any language",
    "Learn to code":           "Interactive step-by-step coding lessons",
    "Language Hub":            "Learn phrases, translate, practice 10 languages",
    "Chat mode":               "Open-ended conversation with memory",
    "Voice mode":              "Wake word mode — say 'Hey Jarvis' to talk",
    "Notes":                   "Save, view, and manage your personal notes",
    "Recipes":                 "Browse, search, and get recipe suggestions",
    "Skill of the day":        "Learn one practical skill — new every day",
    "Symptom checker":         "Interactive medical triage — describe symptoms",
    "News & Weather":          "Headlines, weather forecast, and daily briefing",
    "Set a timer":             "Countdown timer with spoken alerts",
    "Search":                  "Search your archive, Wikipedia, or semantic topics",
    "System & Updates":        "Diagnostics, downloads, web UI, settings",
    "Interactive Law":         "Analyze legal scenarios and explain your rights",
    "Law Library":             "Browse 389 law documents — cases, statutes, rights, Black's Law",
    "Show help":               "Full command reference",
    "Brainstorm":              "Brainstorm, pros/cons, compare, translate, plan, edit",
    "Calculator":              "Instant math and unit conversions — no AI needed",
    "To-do list":              "Add, check off, and manage your checklists",
    "Reminders":               "Set time-based reminders with spoken alerts",
    "Games":                   "Trivia, Hangman, Word Scramble, Blackjack, Math Quiz, Word Chain",
    "Trivia":                  "AI-generated multiple choice — 10 categories",
    "Hangman":                 "Guess the word before the man is hanged",
    "Word Scramble":           "Unscramble the letters before time runs out",
    "Blackjack":               "Hit or stand — beat the dealer to 21",
    "Math Quiz":               "Timed arithmetic — Easy / Medium / Hard",
    "Word Chain":              "Each word starts with the last letter of the previous",
    "Default list":            "View, add, and check off items on your default list",
    "Shopping list":           "View and add items to your shopping list",
    "All lists":               "See all todo lists",
    # submenus
    "Ask a question":          "Full answer with archive context",
    "Brief answer":            "Short, direct answer",
    "Detailed answer":         "In-depth answer with steps and context",
    "Cite sources":            "Answer with archive sources listed",
    "Save a note":             "Save a quick note to today's note file",
    "View today's notes":      "Show all notes written today",
    "Tell Jarvis about yourself": "Save a personal fact Jarvis remembers",
    "Browse recipes":          "Arrow-key recipe browser",
    "Recipe from ingredients": "Tell Jarvis what you have — get meal ideas",
    "Morning daily briefing":  "Weather + news + skill of the day, spoken aloud",
    "News briefing":           "Latest headlines summarized by Jarvis",
    "Weather":                 "Current conditions and forecast for your location",
    "Wikipedia lookup":        "Look up any topic on Wikipedia",
    "Erowid substance browser": "Offline drug reference — dosage, effects, harm reduction, combinations",
    "Search archive":          "Keyword search through your downloaded knowledge",
    "Semantic find":           "Find related topics by meaning, not keywords",
    "List archive topics":     "See everything in your knowledge archive",
    "Web UI (phone access)":   "Start the web interface — access from phone/browser",
    "System diagnostics":      "Check Ollama, models, disk, and system health",
    "Diagnose WiFi":           "Test WiFi connection and diagnose issues",
    "Update current events":   "Refresh news and current events in archive",
    "Set personality level":   "Choose Jarvis personality: Protocol / Character / Ghost",
    "Downloads":               "Download knowledge packs to your offline archive",
    "Brainstorm ideas":        "Generate 12-15 ideas in categories on any topic",
    "Pros & Cons":             "Structured pros/cons analysis with verdict",
    "Explain simply (ELI5)":   "Plain-English explanation of any concept",
    "Compare two things":      "Side-by-side comparison across key dimensions",
    "Action plan":             "Break any goal into phased actionable steps",
    "Translate":               "Translate text to any language with breakdown",
    "Edit / proofread":        "Improve and clean up any piece of writing",
}

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
CLEAR_LINE = "\033[2K\r"


def getch():
    """Read a single character without echo. Returns '\x1b' for plain ESC."""
    import select as _select
    import os as _os
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            # Use select on the raw fd (not the Python stream) — reliable timing
            r, _, _ = _select.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", errors="replace")
                return "\x1b" + rest
            return "\x1b"   # plain ESC — nothing followed within 100 ms
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def input_with_esc(prompt_str):
    """Like input() but returns None if ESC is pressed. Supports backspace."""
    import select
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    # Strip ANSI escape codes to get printable length of prompt
    import re as _re
    _vlen = len(_re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Check for arrow keys or other escape sequences
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)  # drain the sequence, ignore it
                    continue
                # Plain ESC — go back to menu
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):  # backspace
                if buf:
                    buf.pop()
                    try:
                        cols = os.get_terminal_size().columns
                    except OSError:
                        cols = 80
                    total = _vlen + len(buf) + 1
                    lines_up = total // cols
                    if lines_up:
                        sys.stdout.write("\033[%dA" % lines_up)
                    sys.stdout.write("\r\033[J" + prompt_str + "".join(buf))
                    sys.stdout.flush()
            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def draw_submenu(title, items, selected):
    os.system("clear")
    HR = "━" * 76
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  {title}{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()
    for i, (label, *_) in enumerate(items):
        num = f"{i + 1:>2}."
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {label}{RESET}")
        else:
            print(f"  {DIM}{num}    {label}{RESET}")
    print()
    sel_label = items[selected][0]
    hint = HELP.get(sel_label, "")
    if hint:
        print(f"  {YELLOW}{hint}{RESET}")
    print(f"  {DIM}↑↓ or 1-{len(items)} to select  |  Enter to run  |  ESC/Q to go back{RESET}")
    print()


def run_submenu(title, items):
    """Generic submenu handler — works for any group of commands."""
    selected = 0
    while True:
        draw_submenu(title, items, selected)
        key = getch()

        if key in ("q", "Q", "\x1b"):
            return

        elif key == "\x1b[A":
            selected = (selected - 1) % len(items)

        elif key == "\x1b[B":
            selected = (selected + 1) % len(items)

        elif key in ("\r", "\n"):
            label, cmd_args, needs_input, prompt = items[selected]
            run_command(label, cmd_args, needs_input, prompt)

        elif key.isdigit():
            n = int(key)
            if 1 <= n <= len(items):
                selected = n - 1


def draw_menu(items, selected):
    os.system("clear")
    HR = "━" * 76
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print(f"{BOLD}{CYAN}  Jarvis  |  Command Menu{RESET}")
    print(f"{BOLD}{CYAN}{HR}{RESET}")
    print()

    split = (len(items) + 1) // 2   # always balanced — left gets the extra if odd
    COL_W = 40                       # visible character width of the left column

    for row in range(split):
        # ── left column ──────────────────────────────────────────────────────
        num = f"{row + 1:>2}."
        label = items[row][0]
        if row == selected:
            plain   = f"  {num} ▶  {label}"
            colored = f"  {BOLD}{GREEN}{num} ▶  {label}{RESET}"
        else:
            plain   = f"  {num}    {label}"
            colored = f"  {DIM}{num}    {label}{RESET}"
        left_cell = colored + " " * max(0, COL_W - len(plain))

        # ── right column (items split+row, aligned beside rows 0..N) ─────────
        j = split + row
        if j < len(items):
            rnum = f"{j + 1:>2}."
            rlabel = items[j][0]
            if j == selected:
                right_cell = f"  {BOLD}{GREEN}{rnum} ▶  {rlabel}{RESET}"
            else:
                right_cell = f"  {DIM}{rnum}    {rlabel}{RESET}"
            print(f"{left_cell}{right_cell}")
        else:
            print(left_cell)

    print()
    sel_label = items[selected][0]
    hint = HELP.get(sel_label, "")
    if hint:
        print(f"  {YELLOW}{hint}{RESET}")
    print(f"  {DIM}↑↓ or 1-{len(items)} to select  |  Enter to run  |  Q to quit{RESET}")
    print()


# Commands that loop — keep asking questions instead of returning to menu
ASK_LOOP_CMDS = {"ask", "brief", "detailed", "cite", "web", "firstaid", "search", "find", "wiki", "remember", "legal", "brainstorm", "pros", "eli5", "compare", "plan", "translate", "edit", "calc"}

# Commands that manage their own exit flow (Q/ESC exits them internally).
# Skip the extra "Press ESC to return to menu..." wait for these.
SELF_MANAGED = {"chat", "voice", "language", "skill", "trivia", "hangman", "word-scramble", "remind-start", "news", "daily", "symptom", "recipe", "timer", "erowid", "holybooks", "classics", "blackjack", "mathquiz", "wordchain", "learn", "legal", "stocks", "slots", "higherlower", "roulette", "connectfour", "yahtzee", "poker", "weather", "speech"}


def _loop_prompt(prompt):
    """Build the follow-up label from the original prompt, e.g. 'Question: ' → 'Question (ESC to exit): '"""
    base = prompt.split("(")[0].strip().rstrip(":").rstrip()
    return f"{base} (ESC to exit): "


def run_command(label, cmd_args, needs_input, prompt):
    if cmd_args[0] == "__submenu__":
        key = cmd_args[1]
        run_submenu(label, SUBMENUS[key])
        return

    loop = cmd_args[0] in ASK_LOOP_CMDS and needs_input

    def show_header(question=None):
        os.system("clear")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{BOLD}  {label}{RESET}")
        print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        if question:
            print()
            print(f"  {YELLOW}{prompt}{RESET}{question}")
        print()

    show_header()

    if needs_input:
        try:
            user_input = input_with_esc(f"  {YELLOW}{prompt}{RESET}")
        except KeyboardInterrupt:
            return
        if user_input is None:
            return
        user_input = user_input.strip()
        if not user_input:
            # Empty input: if the command supports an optional arg (e.g. weather),
            # run it with no arg so it falls back to its saved default.
            # For commands that require input, just return to menu.
            if cmd_args[0] in ("weather",):
                full_cmd = [JARVIS] + cmd_args
            else:
                return
        else:
            full_cmd = [JARVIS] + cmd_args + [user_input]
    else:
        full_cmd = [JARVIS] + cmd_args

    print()
    try:
        subprocess.run(full_cmd)
    except KeyboardInterrupt:
        pass

    # Self-managed commands handle their own exit — no extra keypress needed.
    if cmd_args[0] in SELF_MANAGED:
        return

    print()
    print(f"  {DIM}{'─' * 40}{RESET}")

    if not loop:
        print(f"  {DIM}Press any key to return to menu...{RESET}", end="", flush=True)
        while True:
            k = getch()
            if not k.startswith("\x1b["):  # ignore arrow keys, accept everything else
                break
        return

    # Loop mode: show answer, then ask for next WITHOUT clearing the screen.
    # Only clear when the user actually types a new question.
    follow = _loop_prompt(prompt)
    while True:
        print()
        try:
            next_q = input_with_esc(f"  {YELLOW}{follow}{RESET}")
        except KeyboardInterrupt:
            return
        if next_q is None:          # ESC → back to menu
            return
        next_q = next_q.strip()
        if not next_q:
            continue                 # blank Enter → re-show same prompt

        show_header(question=next_q)
        full_cmd = [JARVIS] + cmd_args + [next_q]
        print()
        try:
            subprocess.run(full_cmd)
        except KeyboardInterrupt:
            pass
        print()
        print(f"  {DIM}{'─' * 40}{RESET}")


def main():
    selected = 0
    num_buf = ""

    while True:
        draw_menu(MENU, selected)

        key = getch()

        if key in ("q", "Q", "\x03"):  # Q or Ctrl+C
            os.system("clear")
            sys.exit(0)

        elif key == "\x1b[A":  # up arrow — move up within current column
            split = (len(MENU) + 1) // 2
            if selected < split:
                selected = (selected - 1) % split
            else:
                right_size = len(MENU) - split
                selected = split + (selected - split - 1) % right_size
            num_buf = ""

        elif key == "\x1b[B":  # down arrow — move down within current column
            split = (len(MENU) + 1) // 2
            if selected < split:
                selected = (selected + 1) % split
            else:
                right_size = len(MENU) - split
                selected = split + (selected - split + 1) % right_size
            num_buf = ""

        elif key == "\x1b[C":  # right arrow — jump to right column, same row
            split = (len(MENU) + 1) // 2
            if selected < split:
                j = split + selected
                if j < len(MENU):
                    selected = j
            num_buf = ""

        elif key == "\x1b[D":  # left arrow — jump to left column, same row
            split = (len(MENU) + 1) // 2
            if selected >= split:
                selected = selected - split
            num_buf = ""

        elif key == "\r" or key == "\n":  # Enter
            label, cmd_args, needs_input, prompt = MENU[selected]
            run_command(label, cmd_args, needs_input, prompt)
            num_buf = ""

        elif key.isdigit():
            num_buf += key
            n = int(num_buf)
            if 1 <= n <= len(MENU):
                selected = n - 1
                # If two digits possible, wait; if already max range, run immediately
                if n * 10 > len(MENU):
                    label, cmd_args, needs_input, prompt = MENU[selected]
                    run_command(label, cmd_args, needs_input, prompt)
                    num_buf = ""
            else:
                num_buf = ""


if __name__ == "__main__":
    main()
