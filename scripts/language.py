#!/usr/bin/env python3
"""
language.py — Jarvis Language Hub
Top 10 North American languages with learning tools for each.
Usage: Jarvis language
"""

import sys
import os
import io
import re
import readline
import select
import subprocess
import tempfile
import tty
import termios
import textwrap
from pathlib import Path
from datetime import datetime

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")

model = os.environ.get("JARVIS_MODEL", "Jarvis")
host  = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

LANGUAGES = [
    ("Spanish",          "~200M speakers in North America"),
    ("French",           "~12M in Canada + Louisiana"),
    ("Mandarin Chinese", "~5M in US & Canada"),
    ("Tagalog",          "~2M — most spoken Asian language in the US"),
    ("Vietnamese",       "~1.5M in US"),
    ("Arabic",           "~1.3M in US & Canada"),
    ("Korean",           "~1.2M in US & Canada"),
    ("Portuguese",       "~1M in US & Canada"),
    ("Hindi",            "~900K in US & Canada"),
    ("English (ESL)",    "For non-English speakers learning English"),
]

LANG_MENU = [
    ("Learn",          "Structured lessons — vocabulary, grammar, and practice"),
    ("Dictionary",     "Translate and look up words or phrases"),
    ("Common Phrases", "Essential phrases for greetings, food, travel, emergencies"),
    ("Grammar Guide",  "Key grammar rules and patterns for English speakers"),
    ("Tips & Tricks",  "How to learn this language faster — strategies and resources"),
]


# ── Terminal helpers ──────────────────────────────────────────────────────────

def flush_stdin():
    """Discard keystrokes buffered while waiting for the model."""
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass


def input_with_esc(prompt_str):
    """Like input() but returns None if ESC is pressed."""
    sys.stdout.write(prompt_str)
    sys.stdout.flush()
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    _vlen = len(re.sub(r"\x1b\[[0-9;]*m", "", prompt_str))
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(2)
                    continue
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buf)
            elif ch in ("\x7f", "\x08"):
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
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def getch():
    import select as _sel, os as _os
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = _os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            r, _, _ = _sel.select([fd], [], [], 0.1)
            if r:
                rest = _os.read(fd, 2).decode("utf-8", errors="replace")
                return "\x1b" + rest   # e.g. "\x1b[A"
            return "\x1b"              # plain ESC
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def hr(width=56):
    print(f"{CYAN}{'━' * width}{RESET}")


def header(title: str):
    hr()
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    hr()


def wrap(text: str, width: int = 68, indent: str = "  ") -> str:
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(indent + line)
        elif in_fence or len(line.strip()) == 0:
            out.append(indent + line if line.strip() else "")
        elif len(line) <= width:
            out.append(indent + line)
        else:
            out.append(textwrap.fill(
                line, width=width,
                initial_indent=indent, subsequent_indent=indent
            ))
    return "\n".join(out)


# ── AI helpers ────────────────────────────────────────────────────────────────

def ask_model(prompt: str) -> str:
    """Run model silently and return full text."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-lang-", delete=False
    )
    tmp.write(prompt)
    tmp.close()
    try:
        result = subprocess.run(
            [sys.executable, generate_script, model, host, tmp.name],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    finally:
        try: os.unlink(tmp.name)
        except OSError: pass


def stream_model(prompt: str) -> str:
    """Stream model output to terminal and return full text."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-lang-", delete=False
    )
    tmp.write(prompt)
    tmp.close()
    try:
        proc = subprocess.Popen(
            [sys.executable, generate_script, model, host, tmp.name],
            stdout=subprocess.PIPE, text=True
        )
        buf = io.StringIO()
        for ch in iter(lambda: proc.stdout.read(1), ""):
            sys.stdout.write(ch)
            sys.stdout.flush()
            buf.write(ch)
        proc.wait()
        return buf.getvalue()
    finally:
        try: os.unlink(tmp.name)
        except OSError: pass


def save_note(lang: str, topic: str, content: str):
    out_dir = base_dir / "notes" / "language"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug  = lang.lower().replace(" ", "-").replace("(", "").replace(")", "")
    stamp = datetime.now().strftime("%Y-%m-%d")
    fname = f"{stamp}-{slug}-{topic}.md"
    out   = out_dir / fname
    out.write_text(
        f"# {lang} — {topic.replace('-', ' ').title()}\n\n"
        f"*Generated: {stamp}*\n\n{content}\n",
        encoding="utf-8"
    )
    return out


# ── Language selection screen ─────────────────────────────────────────────────

def draw_lang_select(selected: int):
    os.system("clear")
    header("Jarvis Language Hub  |  Choose a Language")
    print()
    for i, (lang, note) in enumerate(LANGUAGES):
        num = f"{i + 1:>2}."
        if i == selected:
            print(f"  {BOLD}{GREEN}{num} ▶  {lang:<18}{RESET}  {GREEN}{DIM}{note}{RESET}")
        else:
            print(f"  {DIM}{num}    {lang:<18}  {note}{RESET}")
    print()
    print(f"  {DIM}↑↓ or 1-{len(LANGUAGES)} to select  |  Enter to open  |  Q to quit{RESET}")
    print()


# ── Language sub-menu ─────────────────────────────────────────────────────────

def draw_lang_menu(lang: str, selected: int):
    os.system("clear")
    header(f"Jarvis Language Hub  |  {lang}")
    print()
    for i, (label, desc) in enumerate(LANG_MENU):
        num = f"{i + 1}."
        if i == selected:
            print(f"  {BOLD}{GREEN}  {num} ▶  {label}{RESET}")
        else:
            print(f"  {DIM}  {num}    {label}{RESET}")
    print()
    # Show description for selected item below the list
    sel_desc = LANG_MENU[selected][1]
    if sel_desc:
        print(f"  {YELLOW}{sel_desc}{RESET}")
    print(f"  {DIM}↑↓ or 1-{len(LANG_MENU)} to select  |  Enter to run  |  B back  |  Q quit{RESET}")
    print()


# ── Feature: Learn ────────────────────────────────────────────────────────────

def feature_learn(lang: str):
    os.system("clear")
    header(f"Learn {lang}  |  Building your lesson plan...")
    print()

    plan_prompt = (
        f"You are a friendly language tutor. Create a beginner lesson plan for learning {lang}.\n\n"
        f"List exactly 5 lesson topics as a numbered list. Each topic should be one short phrase (under 8 words).\n"
        f"Cover the essentials: greetings, numbers, common verbs, daily phrases, asking for help.\n"
        f"Only output the numbered list. Nothing else."
    )
    raw    = ask_model(plan_prompt)
    topics = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            topics.append(line.split(".", 1)[1].strip())
    if not topics:
        topics = [
            "Greetings and introductions",
            "Numbers and basic expressions",
            "Essential verbs and present tense",
            "Food, shopping, and daily life",
            "Asking questions and directions",
        ]

    os.system("clear")
    header(f"Learn {lang}")
    print(f"\n  {BOLD}Your lesson plan:{RESET}")
    for i, t in enumerate(topics, 1):
        print(f"  {DIM}{i}.{RESET} {t}")
    print()
    flush_stdin()
    r = input_with_esc(f"  {YELLOW}Press Enter to start  (ESC to exit) →{RESET} ")
    if r is None:
        return

    all_steps = []

    for step_num, topic in enumerate(topics, 1):
        os.system("clear")
        header(f"Step {step_num}/{len(topics)}  |  {topic}")
        print(f"\n  {DIM}Loading lesson...{RESET}", end="\r", flush=True)

        lesson_prompt = (
            f"You are teaching {lang} to a complete English-speaking beginner.\n\n"
            f"Topic: {topic} (Lesson {step_num} of {len(topics)})\n\n"
            f"Write exactly these three sections. Use PLAIN TEXT headers exactly as shown — "
            f"no bold, no markdown, no hashtags:\n\n"
            f"EXPLAIN:\n"
            f"[2-3 sentences in plain English. Compare to English patterns where helpful.]\n\n"
            f"VOCABULARY:\n"
            f"[6-8 key words or phrases. Format each line as:\n"
            f"{lang} word — English meaning — pronunciation (romanized if non-Latin script)]\n\n"
            f"PRACTICE:\n"
            f"[3 example sentences or short dialogues. Show {lang} first, English in parentheses.]\n\n"
            f"Keep it encouraging, practical, and beginner-friendly."
        )
        lesson = ask_model(lesson_prompt)
        all_steps.append(f"### {topic}\n\n{lesson}")
        print(" " * 50, end="\r")

        def extract(text, section):
            """Extract a named section, tolerating bold/markdown formatting on headers."""
            lines       = text.splitlines()
            capturing   = False
            result      = []
            all_keys    = {"EXPLAIN", "VOCABULARY", "PRACTICE"}
            section_key = section.upper()

            for line in lines:
                # Strip all non-alphanumeric chars for reliable header detection
                norm = re.sub(r'[^A-Za-z0-9]', '', line).upper()

                if norm.startswith(section_key):
                    capturing = True
                    colon_idx = line.find(":")
                    if colon_idx != -1:
                        rest = re.sub(r'[*_`#]', '', line[colon_idx + 1:]).strip()
                        if rest:
                            result.append(rest)
                elif capturing:
                    other_keys = all_keys - {section_key}
                    if any(norm.startswith(k) for k in other_keys):
                        break
                    result.append(line)
            return "\n".join(result).strip()

        explain  = extract(lesson, "EXPLAIN")
        vocab    = extract(lesson, "VOCABULARY")
        practice = extract(lesson, "PRACTICE")

        flush_stdin()  # discard keystrokes typed while model was loading

        # Fallback: if section parsing failed, show the full raw response
        if not explain and not vocab and not practice:
            print(wrap(lesson))

        if explain:
            print(f"\n{BOLD}{CYAN}Explanation:{RESET}")
            print(wrap(explain))
        if vocab:
            print(f"\n{BOLD}{GREEN}Vocabulary:{RESET}")
            print(wrap(vocab))
        if practice:
            print(f"\n{BOLD}{YELLOW}Practice — say these aloud:{RESET}")
            print(wrap(practice))
        print()

        if step_num < len(topics):
            r = input_with_esc(f"  {YELLOW}Press Enter for Step {step_num + 1}  (ESC to exit) →{RESET} ")
        else:
            r = input_with_esc(f"  {GREEN}Press Enter to finish  (ESC to exit) →{RESET} ")
        if r is None:
            break

    # ── End of lesson ──────────────────────────────────────────────────────────
    os.system("clear")
    header(f"Lesson Complete  |  {lang}")
    print(f"\n  {GREEN}{BOLD}Great work! You covered all {len(topics)} topics.{RESET}")
    print(f"\n  {DIM}Tip: revisit these lessons in a few days to reinforce what you learned.{RESET}")
    print(f"  {DIM}Consistency beats intensity — even 10 minutes a day adds up fast.{RESET}\n")

    try:
        sv = input(f"  {YELLOW}Save lesson notes? [y/N]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sv = ""
    if sv == "y":
        content  = "\n\n".join(all_steps)
        out_file = save_note(lang, "lesson", content)
        print(f"  {DIM}Saved to: {out_file}{RESET}\n")

    input_with_esc(f"  {DIM}Press Enter to return to menu  (ESC also works)...{RESET}")


# ── Feature: Dictionary ───────────────────────────────────────────────────────

def feature_dictionary(lang: str):
    os.system("clear")
    header(f"{lang} Dictionary")
    print()
    print(f"  Type a word or phrase in English or {lang}.")
    print(f"  Jarvis will translate and explain it.")
    print(f"  {DIM}Type 'back' or press Enter on an empty line to return.{RESET}")
    print()

    while True:
        try:
            word = input(f"  {YELLOW}Look up: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if not word or word.lower() in ("back", "b", "exit", "quit"):
            return

        print(f"\n  {DIM}Looking up '{word}'...{RESET}\n")

        prompt = (
            f"You are a {lang} language dictionary and tutor.\n\n"
            f'Look up: "{word}"\n\n'
            f"Provide a clear reference entry with:\n\n"
            f"TRANSLATION\n"
            f"The {lang} equivalent (or English if input is in {lang})\n\n"
            f"PRONUNCIATION\n"
            f"Romanized pronunciation guide (include for all languages, especially important for Arabic, Chinese, Korean, Hindi, Vietnamese)\n\n"
            f"PART OF SPEECH\n"
            f"(noun, verb, adjective, phrase, etc.)\n\n"
            f"MEANING\n"
            f"Clear definition in 1-2 sentences\n\n"
            f"EXAMPLE\n"
            f"One natural sentence in {lang} using this word, with English translation below\n\n"
            f"RELATED\n"
            f"2-3 related words or common phrases using this word\n\n"
            f"If the word is ambiguous, give the most common meaning first."
        )

        stream_model(prompt)
        print("\n")


# ── Feature: Common Phrases ───────────────────────────────────────────────────

def feature_phrases(lang: str):
    os.system("clear")
    header(f"{lang} Common Phrases")
    print(f"\n  {DIM}Generating essential phrases — this may take a moment...{RESET}\n")

    prompt = (
        f"You are a {lang} language expert. Generate a practical phrase reference sheet.\n\n"
        f"For each phrase show:\n"
        f"{lang} phrase | English meaning | Pronunciation (romanized)\n\n"
        f"Include these 5 categories with 6 phrases each:\n\n"
        f"GREETINGS & INTRODUCTIONS\n"
        f"(hello, goodbye, how are you, my name is, nice to meet you, please / thank you)\n\n"
        f"NUMBERS & SHOPPING\n"
        f"(one through ten, how much does this cost, too expensive, I'll take it, "
        f"do you have...?, receipt please)\n\n"
        f"FOOD & DINING\n"
        f"(I'm hungry, a table for two, the menu please, I would like..., "
        f"it's delicious, the bill please)\n\n"
        f"GETTING AROUND\n"
        f"(where is...?, turn left / right, straight ahead, how far is it?, "
        f"I'm lost, please call a taxi)\n\n"
        f"EMERGENCIES\n"
        f"(help!, I need a doctor, call the police, I don't understand, "
        f"do you speak English?, I'm allergic to...)\n\n"
        f"Make pronunciation guides intuitive for English speakers."
    )

    result = stream_model(prompt)
    print("\n")

    try:
        sv = input(f"  {YELLOW}Save phrase sheet to file? [y/N]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sv = ""
    if sv == "y":
        out_file = save_note(lang, "common-phrases", result)
        print(f"  {DIM}Saved to: {out_file}{RESET}\n")

    input_with_esc(f"  {DIM}Press Enter to return to menu  (ESC also works)...{RESET}")


# ── Feature: Grammar Guide ────────────────────────────────────────────────────

def feature_grammar(lang: str):
    os.system("clear")
    header(f"{lang} Grammar Guide")
    print(f"\n  {DIM}Generating grammar guide — this may take a moment...{RESET}\n")

    prompt = (
        f"You are a {lang} grammar expert writing a cheat sheet for English speakers.\n\n"
        f"SENTENCE STRUCTURE\n"
        f"How sentences are built in {lang} — word order, key differences from English.\n"
        f"Show 2 example sentences.\n\n"
        f"VERBS & TENSES\n"
        f"How verbs work in {lang}. Show the 5 most essential verbs conjugated in present tense.\n"
        f"Note any tense quirks English speakers find confusing.\n\n"
        f"NOUNS & MODIFIERS\n"
        f"Gender (if applicable), plurals, adjective placement. Show examples.\n\n"
        f"5 ESSENTIAL PATTERNS\n"
        f"The 5 most useful grammar patterns in {lang} for a beginner.\n"
        f"For each: pattern name, formula, and 2 examples.\n\n"
        f"COMMON MISTAKES\n"
        f"4 mistakes English speakers commonly make in {lang}, and how to avoid them.\n\n"
        f"Keep every rule backed by a short example. Beginner-friendly language only."
    )

    result = stream_model(prompt)
    print("\n")

    try:
        sv = input(f"  {YELLOW}Save grammar guide to file? [y/N]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sv = ""
    if sv == "y":
        out_file = save_note(lang, "grammar-guide", result)
        print(f"  {DIM}Saved to: {out_file}{RESET}\n")

    input_with_esc(f"  {DIM}Press Enter to return to menu  (ESC also works)...{RESET}")


# ── Feature: Tips & Tricks ────────────────────────────────────────────────────

def feature_tips(lang: str):
    os.system("clear")
    header(f"Tips & Tricks  |  Learning {lang} Faster")
    print(f"\n  {DIM}Generating learning guide...{RESET}\n")

    prompt = (
        f"You are a language learning expert. Write a practical guide for an English speaker learning {lang}.\n\n"
        f"WHY {lang.upper()} IS WORTH LEARNING\n"
        f"2-3 sentences on real benefits and opportunities.\n\n"
        f"DIFFICULTY & REALISTIC TIMELINE\n"
        f"How hard is {lang} for English speakers (be honest)? "
        f"Rough weeks/months to reach basic conversation.\n\n"
        f"TOP 5 TIPS SPECIFIC TO {lang.upper()}\n"
        f"Actionable advice specific to THIS language — not generic language advice.\n"
        f"Address the real challenges English speakers face with {lang}.\n\n"
        f"DAILY PRACTICE PLAN (15-20 MINUTES)\n"
        f"A simple daily routine that actually works. Be specific about what to do each day.\n\n"
        f"FREE RESOURCES\n"
        f"4-5 genuinely useful free resources (apps, YouTube channels, websites).\n"
        f"Name them specifically — Duolingo, Anki, specific YouTube channels, etc.\n\n"
        f"MEMORY TRICKS & HACKS\n"
        f"3-4 clever tricks specific to {lang} — mnemonics, patterns, shortcuts that "
        f"experienced learners use.\n\n"
        f"Be specific to {lang}. Generic advice that applies to any language is not useful here."
    )

    result = stream_model(prompt)
    print("\n")

    try:
        sv = input(f"  {YELLOW}Save tips to file? [y/N]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sv = ""
    if sv == "y":
        out_file = save_note(lang, "tips-and-tricks", result)
        print(f"  {DIM}Saved to: {out_file}{RESET}\n")

    input_with_esc(f"  {DIM}Press Enter to return to menu  (ESC also works)...{RESET}")


# ── Sub-menu navigator ────────────────────────────────────────────────────────

def lang_submenu(lang: str):
    selected = 0
    num_buf  = ""

    while True:
        draw_lang_menu(lang, selected)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            return

        elif key in ("b", "B"):
            return

        elif key == "\x1b[A":   # up
            selected = (selected - 1) % len(LANG_MENU)
            num_buf  = ""

        elif key == "\x1b[B":   # down
            selected = (selected + 1) % len(LANG_MENU)
            num_buf  = ""

        elif key in ("\r", "\n"):
            label = LANG_MENU[selected][0]
            if label == "Learn":
                feature_learn(lang)
            elif label == "Dictionary":
                feature_dictionary(lang)
            elif label == "Common Phrases":
                feature_phrases(lang)
            elif label == "Grammar Guide":
                feature_grammar(lang)
            elif label == "Tips & Tricks":
                feature_tips(lang)
            num_buf = ""

        elif key.isdigit():
            num_buf += key
            n = int(num_buf)
            if 1 <= n <= len(LANG_MENU):
                selected = n - 1
                if n * 10 > len(LANG_MENU):
                    label = LANG_MENU[selected][0]
                    if label == "Learn":           feature_learn(lang)
                    elif label == "Dictionary":    feature_dictionary(lang)
                    elif label == "Common Phrases":feature_phrases(lang)
                    elif label == "Grammar Guide": feature_grammar(lang)
                    elif label == "Tips & Tricks": feature_tips(lang)
                    num_buf = ""
            else:
                num_buf = ""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    selected = 0
    num_buf  = ""

    while True:
        draw_lang_select(selected)
        key = getch()

        if key in ("q", "Q", "\x1b", "\x03"):
            os.system("clear")
            return

        elif key == "\x1b[A":   # up
            selected = (selected - 1) % len(LANGUAGES)
            num_buf  = ""

        elif key == "\x1b[B":   # down
            selected = (selected + 1) % len(LANGUAGES)
            num_buf  = ""

        elif key in ("\r", "\n"):
            lang = LANGUAGES[selected][0]
            lang_submenu(lang)
            num_buf = ""

        elif key.isdigit():
            num_buf += key
            n = int(num_buf)
            if 1 <= n <= len(LANGUAGES):
                selected = n - 1
                if n * 10 > len(LANGUAGES):
                    lang_submenu(LANGUAGES[selected][0])
                    num_buf = ""
            else:
                num_buf = ""


if __name__ == "__main__":
    main()
