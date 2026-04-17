#!/usr/bin/env python3
"""
diagnose.py — Run system diagnostics and get Jarvis's analysis.
Usage: Jarvis diagnose [--wifi | --disk | --memory | --network | --full]
"""

import sys
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

script_dir      = Path(__file__).parent.resolve()
base_dir        = script_dir.parent
generate_script = str(base_dir / "scripts" / "generate.py")

venv_python = os.environ.get("JARVIS_VENV", str(Path.home() / ".jarvis-venv")) + "/bin/python"
model       = "Jarvis"   # always use local model — diagnostics never go to groq
host        = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def hr(width=56):
    print(f"{CYAN}{'━' * width}{RESET}")


def header(title):
    hr()
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    hr()


def run_cmd(cmd, timeout=10):
    """Run a shell command and return its stdout, or '' on failure."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception:
        return ""


def section(label, content):
    if content:
        print(f"\n{BOLD}{YELLOW}{label}{RESET}")
        for line in content.splitlines():
            print(f"  {line}")


def gather_cpu():
    out = run_cmd("lscpu | grep -E 'Model name|CPU\\(s\\)|Thread|MHz|Architecture'")
    if not out:
        out = run_cmd("cat /proc/cpuinfo | grep 'model name' | head -1")
    return out


def gather_memory():
    return run_cmd("free -h")


def gather_disk():
    return run_cmd("df -h --output=target,size,used,avail,pcent | head -20")


def gather_network():
    ifaces = run_cmd("ip -brief addr show")
    dns    = run_cmd("cat /etc/resolv.conf | grep nameserver")
    gw     = run_cmd("ip route show default")
    return f"Interfaces:\n{ifaces}\n\nDNS:\n{dns}\n\nDefault route:\n{gw}"


def gather_wifi():
    lines = []

    nmcli_dev = run_cmd("nmcli device status 2>/dev/null")
    if nmcli_dev:
        lines.append("Device status:")
        lines.append(nmcli_dev)

    wifi_list = run_cmd(
        "nmcli -f SSID,SIGNAL,SECURITY,BARS,ACTIVE device wifi list 2>/dev/null | head -20"
    )
    if wifi_list:
        lines.append("\nNearby WiFi networks:")
        lines.append(wifi_list)

    active = run_cmd(
        "nmcli -f NAME,TYPE,DEVICE,STATE connection show --active 2>/dev/null"
    )
    if active:
        lines.append("\nActive connections:")
        lines.append(active)

    # Try iw if nmcli isn't available
    if not nmcli_dev:
        iw = run_cmd("iw dev 2>/dev/null")
        if iw:
            lines.append("iw dev:")
            lines.append(iw)

    return "\n".join(lines) if lines else "Could not read WiFi info (nmcli/iw not found)"


def gather_internet():
    results = []
    # Ping test
    ping = run_cmd("ping -c 2 -W 3 8.8.8.8 2>&1", timeout=8)
    results.append(f"Ping 8.8.8.8:\n{ping}")

    dns_ping = run_cmd("ping -c 2 -W 3 google.com 2>&1", timeout=8)
    results.append(f"\nPing google.com (DNS test):\n{dns_ping}")

    return "\n".join(results)


def gather_temps():
    sensors = run_cmd("sensors 2>/dev/null")
    if sensors:
        return sensors
    # Fallback: read thermal zones directly
    tz = run_cmd("for f in /sys/class/thermal/thermal_zone*/temp; do echo \"$f: $(cat $f)\"; done 2>/dev/null")
    if tz:
        return "Thermal zones (raw millidegrees C):\n" + tz
    return "Temperature sensors not available (install lm-sensors)"


def gather_services():
    return run_cmd(
        "systemctl is-active NetworkManager ollama ssh bluetooth 2>/dev/null | "
        "paste - - - - | awk '{print NR\": \"$0}' | "
        "sed 's/1:/NetworkManager /; s/2:/ollama /; s/3:/ssh /; s/4:/bluetooth /'"
    )


def ask_jarvis_analysis(report: str) -> None:
    prompt = (
        "You are Jarvis, an AI assistant helping a user troubleshoot their Linux computer.\n\n"
        "Below is a system diagnostic report. Analyze it and:\n"
        "1. Note anything that looks concerning (high disk usage, failed services, no internet, weak WiFi, etc.)\n"
        "2. If everything looks healthy, say so briefly\n"
        "3. Give 2-3 specific actionable suggestions based on what you see\n"
        "4. Keep the response concise — plain text, no markdown headers, no bullet points with asterisks\n\n"
        f"DIAGNOSTIC REPORT:\n{report}"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="jarvis-diag-", delete=False
    )
    tmp.write(prompt)
    tmp.close()
    try:
        subprocess.run(
            [venv_python, generate_script, model, host, tmp.name],
            env={**os.environ, "JARVIS_BACKEND": "ollama", "JARVIS_THINK": "0"},
        )
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def main():
    mode = "full"
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            mode = arg.lstrip("-")

    valid = {"full", "wifi", "disk", "memory", "network", "internet"}
    if mode not in valid:
        mode = "full"

    os.system("clear")
    header(f"Jarvis Diagnostics  |  {mode.upper()}")
    print(f"\n  {DIM}Gathering system info...{RESET}\n")

    report_parts = []

    if mode in ("full", "cpu"):
        cpu = gather_cpu()
        section("CPU", cpu)
        report_parts.append(f"CPU:\n{cpu}")

    if mode in ("full", "memory"):
        mem = gather_memory()
        section("Memory", mem)
        report_parts.append(f"Memory:\n{mem}")

    if mode in ("full", "disk"):
        disk = gather_disk()
        section("Disk Usage", disk)
        report_parts.append(f"Disk:\n{disk}")

    if mode in ("full", "network", "wifi"):
        wifi = gather_wifi()
        section("WiFi / Network Devices", wifi)
        report_parts.append(f"WiFi:\n{wifi}")

    if mode in ("full", "network", "internet"):
        inet = gather_internet()
        section("Internet Connectivity", inet)
        report_parts.append(f"Internet:\n{inet}")

    if mode in ("full",):
        temps = gather_temps()
        section("Temperature", temps)
        report_parts.append(f"Temperature:\n{temps}")

        svcs = gather_services()
        if svcs:
            section("Key Services (NetworkManager / ollama / ssh / bluetooth)", svcs)
            report_parts.append(f"Services:\n{svcs}")

    full_report = "\n\n".join(report_parts)

    print(f"\n\n{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}  Jarvis Analysis{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    ask_jarvis_analysis(full_report)
    print(f"\n{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")


if __name__ == "__main__":
    main()
