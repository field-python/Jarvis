#!/usr/bin/env python3
"""
download-law.py — Download comprehensive legal reference content:
  Black's Law Dictionary history, landmark cases, legal concepts,
  foundational documents, maritime law, corporate law, common law,
  legal technicalities, constitutional law, and international foundations.

Run: Jarvis download-law [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "law")

TOPICS = {

    # ── Black's Law Dictionary & Legal Reference ──────────────────────────────
    "blacks-law": [
        "Black's Law Dictionary",
        "Henry Campbell Black",
        "Legal dictionary",
        "Law dictionary",
        "Corpus Juris Secundum",
        "American Jurisprudence",
        "Restatements of the Law",
        "Law review",
        "Legal citation",
        "Stare decisis",
        "Precedent",
        "Common law",
        "Equity (law)",
        "Jurisprudence",
        "Natural law",
        "Positive law",
        "Legal realism",
        "Statutory interpretation",
        "Legal fiction",
        "Pro se legal representation in the United States",
        "Legal aid",
        "Legal ethics",
        "Bar association",
        "American Bar Association",
        "Law school",
        "Paralegal",
    ],

    # ── Foundational & Historical Legal Documents ─────────────────────────────
    "foundational-documents": [
        "Magna Carta",
        "Petition of Right",
        "Habeas Corpus Act 1679",
        "English Bill of Rights",
        "Declaration of Independence (United States)",
        "United States Constitution",
        "Bill of Rights (United States)",
        "Articles of Confederation",
        "Mayflower Compact",
        "Federalist Papers",
        "Anti-Federalist Papers",
        "Emancipation Proclamation",
        "Gettysburg Address",
        "Fourteenth Amendment to the United States Constitution",
        "Nineteenth Amendment to the United States Constitution",
        "Code of Hammurabi",
        "Twelve Tables",
        "Justinian Code",
        "Napoleonic Code",
        "Magna Carta in the United States",
        "Universal Declaration of Human Rights",
        "Geneva Conventions",
        "United Nations Charter",
    ],

    # ── US Constitutional Law ──────────────────────────────────────────────────
    "constitutional-law": [
        "Constitutional law",
        "First Amendment to the United States Constitution",
        "Second Amendment to the United States Constitution",
        "Third Amendment to the United States Constitution",
        "Fourth Amendment to the United States Constitution",
        "Fifth Amendment to the United States Constitution",
        "Sixth Amendment to the United States Constitution",
        "Seventh Amendment to the United States Constitution",
        "Eighth Amendment to the United States Constitution",
        "Ninth Amendment to the United States Constitution",
        "Tenth Amendment to the United States Constitution",
        "Fourteenth Amendment to the United States Constitution",
        "Fifteenth Amendment to the United States Constitution",
        "Commerce Clause",
        "Due Process Clause",
        "Equal Protection Clause",
        "Establishment Clause",
        "Free Exercise Clause",
        "Free Speech Clause",
        "Separation of powers under the United States Constitution",
        "Checks and balances",
        "Federalism in the United States",
        "Judicial review in the United States",
        "Executive privilege",
        "Impeachment in the United States",
    ],

    # ── Landmark US Supreme Court Cases ───────────────────────────────────────
    "supreme-court-cases": [
        "Marbury v. Madison",
        "McCulloch v. Maryland",
        "Gibbons v. Ogden",
        "Dred Scott v. Sandford",
        "Plessy v. Ferguson",
        "Lochner v. New York",
        "Schenck v. United States",
        "Korematsu v. United States",
        "Brown v. Board of Education",
        "Mapp v. Ohio",
        "Gideon v. Wainwright",
        "Engel v. Vitale",
        "Escobedo v. Illinois",
        "Miranda v. Arizona",
        "Griswold v. Connecticut",
        "Loving v. Virginia",
        "Terry v. Ohio",
        "Tinker v. Des Moines Independent Community School District",
        "Roe v. Wade",
        "United States v. Nixon",
        "Regents of the University of California v. Bakke",
        "Texas v. Johnson",
        "Planned Parenthood v. Casey",
        "Romer v. Evans",
        "Bush v. Gore",
        "Lawrence v. Texas",
        "District of Columbia v. Heller",
        "Citizens United v. FEC",
        "McDonald v. City of Chicago",
        "Obergefell v. Hodges",
        "Dobbs v. Jackson Women's Health Organization",
        "New York Times Co. v. Sullivan",
        "Kelo v. City of New London",
        "Shelby County v. Holder",
    ],

    # ── Criminal Law & Procedure ───────────────────────────────────────────────
    "criminal-law": [
        "Criminal law",
        "Criminal procedure",
        "Arraignment",
        "Grand jury",
        "Indictment",
        "Preliminary hearing",
        "Bail",
        "Remand (detention)",
        "Trial",
        "Burden of proof (law)",
        "Beyond reasonable doubt",
        "Acquittal",
        "Conviction",
        "Sentencing",
        "Criminal defense lawyer",
        "Prosecutor",
        "District attorney",
        "Public defender",
        "Plea bargain",
        "Jury trial",
        "Bench trial",
        "Hung jury",
        "Double jeopardy",
        "Self-incrimination",
        "Miranda warning",
        "Right to counsel",
        "Exclusionary rule",
        "Fruit of the poisonous tree",
        "Chain of custody",
        "Mens rea",
        "Actus reus",
        "Criminal intent",
        "Strict liability",
        "Conspiracy (criminal)",
        "Accessory (legal term)",
        "Felony",
        "Misdemeanor",
        "Statute of limitations",
        "Speedy trial",
        "Change of venue",
        "Sequestration (law)",
        "Expert witness",
        "Hearsay (evidence law)",
        "Admissible evidence",
        "Search warrant",
        "Probable cause",
        "Reasonable suspicion",
        "Stop and frisk",
        "Consent search",
        "Plain view doctrine",
        "Exigent circumstances",
    ],

    # ── Legal Technicalities & Defenses ───────────────────────────────────────
    "legal-defenses": [
        "Affirmative defense",
        "Insanity defense",
        "Self-defense (legal)",
        "Stand-your-ground law",
        "Castle doctrine",
        "Justification (jurisprudence)",
        "Entrapment",
        "Duress (law)",
        "Necessity (criminal law)",
        "Alibi",
        "Statute of limitations",
        "Double jeopardy",
        "Speedy Trial Act",
        "Brady v. Maryland",
        "Prosecutorial misconduct",
        "Ineffective assistance of counsel",
        "Habeas corpus",
        "Writ of certiorari",
        "Fruit of the poisonous tree",
        "Exclusionary rule",
        "Alford plea",
        "Nolo contendere",
        "Acquittal",
        "Jury nullification",
        "Diminished responsibility",
        "Intoxication defense",
        "Coerced confession",
        "Chain of custody",
        "Wrongful conviction",
        "Innocence Project",
        "Post-conviction relief",
        "Appeals court",
        "Reversal (law)",
        "Mistrial",
    ],

    # ── Famous Acquittals & Landmark Criminal Cases ────────────────────────────
    "famous-cases": [
        "O. J. Simpson murder case",
        "Trial of O. J. Simpson",
        "Casey Anthony trial",
        "George Zimmerman trial",
        "Scott Peterson case",
        "Phil Spector murder trial",
        "Steven Avery",
        "Making a Murderer",
        "West Memphis Three",
        "Rodney King",
        "Emmett Till",
        "Leopold and Loeb",
        "Sacco and Vanzetti",
        "Scottsboro Boys",
        "Sam Sheppard murder case",
        "Jeffrey MacDonald case",
        "John Hinckley Jr.",
        "Dan White",
        "Twinkie defense",
        "Menendez brothers",
        "Lorena Bobbitt",
        "Clarence Darrow",
        "Johnny Cochran",
        "F. Lee Bailey",
        "Alan Dershowitz",
        "Bryan Stevenson",
    ],

    # ── Civil Law ─────────────────────────────────────────────────────────────
    "civil-law": [
        "Civil law (common law)",
        "Tort",
        "Negligence",
        "Strict liability (tort)",
        "Intentional tort",
        "Personal injury",
        "Wrongful death claim",
        "Medical malpractice",
        "Product liability",
        "Defamation",
        "Libel",
        "Slander",
        "Privacy laws of the United States",
        "Trespass",
        "Nuisance",
        "Contract",
        "Breach of contract",
        "Consideration (contract law)",
        "Fraud",
        "Unjust enrichment",
        "Class action",
        "Small claims court",
        "Arbitration",
        "Mediation",
        "Settlement (litigation)",
        "Damages",
        "Punitive damages",
        "Injunction",
        "Restraining order",
        "Statute of frauds",
    ],

    # ── Corporate & Business Law ───────────────────────────────────────────────
    "corporate-law": [
        "Corporate law",
        "Corporation",
        "Limited liability company",
        "Partnership",
        "Sole proprietorship",
        "Incorporation (business)",
        "Articles of incorporation",
        "Bylaws",
        "Board of directors",
        "Fiduciary duty",
        "Shareholder",
        "Shareholder rights",
        "Hostile takeover",
        "Mergers and acquisitions",
        "Initial public offering",
        "Securities regulation",
        "Securities Exchange Act of 1934",
        "Securities and Exchange Commission",
        "Insider trading",
        "Ponzi scheme",
        "Antitrust",
        "Sherman Antitrust Act",
        "Clayton Antitrust Act",
        "Federal Trade Commission",
        "Bankruptcy",
        "Chapter 7, Title 11, United States Code",
        "Chapter 11, Title 11, United States Code",
        "Chapter 13, Title 11, United States Code",
        "Contract law",
        "Non-disclosure agreement",
        "Non-compete clause",
        "Employment discrimination",
        "Whistleblower",
        "Sarbanes–Oxley Act",
        "Dodd–Frank Wall Street Reform and Consumer Protection Act",
        "RICO (law)",
    ],

    # ── Maritime & Admiralty Law ───────────────────────────────────────────────
    "maritime-law": [
        "Admiralty law",
        "Maritime law",
        "Jones Act",
        "Longshoreman and Harbor Workers' Compensation Act",
        "Carriage of Goods by Sea Act",
        "Salvage (maritime law)",
        "General average",
        "Marine insurance",
        "Bill of lading",
        "Ship registration",
        "Flag state",
        "Piracy",
        "Prize (law)",
        "Territorial waters",
        "Exclusive economic zone",
        "United Nations Convention on the Law of the Sea",
        "International Maritime Organization",
        "Port authority",
        "Shipping law",
        "Charter party",
        "Shipwreck",
        "Maritime lien",
        "Arrest of ships",
        "Limitation of liability (maritime law)",
        "Seaman (occupation)",
        "Maintenance and cure",
    ],

    # ── Property & Real Estate Law ─────────────────────────────────────────────
    "property-law": [
        "Property law",
        "Real property",
        "Personal property",
        "Intellectual property",
        "Ownership",
        "Title (property)",
        "Deed",
        "Easement",
        "Lien",
        "Mortgage loan",
        "Foreclosure",
        "Eminent domain",
        "Takings Clause",
        "Adverse possession",
        "Landlord–tenant law",
        "Eviction",
        "Lease",
        "Rent control",
        "Homestead exemption",
        "Zoning in the United States",
        "Deed of trust (real estate)",
        "Title insurance",
        "Property tax",
        "Probate",
        "Will (law)",
        "Trust law",
        "Inheritance tax",
        "Power of attorney",
        "Guardianship",
    ],

    # ── Family & Personal Law ──────────────────────────────────────────────────
    "family-law": [
        "Family law",
        "Divorce",
        "Child custody",
        "Child support",
        "Alimony",
        "Prenuptial agreement",
        "Annulment",
        "Adoption",
        "Parental rights",
        "Domestic violence",
        "Restraining order",
        "Child abuse",
        "Foster care",
        "Juvenile court",
        "Age of consent",
        "Emancipation of minors",
        "Guardianship",
        "Conservatorship",
        "Living will",
        "Advance healthcare directive",
    ],

    # ── Civil Rights & Constitutional Rights ──────────────────────────────────
    "civil-rights-law": [
        "Civil rights",
        "Civil Rights Act of 1964",
        "Voting Rights Act of 1965",
        "Americans with Disabilities Act of 1990",
        "Fair Housing Act",
        "Equal Employment Opportunity Commission",
        "Affirmative action",
        "Brown v. Board of Education",
        "Loving v. Virginia",
        "Heart of Atlanta Motel, Inc. v. United States",
        "Freedom of speech in the United States",
        "Freedom of religion in the United States",
        "Right to bear arms",
        "Police brutality in the United States",
        "Section 1983",
        "Qualified immunity",
        "Sovereign immunity",
        "Civil Rights Movement",
        "NAACP",
        "ACLU",
        "Fourth Amendment to the United States Constitution",
    ],

    # ── International & Comparative Law ───────────────────────────────────────
    "international-law": [
        "International law",
        "Public international law",
        "Private international law",
        "Treaty",
        "Vienna Convention on the Law of Treaties",
        "International Court of Justice",
        "International Criminal Court",
        "War crime",
        "Crime against humanity",
        "Genocide",
        "Nuremberg trials",
        "Geneva Conventions",
        "Hague Conventions",
        "Diplomatic immunity",
        "Extradition",
        "Asylum seeker",
        "Refugee law",
        "Universal Declaration of Human Rights",
        "European Convention on Human Rights",
        "Amnesty International",
        "Human Rights Watch",
        "Customary international law",
        "Sovereignty",
        "Jurisdiction",
        "Comity",
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
