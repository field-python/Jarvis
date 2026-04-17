#!/usr/bin/env python3
"""
download-medical.py — Download medical reference, first aid, anatomy, field medicine,
                       herbal remedies, and health topics.

Run: Jarvis download-medical [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "medical")

TOPICS = {
    "first-aid": [
        "First aid",
        "Basic life support",
        "Cardiopulmonary resuscitation",
        "Automated external defibrillator",
        "Choking",
        "Heimlich maneuver",
        "Bleeding",
        "Wound",
        "Laceration",
        "Hemorrhage",
        "Tourniquet",
        "Pressure bandage",
        "Wound closure",
        "Suture",
        "Wound care",
        "Infection",
        "Antiseptic",
        "Hydrogen peroxide",
        "Iodine",
        "Burn",
        "Thermal burn",
        "Chemical burn",
        "Frostbite",
        "Hypothermia",
        "Heat stroke",
        "Shock (circulatory)",
        "Fracture (bone)",
        "Splint (medicine)",
        "Dislocation",
        "Sprain",
        "Concussion",
        "Skull fracture",
        "Spinal cord injury",
        "Recovery position",
        "Triage",
    ],
    "anatomy": [
        "Human body",
        "Anatomy",
        "Organ (anatomy)",
        "Heart",
        "Lung",
        "Liver",
        "Kidney",
        "Brain",
        "Spinal cord",
        "Digestive system",
        "Circulatory system",
        "Respiratory system",
        "Nervous system",
        "Immune system",
        "Endocrine system",
        "Skeletal system",
        "Muscular system",
        "Lymphatic system",
        "Bone",
        "Muscle",
        "Artery",
        "Vein",
        "Capillary",
        "Neuron",
        "Skin",
        "Blood",
        "Blood type",
        "Red blood cell",
        "White blood cell",
        "Platelet",
        "Hormone",
        "Enzyme",
    ],
    "common-conditions": [
        "Infection",
        "Bacterial infection",
        "Viral infection",
        "Fever",
        "Inflammation",
        "Abscess",
        "Cellulitis",
        "Appendicitis",
        "Pneumonia",
        "Bronchitis",
        "Urinary tract infection",
        "Kidney stone",
        "Gallstone",
        "Diabetes mellitus",
        "Hypertension",
        "Heart attack",
        "Stroke",
        "Anaphylaxis",
        "Allergic reaction",
        "Asthma",
        "Dehydration",
        "Malnutrition",
        "Anemia",
        "Sepsis",
        "Food poisoning",
        "Giardia",
        "Norovirus",
        "Lyme disease",
        "Rabies",
        "Tetanus",
        "Gangrene",
        "Frostbite",
        "Snow blindness",
    ],
    "field-medicine": [
        "Wilderness medicine",
        "Field medicine",
        "Combat medic",
        "Tactical combat casualty care",
        "Improvised tourniquet",
        "Improvised splint",
        "Wound packing",
        "Hemostatic agent",
        "QuikClot",
        "Israeli bandage",
        "SAM splint",
        "Airway management",
        "Jaw thrust",
        "Needle decompression",
        "Tension pneumothorax",
        "Improvised stretcher",
        "Patient assessment",
        "SOAP note",
        "Vital signs",
        "Blood pressure",
        "Pulse",
        "Respiration rate",
        "Oxygen saturation",
        "Glasgow Coma Scale",
        "Pain scale",
        "Hypothermia treatment",
        "Altitude sickness",
        "Evacuation (medical)",
        "Medevac",
        "Golden hour (medicine)",
        "Stop the Bleed",
    ],
    "herbal-medicine": [
        "Herbalism",
        "Medicinal plants",
        "Traditional medicine",
        "Echinacea",
        "Elderberry",
        "Garlic",
        "Ginger",
        "Turmeric",
        "Valerian (herb)",
        "Chamomile",
        "Lavender",
        "Peppermint",
        "St. John's wort",
        "Yarrow",
        "Plantain (plant)",
        "Comfrey",
        "Calendula",
        "Tea tree oil",
        "Oregano oil",
        "Colloidal silver",
        "Activated charcoal",
        "Willow bark",
        "Aspirin",
        "Feverfew",
        "Milk thistle",
        "Dandelion",
        "Nettle",
        "Pine resin",
        "Honey",
        "Manuka honey",
        "Aloe vera",
        "Witch hazel",
    ],
    "medications": [
        "Over-the-counter drug",
        "Ibuprofen",
        "Acetaminophen",
        "Aspirin",
        "Diphenhydramine",
        "Loratadine",
        "Pseudoephedrine",
        "Antacid",
        "Loperamide",
        "Bismuth subsalicylate",
        "Oral rehydration therapy",
        "Electrolyte",
        "Antibiotic",
        "Amoxicillin",
        "Ciprofloxacin",
        "Doxycycline",
        "Metronidazole",
        "Antifungal medication",
        "Clotrimazole",
        "Antiparasitic",
        "Ivermectin",
        "Epinephrine",
        "Naloxone",
        "Glucose",
        "Insulin",
        "Corticosteroid",
        "Hydrocortisone",
        "Antihistamine",
        "Drug interaction",
        "Allergy",
        "Medication storage",
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
