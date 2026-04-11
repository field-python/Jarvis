#!/usr/bin/env python3
"""
download-tech-linux.py — Download Linux, networking, and tech troubleshooting content.
Run: Jarvis download-tech
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "tech")

TOPICS = [
    # Linux distros
    "Linux",
    "Linux Mint",
    "Ubuntu",
    "Debian",
    "Fedora Linux",
    "Arch Linux",
    "Kali Linux",
    "Pop! OS",
    "elementary OS",
    "Manjaro Linux",
    "Linux distribution",
    "Package manager",
    "APT (software)",
    "Snap (software)",
    "Flatpak",
    "GNOME",
    "KDE Plasma",
    "Xfce",
    "Linux kernel",
    "GNU",
    "Bash (Unix shell)",
    "Terminal emulator",

    # Networking and WiFi
    "Wi-Fi",
    "IEEE 802.11",
    "Wi-Fi router",
    "Network interface controller",
    "NetworkManager",
    "Domain Name System",
    "DHCP",
    "IP address",
    "IPv4",
    "IPv6",
    "Network troubleshooting",
    "Ping (networking utility)",
    "Traceroute",
    "Firewall (computing)",
    "Virtual private network",
    "Tailscale",
    "WireGuard",
    "Network address translation",
    "Subnet mask",
    "Default gateway",
    "DNS spoofing",
    "SSID",
    "WPA2",
    "WPA3",

    # General tech
    "Secure Shell",
    "Port forwarding",
    "Localhost",
    "Computer hardware",
    "Solid-state drive",
    "Random-access memory",
    "CPU",
    "GPU",
    "USB",
    "Bluetooth",
    "BIOS",
    "UEFI",
    "Dual boot",
    "Virtual machine",
    "VirtualBox",
    "Docker (software)",
    "Systemd",
    "Cron",
    "File system",
    "Ext4",
]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=5000):
    params = urllib.parse.urlencode({
        "action":         "query",
        "titles":         title,
        "prop":           "extracts",
        "explaintext":    "1",
        "exsectionformat":"plain",
        "format":         "json",
        "redirects":      "1",
        "exchars":        str(max_chars),
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data  = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        if page.get("pageid", -1) == -1:
            return None
        text = page.get("extract", "").strip()
        return text if len(text) > 150 else None
    except Exception as e:
        print(f"    warn: {title}: {e}")
        return None


def main():
    force = "--force" in sys.argv
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n[TECH / LINUX / NETWORKING]  {len(TOPICS)} topics  →  {OUTPUT_DIR}\n")

    total = 0
    for title in TOPICS:
        slug     = slugify(title)
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.md")

        if os.path.exists(out_path) and not force:
            print(f"  skip  {title}")
            continue

        print(f"  fetch {title}...", end=" ", flush=True)
        text = wiki_fetch(title)
        if not text:
            print("not found")
            continue

        header = f"# {title}\n\n*Source: Wikipedia*\n\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + text + "\n")
        print(f"ok ({len(text):,} chars)")
        total += 1
        time.sleep(0.3)

    print(f"\nDone — {total} articles downloaded.")
    print("Run 'Jarvis rebuild-index' to make them searchable.")


if __name__ == "__main__":
    main()
