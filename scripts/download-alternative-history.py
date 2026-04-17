#!/usr/bin/env python3
"""
download-alternative-history.py — Download Great Reset/NWO, Kubrick theories,
                                   Holocaust revisionism, and Epstein content.

Run: python3 download-alternative-history.py [category|all] [--force]

Sources: Wikipedia + written notes. No images or videos — text only.
Content presented as-is. Jarvis presents information; you decide.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "alternative-history")

TOPICS = {

    # ── Great Reset / New World Order ─────────────────────────────────────────
    "great-reset-nwo": [
        "The Great Reset",
        "World Economic Forum",
        "Klaus Schwab",
        "New World Order (conspiracy theory)",
        "Global governance",
        "Agenda 21",
        "Agenda 2030",
        "Sustainable Development Goals",
        "Build Back Better",
        "Fourth Industrial Revolution",
        "Transhumanism",
        "Yuval Noah Harari",
        "Depopulation conspiracy theory",
        "Georgia Guidestones",
        "Population control",
        "Bill Gates",
        "Bill & Melinda Gates Foundation",
        "GAVI Alliance",
        "ID2020",
        "Digital identity",
        "Social credit system",
        "Central bank digital currency",
        "Great Replacement",
        "Replacement conspiracy theory",
        "Kalergi Plan",
        "Globalism",
        "George Soros",
        "Open Society Foundations",
        "Rockefeller Foundation",
        "Event 201",
        "Lockstep (Rockefeller Foundation)",
        "COVID-19 pandemic",
        "mRNA vaccine",
        "Vaccine hesitancy",
        "5G conspiracy theories",
        "Contact tracing",
        "Vaccine passport",
    ],

    # ── Masonic & Elite Conspiracies ──────────────────────────────────────────
    "masonic-elite": [
        "Freemasonry",
        "History of Freemasonry",
        "Albert Pike",
        "Morals and Dogma",
        "Illuminati",
        "Bavarian Illuminati",
        "Adam Weishaupt",
        "Skull and Bones",
        "Bohemian Grove",
        "Owl of Minerva",
        "Moloch",
        "Cremation of Care",
        "Bilderberg Group",
        "Trilateral Commission",
        "Council on Foreign Relations",
        "Committee of 300",
        "Tavistock Institute",
        "Round Table (organization)",
        "Rhodes Scholarship",
        "Cecil Rhodes",
        "British Israel",
        "Christian Identity",
        "Zionism",
        "Protocols of the Elders of Zion",
        "Antisemitic canard",
        "Blood libel",
        "Pizzagate conspiracy theory",
        "QAnon",
        "Satanic panic",
        "Spirit cooking",
        "Marina Abramović",
        "Podesta emails",
        "Jeffrey Epstein",
        "Epstein–Maxwell scandal",
        "Little Saint James",
    ],

    # ── Kubrick Film Theories ─────────────────────────────────────────────────
    "kubrick-theories": [
        "Stanley Kubrick",
        "2001: A Space Odyssey (film)",
        "The Shining (film)",
        "Eyes Wide Shut",
        "A Clockwork Orange",
        "Full Metal Jacket",
        "Dr. Strangelove",
        "Barry Lyndon",
        "Lolita (1962 film)",
        "Room 237 (film)",
        "Apollo 11",
        "Moon landing conspiracy theories",
        "Conspiracy theories about Stanley Kubrick",
        "The Shining (novel)",
        "Stephen King",
        "HAL 9000",
        "Arthur C. Clarke",
        "Overlook Hotel",
        "Jack Torrance",
        "The Shining carpet pattern",
        "Illuminati in popular culture",
        "Eyes Wide Shut conspiracy",
        "Kubrick's death conspiracy",
    ],

    # ── Holocaust Revisionism & Alternative History ───────────────────────────
    "holocaust-revisionism": [
        "Holocaust denial",
        "Holocaust revisionism",
        "Revisionist history",
        "Holocaust",
        "Nuremberg trials",
        "Nuremberg Code",
        "Red Cross and the Holocaust",
        "International Red Cross Holocaust",
        "Holocaust death toll",
        "Zyklon B",
        "Auschwitz",
        "David Irving",
        "Ernst Zündel",
        "Fred Leuchter",
        "Leuchter report",
        "Robert Faurisson",
        "Institute for Historical Review",
        "Holocaust uniqueness",
        "Hellstorm (book)",
        "Bombing of Dresden",
        "Morgenthau Plan",
        "Eisenhower death camps",
        "German prisoner-of-war camps",
        "Allied war crimes in World War II",
        "Holodomor",
        "Armenian genocide",
        "Rwandan genocide",
        "Democide",
        "R. J. Rummel",
        "Death by Government",
        "Population transfer in the Soviet Union",
        "Gulag",
        "Alexander Solzhenitsyn",
        "Two Hundred Years Together",
    ],

    # ── Jeffrey Epstein ───────────────────────────────────────────────────────
    "epstein": [
        "Jeffrey Epstein",
        "Epstein–Maxwell scandal",
        "Ghislaine Maxwell",
        "Little Saint James",
        "Jeffrey Epstein's arrest and death",
        "Jeffrey Epstein victim compensation fund",
        "Virginia Giuffre",
        "Les Wexner",
        "Epstein's black book",
        "Epstein flight logs",
        "Jeffrey Epstein and Donald Trump",
        "Jeffrey Epstein and Bill Clinton",
        "Jeffrey Epstein and Prince Andrew",
        "Prince Andrew, Duke of York",
        "Alan Dershowitz",
        "Alexander Acosta",
        "Non-prosecution agreement",
        "Lolita Express",
        "Zorro Ranch",
        "Epstein's Manhattan mansion",
        "Metropolitan Correctional Center, New York",
        "Suicide watch",
        "Epstein autopsy",
        "Michael Baden",
        "ARCA Foundation",
        "Epstein–Barr virus",
        "Sex trafficking",
        "Human trafficking",
        "Child sexual abuse",
        "Pedophilia",
        "Elite pedophile ring conspiracy theory",
        "Franklin child prostitution ring allegations",
        "Jimmy Savile",
        "Operation Yewtree",
        "Elm Guest House abuse allegations",
    ],
}

# ── Hand-written notes (no Wikipedia equivalent) ─────────────────────────────
WRITTEN_NOTES = {

    "kubrick-moon-landing": """# Kubrick and the Moon Landing Conspiracy

## The Theory
One of the most persistent Kubrick theories claims Stanley Kubrick was hired by NASA
and the US government to fake the Apollo 11 moon landing footage in 1969. Proponents
argue that 2001: A Space Odyssey (1968) demonstrated Kubrick's ability to create
convincing space footage, making him the ideal candidate.

## Key Claims
- Kubrick allegedly embedded confessions in The Shining (1980)
- The Apollo 11 footage supposedly matches the visual style of 2001
- Room 237 (2001 = Apollo number theory) in The Shining references the mission
- Danny's Apollo 11 sweater in The Shining is cited as a symbolic confession
- The carpet pattern in the Overlook Hotel resembles the Apollo launch pad layout

## The "Confession" Interview
A video surfaced showing a man claiming to be Kubrick confessing to filming the moon
landing. The interview was widely shared. It was later confirmed to be a 2002 mockumentary
called "Kubrick, Nixon and the Man on the Moon" by William Karel. The "Kubrick" in the
interview is an actor named T. Patrick Murray.

## Counterarguments
- Over 400,000 people worked on the Apollo program — a cover-up of that scale is
  considered impossible to maintain
- Independent tracking by other countries (Soviet Union, amateur astronomers) confirmed
  the missions in real time
- Retroreflectors left on the lunar surface are still used today
- Kubrick's daughter Vivian has called the theory "an utter fabrication"

## Why People Believe It
- Kubrick was secretive and obsessive about his work
- The Cold War created pressure to beat the Soviets at any cost
- The technology to land on the moon seemed impossibly advanced for 1969
- Kubrick left many intentional visual puzzles in his films, encouraging over-analysis

## The Shining Interpretation (Room 237)
The documentary Room 237 (2012) presents multiple interpretations of The Shining,
including the moon landing theory. Kubrick scholars generally regard these as
imaginative but unsupported readings. Kubrick himself never commented.
""",

    "kubrick-eyes-wide-shut": """# Eyes Wide Shut: Elite Secret Societies and Kubrick's Final Warning

## Background
Eyes Wide Shut (1999) was Stanley Kubrick's final film, released six days after his
death. It stars Tom Cruise and Nicole Kidman and centers on a secret society orgy
attended by elites. Many believe the film was a deliberate exposure of real elite
practices.

## The Conspiracy Theory
The theory holds that Kubrick was given access to real elite society rituals —
possibly through his connections in Hollywood and the aristocracy — and encoded what
he witnessed into the film. The masked orgy scene, set in a mansion, is claimed to
represent real events held by the Rothschilds, British aristocracy, or similar groups.

## The Rothschild Party Connection
In 1972, Baroness Marie-Hélène de Rothschild hosted the "Surrealist Ball" at Château
de Ferrières. Photos from the event show guests in elaborate animal head masks, inverted
cross decorations, and occult imagery remarkably similar to Eyes Wide Shut. The party
is well-documented and the photos are publicly available.

## Kubrick's Death
Kubrick died of a heart attack on March 7, 1999 — just 6 days after showing Warner
Bros. the final cut. He was 70 and had no prior history of heart disease. Conspiracy
theorists claim he was killed to prevent the film's release or that the studio cut
scenes. The film's runtime was reportedly reduced before release.

## What Was Cut?
Warner Bros. and the Kubrick estate have never confirmed what, if anything, was removed.
The theatrical cut is 159 minutes. Some researchers claim an original cut ran longer
and contained more explicit material linking the ritual to real identifiable locations.

## The Orgy Mansion
The filming location was Mentmore Towers in Buckinghamshire, England — a Rothschild
family estate built in the 1850s. This is not disputed. Kubrick chose the location.

## Interpretation
Whether intentional allegory, artistic exploration of power and sexuality, or genuine
whistleblowing — Eyes Wide Shut remains Kubrick's most debated work. The timing of
his death ensures the questions will never be fully answered.
""",

    "mud-flood-tartaria": """# Mud Flood and Tartaria: The Hidden History Theory

## What is the Mud Flood Theory?
The mud flood theory proposes that a catastrophic global event — likely in the 1700s
or early 1800s — buried an entire advanced civilization under several feet of mud and
sediment. Proponents argue that the "official" history of the 18th and 19th centuries
was fabricated to conceal this event and the civilization that preceded it.

## What Was Tartaria?
Tartaria (also spelled Tartary) was a real geographical designation used on European
maps from the 15th through 19th centuries, referring to the vast region of Central
Asia and Siberia. On old maps, it appears as "Grand Tartary" or "Chinese Tartary."

The conspiracy theory version claims Tartaria was actually a global empire — possibly
technologically advanced — that was wiped out and erased from history. Mud flood
researchers claim Tartarian architecture can still be seen in the ornate buildings
of cities worldwide that were supposedly built in the 1800s.

## Key Evidence Cited by Believers
- Old photographs showing buildings with ground floors partially buried
- Basement windows at ground level in supposedly new 19th century buildings
- The "orphan trains" — real historical program (1854–1929) claimed to have been
  repopulating areas depopulated by the mud flood
- "Star forts" — real historical fortifications with distinctive geometry, claimed
  to be free energy devices
- The 1893 Chicago World's Fair (White City) — buildings allegedly too advanced
  for the supposed technology of the time
- Anachronistic architectural details on supposedly new buildings

## The Reset Narrative
Connected to this is the idea of periodic "great resets" — cyclical civilizational
destructions (possibly via comet impacts, pole shifts, or engineered events) that
wipe the slate clean and allow a control group to rewrite history. Researchers like
Randall Carlson and Graham Hancock (working from mainstream evidence) have documented
real catastrophic events during the Younger Dryas period (~12,900 years ago).

## Criticism
- Partially buried buildings are explained by changing ground levels, urban fill,
  and construction practices over time
- Grand Tartary on old maps referred to a geographic region, not a political empire
- The ornate buildings cited were constructed using well-documented labor and methods
- No physical evidence of a civilization-ending mud layer from the 1800s has been found

## Cultural Impact
The theory has spread widely on YouTube and alternative history forums. It connects
to broader narratives about suppressed history, the Smithsonian hiding giant skeletons,
and cyclical civilizational resets. Whether true or not, it has prompted genuine
re-examination of anomalous historical architecture.
""",

    "epstein-documents-summary": """# Jeffrey Epstein: Document Summary and Key Facts

## Who Was Jeffrey Epstein?
Jeffrey Edward Epstein (January 20, 1953 – August 10, 2019) was an American financier
and convicted sex offender. He ran a network that allegedly sexually trafficked minors
and young women to powerful men including politicians, royalty, academics, and
celebrities.

## The 2008 Non-Prosecution Agreement
In 2008, Epstein pleaded guilty to Florida state charges of soliciting prostitution
from a minor. US Attorney Alexander Acosta negotiated a controversial non-prosecution
agreement (NPA) that shielded Epstein and unnamed co-conspirators from federal charges.
Epstein served 13 months in a private wing of Palm Beach County jail with extensive
work-release privileges. Acosta later resigned as US Secretary of Labor when the deal
became public.

## Known Associates
The Epstein flight logs document passengers on his private jets:
- **Bill Clinton** — 26 confirmed flights on "Lolita Express"
- **Donald Trump** — flew on Epstein's plane; later said "I knew him like everyone
  else in Palm Beach did"
- **Prince Andrew, Duke of York** — multiple documented visits; settled civil lawsuit
  in 2022 with Virginia Giuffre for reported $12 million
- **Alan Dershowitz** — Harvard law professor; named in civil lawsuits, denies all
  allegations
- **Les Wexner** — billionaire founder of L Brands (Victoria's Secret); gave Epstein
  power of attorney and his Manhattan townhouse
- **Ghislaine Maxwell** — Epstein's girlfriend and alleged procurer; convicted 2021
  on five federal charges including sex trafficking of minors

## Little Saint James
Epstein owned Little Saint James, a 75-acre private island in the US Virgin Islands,
nicknamed "Pedophile Island" by locals. Witnesses described a blue-striped building
whose purpose remains debated. The island was demolished and sold after Epstein's death.

## The 2019 Arrest and Death
Epstein was arrested July 6, 2019 on federal charges of sex trafficking. He was held
at the Metropolitan Correctional Center in New York. On August 10, 2019, he was found
dead in his cell. The official cause of death was suicide by hanging.

## Death Controversy
- Epstein had been placed on suicide watch following a previous incident, then removed
- Security cameras outside his cell malfunctioned or were not recording
- Two guards on duty fell asleep and falsified records
- Independent forensic pathologist Dr. Michael Baden, hired by Epstein's brother,
  concluded the injuries were more consistent with homicide than suicide
- Baden noted broken bones in the neck typically associated with strangulation rather
  than hanging
- No official investigation has changed the suicide ruling

## The 2024 Document Releases
Starting in January 2024, hundreds of pages of court documents were unsealed from
the civil lawsuit brought by Virginia Giuffre against Ghislaine Maxwell. The documents
named numerous individuals but in most cases the names appeared in the context of
allegations and denials, not proven facts. Many names were accompanied by statements
denying involvement.

## Ghislaine Maxwell
Ghislaine Maxwell, daughter of media mogul Robert Maxwell, was convicted in December
2021 on five counts including sex trafficking of minors. She was sentenced to 20 years.
She has not publicly named additional co-conspirators beyond what appeared in trial.

## What Remains Unknown
- The full client list and what specific acts were observed or participated in
- Whether intelligence agencies (CIA, Mossad) were involved in using Epstein as a
  blackmail operation — a theory raised by journalist Seymour Hersh and others
- The full contents of materials seized from Epstein's properties
- Why the 2008 NPA was so favorable and who pressured Acosta
""",
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

    # Write hand-crafted notes first
    notes_dir = os.path.join(OUTPUT_DIR, "notes")
    os.makedirs(notes_dir, exist_ok=True)
    print("\n[WRITTEN NOTES]")
    for slug, content in WRITTEN_NOTES.items():
        out_path = os.path.join(notes_dir, f"{slug}.md")
        if os.path.exists(out_path) and not force:
            print(f"  skip  {slug}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  wrote {slug}.md ({len(content):,} chars)")

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
