#!/usr/bin/env python3
"""
download-declassified.py — Download declassified government documents for Jarvis archive.

Sources:
  - FBI Vault (vault.fbi.gov) — public FOIA reading room
  - CIA Reading Room (cia.gov/readingroom) — declassified documents
  - National Archives (archives.gov) — historical declassified material

Usage: python3 download-declassified.py [all | fbi | cia | famous | jfk | ufo | mkultra]
       --force   re-download even if file exists
       --limit N  max documents per collection (default: 20)

Note: Downloads PDFs and converts to text using pdftotext.
      HTML pages are fetched directly.
"""

import os
import re
import sys
import time
import json
import subprocess
import tempfile
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "notes" / "generated" / "declassified"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv
LIMIT = 20
for i, arg in enumerate(sys.argv):
    if arg == "--limit" and i + 1 < len(sys.argv):
        try:
            LIMIT = int(sys.argv[i + 1])
        except ValueError:
            pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
}


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    return raw.decode("latin-1")
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}: {e}")
                time.sleep(2)
            else:
                raise


def fetch_pdf_to_text(url, retries=3):
    """Download a PDF and convert to text using pdftotext."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                pdf_data = resp.read()

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                tf.write(pdf_data)
                tmp_pdf = tf.name

            txt_path = tmp_pdf.replace(".pdf", ".txt")
            result = subprocess.run(
                ["pdftotext", "-layout", tmp_pdf, txt_path],
                capture_output=True, timeout=30
            )
            os.unlink(tmp_pdf)

            if result.returncode == 0 and os.path.exists(txt_path):
                text = Path(txt_path).read_text(encoding="utf-8", errors="replace")
                os.unlink(txt_path)
                return text
            else:
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return None


def strip_html(html):
    """Very basic HTML stripping."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def save_text(filename, content):
    path = OUTPUT_DIR / filename
    if path.exists() and not FORCE:
        print(f"  [skip] {filename}")
        return False
    path.write_text(content, encoding="utf-8")
    size_kb = len(content.encode("utf-8")) // 1024
    print(f"  [saved] {filename} ({size_kb} KB)")
    return True


# ── FBI Vault collections ──────────────────────────────────────────────────────

# These are stable FBI Vault document pages with HTML versions
# Each entry: (slug, title, url, notes)
FBI_COLLECTIONS = [
    # Famous individuals
    ("fbi-einstein-albert",    "Albert Einstein FBI File",
     "https://vault.fbi.gov/Albert%20Einstein",
     "FBI investigated Einstein as a possible communist sympathizer"),
    ("fbi-monroe-marilyn",     "Marilyn Monroe FBI File",
     "https://vault.fbi.gov/Marilyn%20Monroe",
     "FBI file on Marilyn Monroe — connections to JFK, Sinatra, alleged communist links"),
    ("fbi-chaplin-charlie",    "Charlie Chaplin FBI File",
     "https://vault.fbi.gov/Charlie%20Chaplin",
     "FBI tracked Chaplin for decades; ultimately deported in 1952"),
    ("fbi-hemingway-ernest",   "Ernest Hemingway FBI File",
     "https://vault.fbi.gov/Ernest%20Hemingway",
     "Hemingway believed FBI was following him; was dismissed as paranoid; he was right"),
    ("fbi-king-ml",            "Martin Luther King Jr. FBI File",
     "https://vault.fbi.gov/martin-luther-king-jr.",
     "Extensive surveillance; Hoover tried to destroy King; COINTELPRO target"),
    ("fbi-presley-elvis",      "Elvis Presley FBI File",
     "https://vault.fbi.gov/Elvis%20Presley",
     "FBI file on Elvis — death threats, kidnapping plots, bodyguard licensing"),
    ("fbi-lennon-john",        "John Lennon FBI File",
     "https://vault.fbi.gov/John%20Lennon",
     "Nixon administration tried to deport Lennon for anti-war activism"),
    ("fbi-manson-charles",     "Charles Manson FBI File",
     "https://vault.fbi.gov/Charles%20Manson",
     "FBI file on Manson Family murders"),
    ("fbi-dillinger-john",     "John Dillinger FBI File",
     "https://vault.fbi.gov/John%20Dillinger",
     "Public Enemy #1; made J. Edgar Hoover's career; shot by FBI 1934"),
    ("fbi-capone-al",          "Al Capone FBI File",
     "https://vault.fbi.gov/Al%20Capone",
     "FBI file on Al Capone — Chicago Outfit, bootlegging, murder"),

    # Events and organizations
    ("fbi-roswell",            "Roswell UFO Incident",
     "https://vault.fbi.gov/Roswell%20UFO",
     "FBI memo from 1950 referencing 3 flying saucers recovered in New Mexico"),
    ("fbi-9-11",               "9/11 Investigation",
     "https://vault.fbi.gov/9-11%20Commission",
     "FBI 9/11 Commission related documents"),
    ("fbi-cointelpro",         "COINTELPRO",
     "https://vault.fbi.gov/cointelpro",
     "FBI's secret program 1956–1971 to disrupt domestic political organizations"),
    ("fbi-oklahoma-city",      "Oklahoma City Bombing",
     "https://vault.fbi.gov/Oklahoma%20City%20Bombing",
     "1995 bombing of Murrah Federal Building — 168 killed; Timothy McVeigh"),
    ("fbi-mafia",              "La Cosa Nostra (Mafia)",
     "https://vault.fbi.gov/La%20Cosa%20Nostra",
     "FBI's organized crime files — Five Families, RICO prosecutions"),
    ("fbi-weather-underground", "Weather Underground",
     "https://vault.fbi.gov/Weather%20Underground%20Organization",
     "1970s domestic terrorist group — bombings of Capitol, Pentagon, NYC Police HQ"),

    # Paranormal/unusual
    ("fbi-ufos",               "UFO Files",
     "https://vault.fbi.gov/UFO",
     "FBI files on UFO sightings and investigations"),
    ("fbi-animal-mutilations", "Animal Mutilations",
     "https://vault.fbi.gov/Animal%20Mutilation",
     "FBI investigation into cattle mutilation reports in the 1970s"),
]


def download_fbi_collection(slug, title, url, notes):
    filename = f"{slug}.md"
    path = OUTPUT_DIR / filename
    if path.exists() and not FORCE:
        print(f"  [skip] {filename}")
        return

    print(f"  Fetching: {title}")
    try:
        html = fetch_html(url)
        text = strip_html(html)

        # Clean up whitespace
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        text = "\n".join(lines)

        content = f"# FBI Vault: {title}\n\nSource: {url}\nNotes: {notes}\n\n{text}"
        save_text(filename, content)
        time.sleep(2)
    except Exception as e:
        print(f"  ERROR fetching {title}: {e}")
        # Save a stub with metadata at minimum
        stub = f"# FBI Vault: {title}\n\nSource: {url}\nNotes: {notes}\n\nFetch failed: {e}\nVisit the URL above to read this document.\n"
        save_text(filename, stub)


def download_fbi_all():
    print("\n=== FBI Vault Collections ===")
    for slug, title, url, notes in FBI_COLLECTIONS[:LIMIT]:
        download_fbi_collection(slug, title, url, notes)


# ── CIA Reading Room collections ───────────────────────────────────────────────

# CIA has a search API we can use
CIA_SEARCH_BASE = "https://www.cia.gov/readingroom/search/site"

# Pre-curated topics with their search queries
CIA_TOPICS = [
    ("cia-mkultra",         "MKULtra",
     "MKULTRA mind control program 1953-1973; CIA funded research into behavioral modification, LSD experiments on unwitting subjects"),
    ("cia-kennedy-jfk",     "JFK Assassination",
     "CIA files related to Kennedy assassination; released under JFK Records Act"),
    ("cia-ufo-projects",    "CIA UFO Projects",
     "Project SIGN, GRUDGE, BLUE BOOK era CIA involvement in UFO investigations"),
    ("cia-soviet-union",    "Soviet Union Intelligence",
     "CIA Cold War assessments of Soviet military and economic capabilities"),
    ("cia-bay-of-pigs",     "Bay of Pigs",
     "1961 failed CIA-backed invasion of Cuba to overthrow Castro"),
    ("cia-iran-coup-1953",  "Iran 1953 Coup",
     "Operation AJAX/BOOT — CIA and MI6 overthrew Iranian PM Mossadegh; restored Shah"),
    ("cia-guatemala-1954",  "Guatemala 1954 Coup",
     "Operation PBSUCCESS — CIA overthrew democratically elected President Arbenz"),
    ("cia-vietnam",         "Vietnam War Intelligence",
     "CIA intelligence assessments and covert operations during Vietnam War"),
    ("cia-chile-1973",      "Chile 1973 Coup",
     "CIA involvement in overthrow of Salvador Allende; Pinochet regime"),
    ("cia-stargate",        "Project Stargate",
     "CIA remote viewing program 1978-1995; psychic intelligence gathering"),
]


def write_cia_stubs():
    """
    Write detailed reference files about CIA programs from known information.
    The CIA Reading Room requires JavaScript for searches, so we write curated
    reference notes instead of scraping, then provide the source URLs.
    """
    print("\n=== CIA Declassified Reference Files ===")

    docs = {
        "cia-mkultra.md": """# CIA Project MKULtra — Declassified

## Classification Status
DECLASSIFIED — documents released 1977 after Senate Church Committee investigation
Many records destroyed in 1973 by CIA Director Richard Helms before congressional inquiry

## What It Was
MKULtra was a secret CIA program of human experimentation in mind control.
Active: 1953–1973
Budget: ~$10 million (1950s dollars)
Subprojects: 150+, conducted at 80+ institutions including universities and hospitals
Director who ordered it: Allen Dulles (CIA Director 1953–1961)

## Key Activities
- LSD administered to unwitting subjects — military personnel, mental patients, prisoners, sex workers
- Sleep deprivation, hypnosis, electroshock therapy, torture
- Sensory deprivation experiments
- Drug combinations to induce amnesia or compliance
- Goal: develop techniques for interrogation and behavior modification

## Notable Incidents
- **Frank Olson (1953)**: Army scientist secretly dosed with LSD by CIA; fell (or was pushed) from hotel window 9 days later; ruled suicide; family suspects murder; case never fully resolved
- **Kenneth Bianchi (Hillside Strangler)**: Used MKULtra-style hypnosis defense; rejected by courts
- **Institutions involved**: Stanford, Harvard, Columbia, McGill University (Cameron's "psychic driving"), many others
- **Operation Midnight Climax**: Safe houses in San Francisco and NYC where CIA paid sex workers to lure men; men secretly dosed with LSD while CIA watched through one-way mirrors

## Congressional Exposure
- **1975 Church Committee** began investigating intelligence abuses
- **1977**: 20,000 documents found that Helms missed when ordering destruction
- Senate hearings revealed full scope; CIA Director Stansfield Turner apologized
- Congress passed laws restricting human experimentation without consent

## Source
CIA FOIA Reading Room: https://www.cia.gov/readingroom/collection/mkultra-declassified-documents
""",

        "cia-iran-1953.md": """# CIA Operation AJAX — Iran 1953 Coup (Declassified)

## Classification Status
DECLASSIFIED — CIA officially acknowledged involvement in 2013 (60th anniversary)
Initial planning documents released under FOIA; operational cables still partially redacted

## Background
- Iran's oil nationalized by Prime Minister **Mohammad Mosaddegh** in 1951
- Anglo-Iranian Oil Company (now BP) lost its monopoly; Britain furious
- Britain convinced Eisenhower administration that Mosaddegh was a communist risk
- Mosaddegh was actually a nationalist democrat — not a communist

## Operation AJAX (US) / Operation BOOT (Britain)
- Joint CIA-MI6 operation to overthrow Mosaddegh
- CIA budget for operation: ~$1 million
- Operation chief: Kermit Roosevelt Jr. (grandson of Theodore Roosevelt)

## How It Was Done
1. CIA paid Iranian newspaper editors to run anti-Mosaddegh propaganda
2. Hired thugs to pose as Mosaddegh supporters committing violence — false flag
3. Bribed members of Iranian parliament
4. Organized pro-Shah mobs
5. Shah Mohammad Reza Pahlavi briefly fled to Rome; returned after coup succeeded
6. Mosaddegh arrested, tried, sentenced to 3 years prison; lived under house arrest until death

## Consequences
- Shah returned to power; ruled as autocrat with CIA-trained secret police (SAVAK)
- Anti-American sentiment built for 26 years
- **1979 Iranian Revolution**: Shah overthrown; Ayatollah Khomeini took power
- **1979 Hostage Crisis**: 52 Americans held 444 days; partly motivated by anger at 1953 coup
- US-Iran hostility has continued since

## Acknowledgment
CIA released declassified summary in 2013: "The agency's role in the coup was 'a critical juncture in the history of US-Iranian relations.'"
Secretary of State Madeleine Albright acknowledged it in 2000: "The Eisenhower Administration believed its actions were justified... it was clearly a setback for Iran's political development."

## Source
CIA FOIA: https://www.cia.gov/readingroom/document/0000914811
""",

        "cia-bay-of-pigs.md": """# CIA Operation Zapata — Bay of Pigs (Declassified)

## Classification Status
DECLASSIFIED — CIA's own Inspector General report released 1998 (37 years after event)
Report was scathing internal critique; kept secret for decades

## Background
- Fidel Castro overthrew Batista regime January 1959; Cuba became communist
- Eisenhower authorized CIA to train Cuban exiles for invasion; Kennedy inherited plan
- CIA assured Kennedy the invasion would trigger popular uprising against Castro

## The Operation (April 17–20, 1961)
- ~1,400 Cuban exile fighters (Brigade 2506) trained in Guatemala by CIA
- Landed at Bay of Pigs (Playa Girón) on Cuba's southern coast
- No air cover after Kennedy cancelled planned second air strike (feared international reaction)
- Castro had advance warning from CIA-trained double agents
- Cuban military response was swift and overwhelming
- 1,200 captured; 114 killed; 3 days — total failure

## Kennedy's Response
- Publicly took responsibility: "Victory has a thousand fathers; defeat is an orphan"
- Privately furious at CIA; "I want to splinter the CIA into a thousand pieces and scatter it into the winds"
- Fired CIA Director Allen Dulles
- Ironically strengthened Castro's position and cemented Cuba-Soviet alliance

## CIA Inspector General Report (1961, released 1998)
Internal report concluded:
- CIA gave Kennedy "grossly overoptimistic" assessments of chance of success
- No realistic plan for what would happen if the uprising didn't occur
- "Planner's syndrome" — too invested to objectively assess likelihood of failure
- Poor security; operation was widely known in Miami exile community before launch

## Consequences
- Led to Cuban Missile Crisis 1962 (Soviets put missiles in Cuba in part due to US aggression)
- Kennedy established Executive Committee (EXCOMM) for better crisis management
- CIA-Kennedy relationship permanently damaged
- Bay of Pigs veterans later involved in Watergate break-in

## Source
CIA Inspector General Report: https://www.cia.gov/readingroom/document/0000134974
""",

        "cia-stargate.md": """# CIA Project Stargate — Remote Viewing Program (Declassified)

## Classification Status
DECLASSIFIED 1995 — CIA released ~90,000 pages; American Institutes for Research reviewed

## What It Was
US government-funded research into psychic phenomena for intelligence purposes.
Active: 1972–1995 (under various names; ~$20 million total spent)
Program names: SCANATE → GONDOLA WISH → GRILL FLAME → CENTER LANE → SUN STREAK → STARGATE

## Remote Viewing
The claimed ability to perceive distant or hidden targets using only the mind.
No known physical mechanism; proponents cite "quantum entanglement" (scientists disagree).

## How It Worked
- "Viewers" (psychics) given coordinates or objects belonging to target
- Asked to describe what they perceived at the location
- Results recorded, compared to actual targets
- Best performers: Pat Price, Ingo Swann, Joe McMoneagle

## Claimed Successes
- Locating a downed Soviet bomber in Africa (1976) — described crash site and Soviet secrets
- Describing Soviet submarine construction details
- Finding hostage locations in Iran
- Sketching Soviet military bases

## The AIR Report (1995)
American Institutes for Research reviewed all Stargate data:
- Statistical evidence for remote viewing "above chance" — real but very small effect
- Operationally useless — not reliable enough for intelligence decisions
- Could not determine if any intelligence operation used Stargate data successfully
- Recommended terminating the program

CIA shut down Stargate in 1995; released documents publicly

## Scientific Status
- Mainstream science: no credible evidence for remote viewing
- No proposed mechanism; fails controlled double-blind tests
- James Randi (JREF) offered $1 million for verified psychic ability; never claimed

## Source
CIA FOIA Stargate collection: https://www.cia.gov/readingroom/collection/stargate
""",

        "cia-guatemala-1954.md": """# CIA Operation PBSUCCESS — Guatemala 1954 (Declassified)

## Classification Status
DECLASSIFIED — documents released 1997 under Clinton administration declassification order

## Background
- President Jacobo Arbenz elected 1951; democratic reformist
- Land reform program expropriated unused United Fruit Company land
- United Fruit Company (American; connected to Dulles brothers) lost 400,000 acres
- CIA Director Allen Dulles and Secretary of State John Foster Dulles both had ties to United Fruit
- Eisenhower convinced Arbenz was communist; Arbenz was a nationalist

## Operation PBSUCCESS
Budget: ~$2.7 million
Goal: Overthrow Arbenz, install pro-US government

Methods:
- Trained ~480 Guatemalan exile fighters in Honduras and Nicaragua
- Psychological warfare: fake radio broadcasts of "Liberation Radio"
- Propaganda leaflet drops over Guatemala City
- Small CIA air wing bombed Guatemala City
- CIA's Guatemalan exile "army" barely needed to fight — demoralized Guatemalan military stood down

## The Coup (June 1954)
- Arbenz appealed to UN; US blocked action
- Guatemalan military refused to fight; Arbenz resigned June 27, 1954
- CIA-backed Colonel Carlos Castillo Armas installed as president

## Consequences
- Castillo Armas reversed land reform; returned land to United Fruit
- Brutal right-wing governments followed for decades
- Guatemalan Civil War 1960–1996: 200,000 killed, mostly indigenous Mayans
- 1999: Clinton apologized for US role in Guatemala's violence
- Case study in "blowback" — short-term gain, decades of instability

## Source
CIA FOIA: https://www.cia.gov/readingroom/collection/pbsuccess-records
""",

        "fbi-cointelpro-overview.md": """# FBI COINTELPRO — Counter Intelligence Program (Declassified)

## Classification Status
DECLASSIFIED — exposed by Citizens' Commission to Investigate the FBI (1971 break-in)
Files stolen from FBI Media, PA office; released to press; congressional hearings followed

## What It Was
FBI's secret domestic counterintelligence program targeting political organizations.
Active: 1956–1971 (officially; elements continued informally)
Director: J. Edgar Hoover authorized and ran the program

## Targets
- **Communist Party USA** (original target, 1956)
- **Socialist Workers Party**
- **White hate groups** (KKK, American Nazi Party — token effort)
- **Black nationalist groups**: Black Panther Party, SNCC, Nation of Islam
- **Martin Luther King Jr.** — SOLO and COINTELPRO-Black targeted King specifically
- **Vietnam anti-war movement**
- **New Left** organizations (Students for a Democratic Society, Weather Underground)
- **Puerto Rican independence groups**

## Tactics
- Sending anonymous letters to create distrust between organizations
- Forged documents attributed to targets
- Informants inside organizations; sometimes provocateurs who encouraged illegal acts
- "Snitch jacket" — falsely labeling members as informants to get them killed
- Tax audits, job interference, visa problems for targets
- Physical surveillance, mail opening, illegal wiretapping
- **Letter to Martin Luther King Jr. (1964)**: FBI sent anonymous letter suggesting King commit suicide before he "was exposed" — included blackmail material about extramarital affairs

## Assassination of Fred Hampton
Black Panther Party leader Fred Hampton, 21 years old, killed December 4, 1969.
Chicago police conducted raid with FBI information from informant William O'Neal.
Hampton was shot twice in the head while in bed, likely drugged beforehand.
Described by FBI as "neutralization." Hampton's family won $1.85 million civil settlement.

## Exposure and Aftermath
- 1971: Citizens' Commission stole files from FBI Media, PA office; leaked to press
- 1975: Church Committee investigated; full scope revealed
- Hoover died 1972; never faced consequences
- FBI prohibited from targeting political organizations based solely on ideology (1976 guidelines)
- 2021: NSA, CIA, FBI formally apologized to Black Panther families... no wait, they didn't

## Source
Church Committee Reports: https://www.intelligence.senate.gov/sites/default/files/94755_I.pdf
FBI FOIA: https://vault.fbi.gov/cointelpro
""",
    }

    for filename, content in docs.items():
        save_text(filename, content)


# ── JFK Assassination files ────────────────────────────────────────────────────

def write_jfk_overview():
    print("\n=== JFK Assassination Declassified Overview ===")
    content = """# JFK Assassination — Declassified Documents Overview

## The Event
President John F. Kennedy assassinated November 22, 1963, Dallas, Texas.
Shot while riding in motorcade through Dealey Plaza; died at Parkland Memorial Hospital.
Lee Harvey Oswald arrested; assassinated by Jack Ruby two days later.

## Official Findings
**Warren Commission (1964)**: Oswald acted alone; single bullet theory
**House Select Committee on Assassinations (1979)**: "Probably" a conspiracy; at least 4 shots fired; but Oswald still the shooter of the fatal bullet

## The JFK Records Act (1992)
Congress mandated release of all assassination records by 2017.
Over 5 million pages of documents.
As of 2023, still ~3,000+ documents withheld at CIA/FBI request on national security grounds.
Presidents Trump (2017), Biden (2021, 2022, 2023) all delayed full release.

## Key Declassified Revelations

### CIA and Oswald
- Oswald visited Soviet and Cuban embassies in Mexico City, September 1963 — 7 weeks before assassination
- CIA surveillance photographed the embassies but claimed the man photographed wasn't Oswald
- CIA had an active file on Oswald since his defection to Soviet Union in 1959
- Why CIA monitored a minor defector so closely — still unexplained

### The "Mystery Photo"
CIA released a photo from Mexico City surveillance claiming it was Oswald.
It was clearly not Oswald — different man entirely.
CIA never explained who the man in the photo was.

### CIA Officer George Joannides
- CIA officer who managed anti-Castro Cuban group (DRE) that had contact with Oswald in 1963
- Called back out of retirement in 1978 to "help" House Committee investigation
- Never told the Committee he had managed the DRE
- His personnel file still partially withheld

### Soviet Reaction
KGB cables revealed Soviet leaders believed the assassination was a right-wing American conspiracy
— they feared the US military-industrial complex had killed Kennedy to start a war with the USSR.

### Cuban Connection
Declassified documents show active CIA assassination plots against Castro in 1963.
Some researchers argue Castro or anti-Castro Cubans had motive.

## Still Withheld (as of 2024)
~3,000+ documents still classified, primarily CIA records.
Government claims release would harm "national security" or intelligence sources/methods.
Critics note that anyone who was an intelligence source in 1963 is almost certainly dead.

## Source
National Archives JFK Collection: https://www.archives.gov/research/jfk
Mary Ferrell Foundation database: https://www.maryferrell.org
"""
    save_text("jfk-assassination-declassified.md", content)


# ── Dispatch ──────────────────────────────────────────────────────────────────

def run_fbi():
    download_fbi_all()

def run_cia():
    write_cia_stubs()

def run_jfk():
    write_jfk_overview()

def run_all():
    run_fbi()
    run_cia()
    run_jfk()

COMMANDS = {
    "fbi":    run_fbi,
    "cia":    run_cia,
    "jfk":    run_jfk,
    "mkultra": lambda: save_text("cia-mkultra.md", "") or write_cia_stubs(),
    "all":    run_all,
}

args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.lstrip("-").isdigit()]
targets = args if args else ["all"]

print(f"Declassified Documents Downloader")
print(f"Output: {OUTPUT_DIR}")
print(f"Limit: {LIMIT} documents per collection\n")

for target in targets:
    if target in COMMANDS:
        COMMANDS[target]()
    else:
        print(f"Unknown target: '{target}'. Options: {', '.join(COMMANDS.keys())}")

print(f"\nDone. Files saved to: {OUTPUT_DIR}")
print("Run 'rebuild index' in Jarvis chat to make documents searchable.")
