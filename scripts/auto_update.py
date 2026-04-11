#!/usr/bin/env python3
"""auto_update.py — refresh key pages in the Jarvis archive (cross-platform replacement for auto-update.sh)"""
import re
import time
import urllib.request
from pathlib import Path
from datetime import datetime

script_dir  = Path(__file__).parent.resolve()
base_dir    = script_dir.parent
pages_dir   = base_dir / "pages"
index_file  = base_dir / "index" / "sources.md"
pages_dir.mkdir(parents=True, exist_ok=True)
(base_dir / "index").mkdir(parents=True, exist_ok=True)

UA        = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/135.0 Safari/537.36")
SEVEN_DAYS = 7 * 24 * 3600
now        = datetime.now()
stamp      = now.strftime("%Y-%m-%d")

ok = skip = fail = 0


def fetch_if_stale(name, url):
    global ok, skip, fail
    out = pages_dir / f"{name}.html"

    if out.exists() and (time.time() - out.stat().st_mtime) < SEVEN_DAYS:
        skip += 1
        return

    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            out.write_bytes(resp.read())
        with index_file.open("a", encoding="utf-8") as f:
            f.write(f"- `pages/{name}.html` - {url} - updated {stamp}\n")
        print(f"  updated  {name}")
        ok += 1
    except Exception:
        print(f"  failed   {name}")
        fail += 1


print(f"Jarvis auto-update — {now.strftime('%Y-%m-%d %H:%M')}")
print()

# ── Health ────────────────────────────────────────────────────────────────────
fetch_if_stale("health-fever-basics",         "https://medlineplus.gov/fever.html")
fetch_if_stale("health-first-aid-overview",   "https://medlineplus.gov/firstaid.html")
fetch_if_stale("health-mental-health",        "https://medlineplus.gov/mentalhealth.html")
fetch_if_stale("health-high-blood-pressure",  "https://medlineplus.gov/highbloodpressure.html")
fetch_if_stale("health-diabetes",             "https://medlineplus.gov/diabetes.html")
fetch_if_stale("meds-drug-info-overview",     "https://medlineplus.gov/druginformation.html")
fetch_if_stale("meds-antibiotics-guide",      "https://www.cdc.gov/antibiotic-use/index.html")

# ── Safety & preparedness ─────────────────────────────────────────────────────
fetch_if_stale("home-repair-radon",      "https://www.epa.gov/radon/health-risk-radon")
fetch_if_stale("home-repair-lead-paint", "https://www.epa.gov/lead/protect-your-family-lead-your-home")
fetch_if_stale("home-repair-mold",       "https://www.epa.gov/mold/mold-course-chapter-1")

# ── Finance ───────────────────────────────────────────────────────────────────
fetch_if_stale("finance-scam-protection",   "https://consumer.ftc.gov/articles/what-do-if-you-were-scammed")
fetch_if_stale("finance-dealing-with-debt", "https://consumer.ftc.gov/articles/coping-debt")
fetch_if_stale("finance-irs-tax-basics",    "https://www.irs.gov/filing")

# ── Nutrition ─────────────────────────────────────────────────────────────────
fetch_if_stale("nutrition-safe-food-handling", "https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling")
fetch_if_stale("nutrition-myplate-basics",     "https://www.myplate.gov/eat-healthy/what-is-myplate")

# ── Auto ──────────────────────────────────────────────────────────────────────
fetch_if_stale("auto-maintenance-schedule", "https://www.fueleconomy.gov/feg/maintain.shtml")
fetch_if_stale("auto-winterize",            "https://www.dmv.org/how-to-guides/winterize-car.php")

# ── Current events (always refresh) ──────────────────────────────────────────
print()
print("Fetching current events...")

current_events_file = base_dir / "notes" / "current-events.md"
today = f"{now.strftime('%A, %B')} {now.day}, {now.year}"

lines = [
    "# Current Events",
    f"<!-- Last updated: {today} -->",
    "",
]


def fetch_rss_titles(url, max_items=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        titles = re.findall(r'<title>([^<]+)</title>', content)
        return [t for t in titles if "Google News" not in t][:max_items]
    except Exception:
        return []


world_titles = fetch_rss_titles("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", 15)
lines += ["## US & World News"]
lines += [f"- {t}" for t in world_titles] if world_titles else ["- (could not fetch)"]
lines.append("")

ent_titles = fetch_rss_titles(
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
    10
)
lines += ["## Entertainment"]
lines += [f"- {t}" for t in ent_titles] if ent_titles else ["- (could not fetch)"]
lines.append("")

sports_titles = fetch_rss_titles(
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
    10
)
lines += ["## Sports"]
lines += [f"- {t}" for t in sports_titles] if sports_titles else ["- (could not fetch)"]
lines.append("")

lines += [
    "## Key Facts",
    "- Current US President: Donald Trump (took office January 20, 2025)",
    f"- Last updated: {today}",
]

current_events_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("  current events updated")

print()
print(f"Done — {ok} updated, {skip} skipped, {fail} failed.")
if skip > 0:
    print("  (skipped = pages fetched within the last 7 days, still current)")
print("  Note: base knowledge comes from model training — only web-fetched pages update here.")
