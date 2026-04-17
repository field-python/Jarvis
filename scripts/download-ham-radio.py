#!/usr/bin/env python3
"""
download-ham-radio.py — Download amateur radio, communications, electronics,
                         antennas, propagation, and radio emergency services content.

Run: Jarvis download-ham-radio [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "ham-radio")

TOPICS = {
    "ham-radio-basics": [
        "Amateur radio",
        "Ham radio",
        "Amateur radio licensing in the United States",
        "Technician class license",
        "General class license",
        "Amateur Extra class license",
        "FCC",
        "Callsign",
        "Q code",
        "Phonetic alphabet",
        "NATO phonetic alphabet",
        "Morse code",
        "Continuous wave",
        "Transceiver",
        "Receiver (radio)",
        "Transmitter",
        "Repeater (radio)",
        "Simplex",
        "Duplex (telecommunications)",
        "CTCSS",
        "DTMF",
        "Radio frequency",
        "Frequency band",
        "HF",
        "VHF",
        "UHF",
        "Shortwave radio",
        "2-meter band",
        "70-centimeter band",
        "Band plan (radio)",
        "RF power",
        "SWR",
        "Ohm's law",
    ],
    "antennas": [
        "Antenna (radio)",
        "Dipole antenna",
        "Vertical antenna",
        "Yagi–Uda antenna",
        "Beam antenna",
        "Loop antenna",
        "Magnetic loop antenna",
        "Wire antenna",
        "End-fed half-wave antenna",
        "Random wire antenna",
        "Ground plane antenna",
        "J-pole antenna",
        "Slim Jim antenna",
        "Antenna gain",
        "Directivity",
        "Feed line",
        "Coaxial cable",
        "Ladder line",
        "Balun",
        "Unun",
        "Impedance matching",
        "Antenna tuner",
        "SWR meter",
        "Radiation pattern",
        "Polarization (antenna)",
        "Antenna height",
        "Ground (electricity)",
        "Counterpoise",
        "Mobile antenna",
        "Portable antenna",
        "EFHW",
        "Inverted-V antenna",
    ],
    "propagation": [
        "Radio propagation",
        "Ionosphere",
        "Ionospheric propagation",
        "Skywave",
        "Ground wave",
        "Line-of-sight propagation",
        "Tropospheric propagation",
        "Sporadic E",
        "F-layer",
        "E-layer",
        "D-layer",
        "Solar cycle",
        "Solar flux index",
        "Sunspot",
        "Geomagnetic storm",
        "Aurora",
        "Multipath propagation",
        "Troposcatter",
        "Moonbounce",
        "Meteor scatter",
        "DX (telecommunications)",
        "DXing",
        "Grey line",
        "Critical frequency",
        "Maximum usable frequency",
        "Lowest usable frequency",
        "Path loss",
        "Fading",
        "Noise figure",
        "Signal-to-noise ratio",
    ],
    "emergency-comms": [
        "Amateur Radio Emergency Service",
        "RACES",
        "ARES",
        "SKYWARN",
        "Emergency communications",
        "Net (radio)",
        "Emergency net",
        "Traffic net",
        "Message handling",
        "Radiogram",
        "National Traffic System",
        "Winlink",
        "Packet radio",
        "APRS",
        "Automatic Packet Reporting System",
        "Digital modes",
        "FT8",
        "JS8Call",
        "Olivia MFSK",
        "RTTY",
        "Pactor",
        "Portable operation",
        "Go kit",
        "POTA",
        "SOTA",
        "Battery operation",
        "Solar power for radio",
        "Handheld transceiver",
        "GMRS",
        "FRS",
        "CB radio",
        "MURS",
    ],
    "electronics-basics": [
        "Electronics",
        "Electronic component",
        "Resistor",
        "Capacitor",
        "Inductor",
        "Diode",
        "Transistor",
        "Integrated circuit",
        "Operational amplifier",
        "Voltage regulator",
        "Power supply",
        "Battery",
        "Soldering",
        "Printed circuit board",
        "Breadboard",
        "Multimeter",
        "Oscilloscope",
        "Frequency counter",
        "Spectrum analyzer",
        "Signal generator",
        "Ohm's law",
        "Kirchhoff's circuit laws",
        "Voltage divider",
        "RC circuit",
        "LC circuit",
        "Resonance",
        "Impedance",
        "Decibel",
        "Gain",
        "Amplifier",
        "Filter (signal processing)",
        "Low-pass filter",
        "High-pass filter",
        "Band-pass filter",
    ],
    "radio-modes": [
        "Amplitude modulation",
        "Frequency modulation",
        "Single-sideband modulation",
        "Upper sideband",
        "Lower sideband",
        "Phase modulation",
        "Digital mode",
        "FT8",
        "FT4",
        "PSK31",
        "WSPR",
        "JT65",
        "Olivia (digital mode)",
        "SSTV",
        "Slow-scan television",
        "ATV",
        "Fast-scan television",
        "DMR (radio)",
        "D-STAR",
        "System Fusion",
        "P25",
        "APCO Project 25",
        "EchoLink",
        "AllStar Link",
        "Internet radio linking project",
        "Satellite communication",
        "AMSAT",
        "Linear transponder",
        "Fox-1 satellite",
        "ISS ham radio",
    ],
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=6000):
    params = urllib.parse.urlencode({
        "action":          "query",
        "titles":          title,
        "prop":            "extracts",
        "explaintext":     "1",
        "exsectionformat": "plain",
        "format":          "json",
        "redirects":       "1",
        "exchars":         str(max_chars),
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
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force  = "--force" in sys.argv

    if target == "all":
        cats = list(TOPICS.keys())
    elif target in TOPICS:
        cats = [target]
    else:
        print(f"Unknown category: {target}")
        print(f"Available: {', '.join(TOPICS.keys())}, all")
        sys.exit(1)

    grand_total = 0
    for cat in cats:
        out_dir = os.path.join(OUTPUT_DIR, cat)
        os.makedirs(out_dir, exist_ok=True)
        pages = TOPICS[cat]
        print(f"\n[{cat.upper()}]  {len(pages)} topics  →  {out_dir}")

        for title in pages:
            slug     = slugify(title)
            out_path = os.path.join(out_dir, f"{slug}.md")

            if os.path.exists(out_path) and not force:
                print(f"  skip  {title}")
                continue

            print(f"  fetch {title}...", end=" ", flush=True)
            text = wiki_fetch(title)
            if not text:
                print("not found")
                continue

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Source: Wikipedia*\n\n{text}\n")
            print(f"ok ({len(text):,} chars)")
            grand_total += 1
            time.sleep(0.3)

    print(f"\nDone — {grand_total} articles downloaded.")
    print("Run 'Jarvis rebuild-index' to make them searchable.")


if __name__ == "__main__":
    main()
