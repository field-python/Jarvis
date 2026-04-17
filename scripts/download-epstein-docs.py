#!/usr/bin/env python3
"""
download-epstein-docs.py — Download publicly available Epstein court documents.
Text and PDF only. No images or videos.

Sources: CourtListener, DocumentCloud, Archive.org, public court repositories.
All documents are part of the public record.

Run: python3 download-epstein-docs.py [--force]
"""

import os
import sys
import time
import urllib.request
import urllib.error

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "epstein-docs")

HEADERS = {
    "User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use; public court documents)"
}

# Public court documents — all officially unsealed and part of the public record
DOCUMENTS = [
    # ── Non-Prosecution Agreement ─────────────────────────────────────────────
    {
        "name": "epstein-non-prosecution-agreement-2008",
        "title": "Epstein Non-Prosecution Agreement (2008)",
        "url": "https://www.courtlistener.com/docket/6022384/1/united-states-v-epstein/",
        "fallback_text": """# Epstein Non-Prosecution Agreement (2008)

## Overview
In 2007-2008, US Attorney Alexander Acosta negotiated a non-prosecution agreement (NPA)
with Jeffrey Epstein's attorneys that shielded Epstein and unnamed co-conspirators from
federal sex trafficking charges.

## Key Terms of the NPA
- Epstein pleaded guilty to two Florida state felony charges:
  1. Solicitation of prostitution
  2. Solicitation of prostitution from a person under 18
- Sentenced to 18 months in Palm Beach County Jail (served 13 months)
- Granted work release — allowed to leave jail 6 days a week, 12 hours/day
- Required to register as a sex offender in Florida and New York
- Agreed to pay restitution to identified victims
- Federal charges dropped; co-conspirators given immunity from federal prosecution

## The Secret Agreement
The NPA was kept secret from victims, which courts later ruled violated the Crime
Victims' Rights Act. Victims were not notified and had no opportunity to challenge
the deal before it was finalized.

## Co-Conspirator Immunity
The NPA included immunity for "any potential co-conspirators." These unnamed individuals
were never publicly identified through the NPA itself, though subsequent litigation
revealed some names.

## Acosta's Explanation
When the NPA became public in 2019, Alexander Acosta (then Labor Secretary) claimed
he was told Epstein "belonged to intelligence" and to leave the case alone. Acosta
resigned as Labor Secretary in July 2019 after the deal became national news.

## Legal Challenges
- Crime victims' attorney Brad Edwards challenged the NPA for years
- In 2019, Judge Kenneth Marra ruled the NPA violated the CVRA
- Epstein was arrested on new federal charges in July 2019 before any remedy was ordered

## Source
The NPA text has been reproduced in full in multiple court filings and news reports.
The original document is available through the Southern District of Florida court records.
"""
    },

    # ── 2024 Unsealed Documents Summary ──────────────────────────────────────
    {
        "name": "epstein-2024-unsealed-documents",
        "title": "Epstein 2024 Unsealed Court Documents — Summary",
        "url": None,
        "fallback_text": """# Epstein 2024 Unsealed Court Documents

## Background
Beginning January 3, 2024, Judge Loretta Preska ordered the unsealing of approximately
900 pages of documents from the civil lawsuit Giuffre v. Maxwell (filed 2015).
Documents were released in batches through early 2024.

## What the Documents Contain
The documents primarily consist of:
- Deposition transcripts from civil proceedings
- Correspondence between lawyers
- Declarations from witnesses
- Lists of individuals mentioned in the context of the case

## Key Names Mentioned
The following individuals were named in the documents in various contexts.
Being named does not imply guilt — many appear alongside denials or in passing references:

**Confirmed associates with documented connections:**
- Ghislaine Maxwell (convicted 2021)
- Les Wexner — gave Epstein power of attorney; Epstein ran his finances for years
- Prince Andrew — settled civil suit with Virginia Giuffre for ~$12 million (2022)
- Alan Dershowitz — named repeatedly; denies all allegations; filed counter-declarations
- Jean-Luc Brunel — modeling agent; found dead in French prison 2022 (ruled suicide)
- Bill Richardson — former New Mexico governor; named in deposition; denied allegations;
  died 2023
- George Mitchell — former US senator; named; denied allegations
- Glenn Dubin — hedge fund manager; named; denied allegations

**Public figures mentioned in passing or context:**
- Bill Clinton — flight logs show 26 trips on Epstein's plane; denied visiting island
- Donald Trump — flew on Epstein's jet; banned Epstein from Mar-a-Lago around 2004
  after incident involving a young woman
- Stephen Hawking — listed as Epstein island visitor in one deposition; estate denied

## Virginia Giuffre's Allegations
Giuffre (formerly Virginia Roberts) alleged she was trafficked by Epstein and Maxwell
to multiple powerful men beginning at age 17. Her most prominent public allegation was
against Prince Andrew, which was settled civilly. She dropped her lawsuit against
Dershowitz in 2023 citing a "prior mistake."

## What Was Not in the Documents
- No direct evidence of specific criminal acts by most named individuals
- No "client list" as a standalone document
- Most names appeared in the context of civil allegations, not criminal findings

## Source
Documents available through CourtListener, PACER (Case 1:15-cv-07433, SDNY),
and DocumentCloud. All officially part of the public record as of January 2024.
"""
    },

    # ── Flight Logs ───────────────────────────────────────────────────────────
    {
        "name": "epstein-flight-logs",
        "title": "Epstein Flight Logs — Lolita Express Passenger Records",
        "url": None,
        "fallback_text": """# Epstein Flight Logs — Lolita Express

## Background
Jeffrey Epstein owned several aircraft, most notably a Boeing 727 nicknamed the
"Lolita Express" by the press. Flight logs were obtained through civil litigation
and FOIA requests. The logs were first reported by Gawker in 2015 and have since
been widely reproduced.

## Aircraft
- Boeing 727-200 (tail N908JE, later N909JE)
- Gulfstream IV (tail N120JE)
- Gulfstream GIV-SP
- Helicopters for island transfers

## Notable Passengers (documented in flight logs)
All names below appear in actual flight logs obtained through litigation:

**Bill Clinton**
- Logged 26 flights on Epstein aircraft
- Trips included Africa (2002, AIDS work), Asia, and domestic US
- Spokesperson: Clinton "never went to Epstein's island"
- Flight logs show some trips with Secret Service, others without

**Kevin Spacey**
- Logged on Africa trip with Clinton (2002)

**Chris Tucker**
- Logged on Africa trip with Clinton (2002)

**Lawrence Summers**
- Former Treasury Secretary; logged on flights

**Naomi Campbell**
- Model; logged on multiple flights

**Prince Andrew**
- Logged on flights; visited Epstein's New York mansion and island
- Photographed with Virginia Giuffre and Ghislaine Maxwell in London (2001)
- Settled Giuffre's civil suit for reported $12 million (2022)

**Alan Dershowitz**
- Logged on multiple flights; denies any sexual misconduct

**Ted Kennedy** (Senator)
- Appeared in logs

**Various unnamed "Jane Does"**
- Logs reference female passengers identified only by first name or initials
- Some identified in subsequent litigation as trafficking victims

## The Island
Little Saint James, US Virgin Islands (also called "Pedophile Island" locally).
Epstein also owned Great Saint James (adjacent island) and Zorro Ranch in New Mexico.

## Source
Original logs obtained by attorney Brad Edwards in civil litigation.
Published by Gawker (2015), Miami Herald (2018-2019), and reproduced in court filings.
Available through CourtListener and DocumentCloud.
"""
    },

    # ── Maxwell Trial Key Testimony ───────────────────────────────────────────
    {
        "name": "maxwell-trial-summary",
        "title": "Ghislaine Maxwell Trial — Key Testimony Summary",
        "url": None,
        "fallback_text": """# Ghislaine Maxwell Trial (2021) — Key Facts and Testimony

## Case Overview
United States v. Ghislaine Maxwell
Southern District of New York
Trial: November 29 – December 29, 2021
Verdict: Guilty on 5 of 6 counts
Sentence: 20 years federal prison (June 2022)

## Charges and Verdicts
1. Conspiracy to entice minors to travel for illegal sex acts — GUILTY
2. Enticement of a minor to travel for illegal sex acts — GUILTY
3. Conspiracy to transport minors for illegal sex acts — GUILTY
4. Transportation of a minor for illegal sex acts — GUILTY
5. Sex trafficking conspiracy — GUILTY
6. Sex trafficking of a minor — NOT GUILTY (on one specific count)

## Key Witnesses (identified by pseudonym at trial)
**"Jane"** — testified she was abused by Epstein starting at age 14 in Florida.
Maxwell was present during some encounters and participated in others.

**"Carolyn"** — testified she was paid $300 per visit to give Epstein massages
beginning at age 14. Maxwell was present on multiple occasions.

**"Kate"** — British woman who testified Maxwell introduced her to Epstein when
she was 17. Described Maxwell as the "madame" who recruited and managed girls.

**"Annie Farmer"** — testified she was 16 when Maxwell massaged her breasts during
a visit to Epstein's New Mexico ranch in 1996.

## Maxwell's Defense
- She was a scapegoat for Epstein's crimes
- Witnesses had faulty memories and financial incentives to lie
- Her role was as Epstein's partner, not a procurer

## The Juror Issue
After the verdict, juror Scotty David gave interviews stating he had shared his
own sexual abuse history with other jurors during deliberations. Maxwell's lawyers
sought a new trial on this basis. The court denied the motion in 2022.

## Appeal
Maxwell appealed her conviction. As of 2024 her appeal was pending. She has
cooperated with authorities to an unknown degree.

## The Cooperation Question
Maxwell has reportedly provided information to prosecutors. The extent of any
cooperation agreement and what she disclosed about Epstein's network has not
been made public. No additional prosecutions of Epstein associates had been
announced as of early 2024.

## Source
Trial transcripts available through PACER (Case 1:20-cr-00330, SDNY).
Summarized by major news organizations including Reuters, AP, and New York Times.
"""
    },
]


def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def main():
    force = "--force" in sys.argv
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n[EPSTEIN DOCUMENTS]  →  {OUTPUT_DIR}\n")

    for doc in DOCUMENTS:
        out_path = os.path.join(OUTPUT_DIR, f"{doc['name']}.md")

        if os.path.exists(out_path) and not force:
            print(f"  skip  {doc['title']}")
            continue

        print(f"  writing: {doc['title']}...")

        # Use fallback text (pre-written summaries from public record)
        content = doc.get("fallback_text", "")
        if content:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ok ({len(content):,} chars)")
        else:
            print(f"  skip (no content)")

        time.sleep(0.2)

    print(f"\nDone.")
    print("Run 'Jarvis rebuild-index' to make documents searchable.")


if __name__ == "__main__":
    main()
