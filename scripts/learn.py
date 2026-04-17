#!/usr/bin/env python3
"""
learn.py — Step-by-step interactive coding lessons with Jarvis
Usage: learn.py "topic"

Walks through a topic with explanations, examples, challenges, and feedback.
Uses qwen2.5-coder:7b for instruction quality.
"""

import sys
import os
import re
import readline
import select
import subprocess
import tempfile
import textwrap
import tty
import termios
from pathlib import Path
from datetime import date

script_dir = Path(__file__).parent.resolve()
base_dir   = script_dir.parent

venv_python    = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-venv")) + "/bin/python"
generate_script = str(base_dir / "scripts" / "generate.py")
host            = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
CODE_MODEL      = "qwen2.5-coder:7b"
LESSONS_DIR     = base_dir / "notes" / "lessons"

# Force local Ollama — qwen2.5-coder isn't available on Groq
CODE_ENV = {**os.environ, "JARVIS_BACKEND": "ollama", "JARVIS_THINK": "0"}

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def ask_model(prompt: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="jarvis-learn-", delete=False) as f:
        f.write(prompt)
        tmp = f.name
    try:
        result = subprocess.run(
            [venv_python, generate_script, CODE_MODEL, host, tmp],
            capture_output=True, text=True, env=CODE_ENV
        )
        return result.stdout.strip()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
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


def wrap(text: str, width: int = 72, indent: str = "  ") -> str:
    lines = text.splitlines()
    out = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(indent + line)
        elif in_code:
            out.append(indent + line)
        else:
            if len(line) > width:
                wrapped = textwrap.fill(line, width=width, initial_indent=indent, subsequent_indent=indent)
                out.append(wrapped)
            else:
                out.append(indent + line if line.strip() else "")
    return "\n".join(out)


def hr(char="━", width=50):
    print(f"{CYAN}{char * width}{RESET}")


def header(title: str):
    hr()
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    hr()


def save_session(topic: str, steps: list):
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y-%m-%d")
    slug = topic.lower().replace(" ", "-")[:40]
    out = LESSONS_DIR / f"{stamp}-{slug}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Lesson: {topic}\n\n*Date: {stamp}*\n\n")
        for i, step in enumerate(steps, 1):
            f.write(f"## Step {i}\n\n{step}\n\n")
    return out


def get_curriculum(topic: str) -> list:
    """Ask the model for a 5-step lesson plan."""
    prompt = f"""You are a patient coding tutor for a beginner.
Create a lesson plan for: {topic}

List exactly 5 lesson steps as a numbered list. Each step should be one short phrase (under 8 words).
Example format:
1. What a variable is and why
2. Assigning values to variables
3. Variable types: strings and numbers
4. Updating and reusing variables
5. Common beginner mistakes

Only output the numbered list. Nothing else."""
    raw = ask_model(prompt)
    steps = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            steps.append(line.split(".", 1)[1].strip())
    return steps[:5] if steps else [f"Introduction to {topic}",
                                     f"Core concepts",
                                     f"Writing your first code",
                                     f"Common patterns",
                                     f"Practice and review"]


def get_lesson_step(topic: str, step_title: str, step_num: int, total: int) -> str:
    """Generate content for one lesson step."""
    prompt = f"""You are teaching coding to a complete beginner who has never written code before.
Pretend you are explaining this to a curious 12-year-old. Use everyday words and real-life comparisons.

Topic: {topic}
Step {step_num} of {total}: {step_title}

Write exactly these three sections:

EXPLAIN:
[2-3 sentences in plain everyday English. Compare the concept to something from real life if possible.
Never use jargon without immediately explaining it in parentheses.]

EXAMPLE:
[3-8 lines of working code. Every single line must have a comment explaining what it does in plain English.]

CHALLENGE:
[One very specific task. Tell the student EXACTLY what to type and what result to expect.
Example: "Write a loop that prints the word Hello five times. When you run it, you should see Hello printed on five separate lines."]

Keep it simple. Short sentences. Be encouraging and friendly."""
    return ask_model(prompt)


def get_feedback(topic: str, challenge: str, student_answer: str) -> str:
    """Evaluate the student's attempt."""
    prompt = f"""You are a patient coding tutor reviewing a beginner's work.

Topic: {topic}
Challenge given: {challenge}
Student's attempt:
{student_answer}

Give feedback in exactly this format:

FEEDBACK:
[2-3 sentences: what they did right, what needs fixing, be encouraging]

SOLUTION:
[The clean, correct solution with brief comments]

If their answer was correct or close enough, say so clearly."""
    return ask_model(prompt)


def open_in_editor(challenge: str) -> str:
    """Open a temp file in the user's editor and return the typed code."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", prefix="jarvis-answer-", delete=False)
    tmp.write(f"# Challenge: {challenge}\n# Write your code below, save and close when done.\n\n")
    tmp.close()
    editor = os.environ.get("VISUAL", os.environ.get("EDITOR", "nano"))
    subprocess.run([editor, tmp.name])
    with open(tmp.name) as f:
        content = f.read()
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
    # Strip the comment header lines
    lines = [l for l in content.splitlines() if not l.startswith("# Challenge:") and not l.startswith("# Write your")]
    return "\n".join(lines).strip()


def flush_stdin():
    """Discard keystrokes buffered while waiting for the model."""
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass


def parse_section(text: str, section: str) -> str:
    """Extract a named section from model output, tolerating markdown-formatted headers."""
    lines = text.splitlines()
    capturing = False
    result = []
    all_keys = {"EXPLAIN", "EXAMPLE", "CHALLENGE", "FEEDBACK", "SOLUTION"}
    section_key = section.upper()
    for line in lines:
        # Strip non-alphanumeric chars so **EXPLAIN:** and EXPLAIN: both match
        norm = re.sub(r'[^A-Za-z0-9]', '', line).upper()
        if norm.startswith(section_key):
            capturing = True
            colon_idx = line.find(":")
            if colon_idx != -1:
                rest = re.sub(r'[*_`#]', '', line[colon_idx + 1:]).strip()
                if rest:
                    result.append(rest)
        elif capturing:
            if any(norm.startswith(k) for k in (all_keys - {section_key})):
                break
            result.append(line)
    return "\n".join(result).strip()


def print_section(label: str, content: str, color: str = RESET):
    print(f"\n{BOLD}{color}{label}{RESET}")
    print(wrap(content))


def run_lesson(topic: str):
    os.system("clear")
    header(f"Jarvis Learn  |  {topic}")
    print(f"\n  {DIM}Building your lesson plan...{RESET}\n")

    curriculum = get_curriculum(topic)

    print(f"  {BOLD}Your lesson plan:{RESET}")
    for i, step in enumerate(curriculum, 1):
        print(f"  {DIM}{i}.{RESET} {step}")
    print()
    r = input_with_esc(f"  {YELLOW}Press Enter to start  (ESC to exit) →{RESET} ")
    if r is None:
        return

    all_steps = []
    step_num = 0

    for step_num, step_title in enumerate(curriculum, 1):
        os.system("clear")
        header(f"Step {step_num}/{len(curriculum)}  |  {step_title}")
        print(f"\n  {DIM}Loading lesson...{RESET}", end="\r", flush=True)

        lesson = get_lesson_step(topic, step_title, step_num, len(curriculum))
        all_steps.append(f"### {step_title}\n\n{lesson}")

        explain  = parse_section(lesson, "EXPLAIN")
        example  = parse_section(lesson, "EXAMPLE")
        challenge = parse_section(lesson, "CHALLENGE")

        print(" " * 40, end="\r")  # clear loading line
        flush_stdin()              # discard keystrokes typed during model load

        if explain:
            print_section("Concept:", explain, CYAN)
        if example:
            print_section("Example:", example, GREEN)
        if challenge:
            print_section("Challenge:", challenge, YELLOW)

        task_line = challenge.splitlines()[0] if challenge else f"Write code demonstrating: {step_title}"
        print(f"\n{DIM}  Options: type code, 'e' open editor, 's' skip, 'h' hint, 'q' quit{RESET}\n")

        while True:
            # Always reprint the challenge as a reminder before each attempt
            print(f"  {BOLD}{YELLOW}Challenge:{RESET} {task_line}")
            print()

            try:
                lines = []
                print(f"  {YELLOW}Your answer (blank line to submit  |  ESC to exit):{RESET}")
                # First line: detect single-char commands immediately
                first = input_with_esc("  ")
                if first is None:   # ESC
                    print(f"\n  {DIM}Session saved. Come back anytime!{RESET}")
                    save_session(topic, all_steps)
                    return
                if first.strip().lower() in ("q", "s", "h", "e"):
                    student_input = first.strip().lower()
                else:
                    if first:
                        lines.append(first)
                    while True:
                        line = input_with_esc("  ")
                        if line is None:   # ESC
                            print(f"\n  {DIM}Session saved. Come back anytime!{RESET}")
                            save_session(topic, all_steps)
                            return
                        if line == "":
                            break
                        lines.append(line)
                    student_input = "\n".join(lines).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSession ended.")
                save_session(topic, all_steps)
                return

            if student_input.lower() == "q":
                print(f"\n  {DIM}Session saved. Come back anytime!{RESET}")
                save_session(topic, all_steps)
                return

            if student_input.lower() == "s":
                print(f"\n  {DIM}Skipped. Moving on.{RESET}")
                break

            if student_input.lower() == "h":
                print(f"\n  {DIM}Getting hint...{RESET}", flush=True)
                hint_context = task_line
                hint_prompt = (
                    f"You are a patient coding tutor helping a beginner.\n"
                    f"Topic: {topic}\n"
                    f"Step: {step_title}\n"
                    f"The challenge: {hint_context}\n\n"
                    f"Give exactly ONE sentence (under 15 words) as a concrete, specific hint "
                    f"that points toward the solution without giving it away. "
                    f"The hint must reference this exact challenge — no generic tips."
                )
                hint = ask_model(hint_prompt)
                print(f"  {CYAN}Hint: {hint}{RESET}\n")
                continue

            if student_input.lower() == "e":
                print(f"\n  {DIM}Opening editor...{RESET}")
                student_input = open_in_editor(task_line)
                if not student_input:
                    print(f"  {DIM}(empty — nothing to submit){RESET}\n")
                    continue
                print(f"\n  {DIM}Code from editor:{RESET}")
                print(wrap(student_input))
                print()

            if not student_input:
                print(f"  {DIM}(enter your code, 'e' for editor, or 's' to skip){RESET}")
                continue

            # Get feedback
            print(f"\n  {DIM}Checking your answer...{RESET}", end="\r", flush=True)
            feedback_raw = get_feedback(topic, challenge, student_input)
            feedback = parse_section(feedback_raw, "FEEDBACK")
            solution = parse_section(feedback_raw, "SOLUTION")

            print(" " * 40, end="\r")
            flush_stdin()
            if feedback:
                print_section("Feedback:", feedback, GREEN)
            if solution:
                print_section("Solution:", solution, CYAN)

            print()
            resp = input_with_esc(f"  {YELLOW}Try again? [y/N]  (ESC to exit) {RESET}")
            if resp is None:
                save_session(topic, all_steps)
                return
            if resp.strip().lower() != "y":
                break

        if step_num < len(curriculum):
            r = input_with_esc(f"\n  {YELLOW}Press Enter for Step {step_num + 1}  (ESC to exit) →{RESET} ")
            if r is None:
                save_session(topic, all_steps)
                return

    # Final summary
    os.system("clear")
    header(f"Lesson Complete  |  {topic}")
    print(f"\n  {GREEN}{BOLD}Great work! You've covered all {len(curriculum)} steps.{RESET}\n")

    saved = save_session(topic, all_steps)
    print(f"  {DIM}Session saved to: {saved}{RESET}\n")

    print(f"  {BOLD}What you learned:{RESET}")
    for i, step in enumerate(curriculum, 1):
        print(f"  {GREEN}✓{RESET} {step}")

    print(f"\n  {DIM}Next: try 'Jarvis code' to build something using these skills.{RESET}\n")


def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage:{RESET} Jarvis learn \"topic\"")
        print()
        print("Examples:")
        print("  Jarvis learn \"Python for loops\"")
        print("  Jarvis learn \"bash scripting basics\"")
        print("  Jarvis learn \"Python functions\"")
        print("  Jarvis learn \"reading and writing files in Python\"")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    run_lesson(topic)


if __name__ == "__main__":
    main()
