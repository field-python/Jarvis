#!/usr/bin/env python3
"""
download-misc.py — Download law, finance, astronomy, mythology, philosophy,
                   psychology, true crime, military history, and automotive content.
Run: Jarvis download-misc [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "misc")

TOPICS = {
    "law-rights": [
        "United States Constitution",
        "Bill of Rights (United States)",
        "First Amendment to the United States Constitution",
        "Second Amendment to the United States Constitution",
        "Fourth Amendment to the United States Constitution",
        "Fifth Amendment to the United States Constitution",
        "Miranda warning",
        "Due process",
        "Habeas corpus",
        "Probable cause",
        "Search warrant",
        "Plea bargain",
        "Jury trial",
        "Supreme Court of the United States",
        "Federal judiciary of the United States",
        "United States federal law",
        "Criminal law",
        "Civil law (common law)",
        "Contract",
        "Tort",
        "Intellectual property",
        "Copyright",
        "Self-defense (legal)",
        "Castle doctrine",
        "Stand-your-ground law",
        "Statute of limitations",
        "Class action",
        "Public defender",
    ],
    "finance": [
        "Personal finance",
        "Budgeting",
        "Saving",
        "Investment",
        "Stock",
        "Bond (finance)",
        "Mutual fund",
        "Index fund",
        "Exchange-traded fund",
        "401(k)",
        "Individual retirement account",
        "Roth IRA",
        "Compound interest",
        "Inflation",
        "Credit score",
        "Mortgage loan",
        "Interest rate",
        "Cryptocurrency",
        "Bitcoin",
        "Stock market",
        "New York Stock Exchange",
        "Federal Reserve",
        "Income tax in the United States",
        "Capital gains tax",
        "Estate tax in the United States",
        "Social Security (United States)",
        "Medicare (United States)",
        "Debt",
        "Credit card",
        "Bankruptcy",
        "Insurance",
        "Term life insurance",
        "Health insurance in the United States",
    ],
    "astronomy": [
        "Astronomy",
        "Solar System",
        "Sun",
        "Mercury (planet)",
        "Venus",
        "Earth",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Moon",
        "Asteroid",
        "Comet",
        "Milky Way",
        "Galaxy",
        "Black hole",
        "Neutron star",
        "Supernova",
        "Nebula",
        "Dark matter",
        "Dark energy",
        "Big Bang",
        "Exoplanet",
        "Hubble Space Telescope",
        "James Webb Space Telescope",
        "Constellation",
        "Northern lights",
        "Meteor shower",
        "Eclipse",
        "Light-year",
        "Cosmology",
        "Multiverse",
        "Fermi paradox",
        "SETI",
        "Drake equation",
    ],
    "mythology": [
        "Greek mythology",
        "Roman mythology",
        "Norse mythology",
        "Egyptian mythology",
        "Mesopotamian mythology",
        "Celtic mythology",
        "Aztec mythology",
        "Inca mythology",
        "Native American mythology",
        "Slavic mythology",
        "Hindu mythology",
        "Japanese mythology",
        "Chinese mythology",
        "Zeus",
        "Odin",
        "Thor",
        "Loki",
        "Hercules",
        "Achilles",
        "Odysseus",
        "Perseus",
        "Medusa",
        "Minotaur",
        "Poseidon",
        "Ares",
        "Athena",
        "Apollo",
        "Artemis",
        "Hades",
        "Persephone",
        "Ra (deity)",
        "Anubis",
        "Osiris",
        "Isis (deity)",
        "Dragon",
        "Phoenix (mythology)",
        "Vampire",
        "Werewolf",
        "Mermaid",
        "Bigfoot",
        "Loch Ness Monster",
    ],
    "philosophy": [
        "Philosophy",
        "Socrates",
        "Plato",
        "Aristotle",
        "Stoicism",
        "Epicureanism",
        "Existentialism",
        "Nihilism",
        "Empiricism",
        "Rationalism",
        "Utilitarianism",
        "Immanuel Kant",
        "Friedrich Nietzsche",
        "René Descartes",
        "John Locke",
        "David Hume",
        "Jean-Paul Sartre",
        "Albert Camus",
        "Karl Marx",
        "Friedrich Engels",
        "Sigmund Freud",
        "Carl Jung",
        "Ethics",
        "Metaphysics",
        "Epistemology",
        "Free will",
        "Determinism",
        "Consciousness",
        "Meaning of life",
        "Social contract",
        "Democracy",
        "Fascism",
        "Communism",
        "Libertarianism",
        "Anarchism",
    ],
    "psychology": [
        "Psychology",
        "Cognitive bias",
        "List of cognitive biases",
        "Confirmation bias",
        "Dunning–Kruger effect",
        "Maslow's hierarchy of needs",
        "Classical conditioning",
        "Operant conditioning",
        "Cognitive behavioral therapy",
        "Narcissistic personality disorder",
        "Psychopathy",
        "Sociopathy",
        "Depression (mood)",
        "Anxiety",
        "Post-traumatic stress disorder",
        "Bipolar disorder",
        "Schizophrenia",
        "Borderline personality disorder",
        "Attachment theory",
        "Stanford prison experiment",
        "Milgram experiment",
        "Placebo effect",
        "Gaslighting",
        "Manipulation (psychology)",
        "Social psychology",
        "Mob mentality",
        "Groupthink",
        "Propaganda",
        "Persuasion",
        "Body language",
        "Emotional intelligence",
        "Introversion and extraversion",
        "MBTI",
        "Stockholm syndrome",
    ],
    "true-crime": [
        "Serial killer",
        "Ted Bundy",
        "Jeffrey Dahmer",
        "John Wayne Gacy",
        "Charles Manson",
        "Manson Family",
        "Zodiac Killer",
        "Jack the Ripper",
        "Son of Sam",
        "BTK killer",
        "Green River Killer",
        "Edmund Kemper",
        "Richard Ramirez",
        "Dennis Rader",
        "Aileen Wuornos",
        "Scott Peterson",
        "O. J. Simpson murder case",
        "Columbine High School massacre",
        "Sandy Hook Elementary School shooting",
        "Oklahoma City bombing",
        "Unabomber",
        "D.B. Cooper",
        "Ponzi scheme",
        "Bernie Madoff",
        "Enron scandal",
        "Alcatraz Federal Penitentiary",
        "Death row",
        "Capital punishment in the United States",
        "Forensic science",
        "DNA profiling",
    ],
    "military-history": [
        "Vietnam War",
        "Korean War",
        "Gulf War",
        "Iraq War",
        "War in Afghanistan (2001–2021)",
        "American Revolutionary War",
        "War of 1812",
        "Mexican–American War",
        "Spanish–American War",
        "World War I",
        "World War II",
        "D-Day",
        "Battle of Stalingrad",
        "Battle of Midway",
        "Manhattan Project",
        "Hiroshima and Nagasaki atomic bombings",
        "Cold War",
        "Cuban Missile Crisis",
        "Bay of Pigs Invasion",
        "Special forces",
        "Navy SEALs",
        "Green Berets",
        "Delta Force",
        "CIA",
        "NSA",
        "Military rank",
        "Medal of Honor",
        "PTSD in veterans",
        "Agent Orange",
        "Napalm",
        "Land mine",
        "Nuclear weapon",
        "Chemical weapon",
        "Biological warfare",
        "Drone warfare",
    ],
    "automotive": [
        "Automobile",
        "Internal combustion engine",
        "Electric vehicle",
        "Hybrid vehicle",
        "Ford Motor Company",
        "General Motors",
        "Chrysler",
        "Toyota",
        "Honda",
        "Volkswagen",
        "BMW",
        "Mercedes-Benz",
        "Ferrari",
        "Lamborghini",
        "Porsche",
        "Ford Mustang",
        "Chevrolet Camaro",
        "Dodge Challenger",
        "Jeep",
        "Ford F-150",
        "Chevrolet Silverado",
        "Pickup truck",
        "Four-wheel drive",
        "Off-road vehicle",
        "NASCAR",
        "Formula One",
        "Drag racing",
        "Monster truck",
        "Car tuning",
        "Motorcycle",
        "Harley-Davidson",
        "Car maintenance",
        "Transmission (mechanics)",
        "Carburetor",
        "Fuel injection",
        "Turbocharger",
        "Supercharger",
        "Diesel engine",
        "Tesla, Inc.",
    ],
    "science-misc": [
        "Quantum mechanics",
        "Theory of relativity",
        "String theory",
        "Thermodynamics",
        "Electromagnetism",
        "Nuclear physics",
        "Particle physics",
        "Standard Model",
        "Higgs boson",
        "Photon",
        "Electron",
        "Proton",
        "Neutron",
        "Radioactive decay",
        "Nuclear fission",
        "Nuclear fusion",
        "Genetic engineering",
        "CRISPR",
        "Stem cell",
        "Cloning",
        "Nanotechnology",
        "Robotics",
        "Artificial intelligence",
        "Machine learning",
        "Neural network",
        "Cryptography",
        "Blockchain",
        "Quantum computing",
        "Climate change",
        "Ozone layer",
        "Plate tectonics",
        "Dinosaur",
        "Human evolution",
        "Neanderthal",
        "Ice age",
    ],
}


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
