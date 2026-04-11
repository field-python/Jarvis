#!/usr/bin/env bash
# download-tier1.sh — fetch Tier 1 reference pages for Jarvis
# Sources: US government and public health sites (no paywalls, no photos needed)
# Run time: a few minutes depending on connection speed

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
base_dir="$(cd -- "$script_dir/.." && pwd -P)"
pages_dir="$base_dir/pages"
index_file="$base_dir/index/sources.md"
ua="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"

mkdir -p "$pages_dir" "$base_dir/index"
stamp="$(date +%F)"
ok=0
fail=0

fetch() {
  local name="$1" url="$2"
  local out="$pages_dir/$name.html"
  if curl -L --fail --silent --show-error --max-time 30 \
      -A "$ua" \
      -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
      "$url" -o "$out" 2>/dev/null; then
    printf -- '- `pages/%s.html` - %s - saved %s\n' "$name" "$url" "$stamp" >> "$index_file"
    echo "  OK  $name"
    return 0
  else
    echo "  FAIL $name ($url)"
    return 1
  fi
}

run_fetch() {
  if fetch "$1" "$2"; then
    echo "ok" >> /tmp/jarvis-dl-ok-$$
  else
    echo "fail" >> /tmp/jarvis-dl-fail-$$
  fi
}

rm -f /tmp/jarvis-dl-ok-$$ /tmp/jarvis-dl-fail-$$

echo ""
echo "=== HOME REPAIR & DIY ==="
run_fetch "home-repair-weatherization"      "https://www.energy.gov/energysaver/weatherize-your-home" &
run_fetch "home-repair-insulation"          "https://www.energy.gov/energysaver/insulation" &
run_fetch "home-repair-air-sealing"         "https://www.energy.gov/energysaver/air-sealing-your-home" &
run_fetch "home-repair-water-heating"       "https://www.energy.gov/energysaver/water-heating" &
run_fetch "home-repair-plumbing"            "https://www.energy.gov/energysaver/plumbing" &
run_fetch "home-repair-windows-doors"       "https://www.energy.gov/energysaver/windows-doors-and-skylights" &
run_fetch "home-repair-asbestos"            "https://www.epa.gov/asbestos/protect-your-family-asbestos" &
run_fetch "home-repair-radon"               "https://www.epa.gov/radon/health-risk-radon" &
run_fetch "home-repair-lead-paint"          "https://www.epa.gov/lead/protect-your-family-lead-your-home" &
run_fetch "home-repair-electrical-safety"   "https://www.osha.gov/electrical" &
run_fetch "home-repair-co-safety"           "https://www.cpsc.gov/Safety-Education/Safety-Education-Centers/Carbon-Monoxide-Information-Center" &
run_fetch "home-repair-mold"                "https://www.epa.gov/mold/mold-course-chapter-1" &
wait

echo ""
echo "=== AUTOMOTIVE ==="
run_fetch "auto-car-care-tips"              "https://www.carcare.org/car-care-tips/" &
run_fetch "auto-tire-safety"                "https://www.nhtsa.gov/vehicle-safety/tires" &
run_fetch "auto-fuel-economy-tips"          "https://www.fueleconomy.gov/feg/drive.shtml" &
run_fetch "auto-fuel-economy-why"           "https://www.fueleconomy.gov/feg/why.shtml" &
run_fetch "auto-vehicle-recalls"            "https://www.nhtsa.gov/recalls" &
run_fetch "auto-brake-safety"               "https://www.nhtsa.gov/vehicle-safety/brakes" &
run_fetch "auto-winter-driving"             "https://www.nhtsa.gov/winter-driving-safety" &
run_fetch "auto-battery-basics"             "https://www.carcare.org/car-care-guides/battery-care-guide/" &
wait

echo ""
echo "=== COOKING & NUTRITION ==="
run_fetch "nutrition-food-safety-4steps"    "https://www.foodsafety.gov/keep-food-safe/4-steps-to-food-safety" &
run_fetch "nutrition-safe-food-handling"    "https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling" &
run_fetch "nutrition-food-storage-chart"    "https://www.foodsafety.gov/keep-food-safe/foodkeeper-app" &
run_fetch "nutrition-myplate-basics"        "https://www.myplate.gov/eat-healthy/what-is-myplate" &
run_fetch "nutrition-protein-foods"         "https://www.myplate.gov/eat-healthy/protein-foods" &
run_fetch "nutrition-vegetables"            "https://www.myplate.gov/eat-healthy/vegetables" &
run_fetch "nutrition-fruits"                "https://www.myplate.gov/eat-healthy/fruits" &
run_fetch "nutrition-grains"                "https://www.myplate.gov/eat-healthy/grains" &
run_fetch "nutrition-dairy"                 "https://www.myplate.gov/eat-healthy/dairy" &
run_fetch "nutrition-facts-label"           "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label" &
run_fetch "nutrition-dietary-guidelines"    "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials" &
run_fetch "nutrition-food-safety-pregnancy" "https://www.foodsafety.gov/people-at-risk/pregnant-women" &
wait

echo ""
echo "=== PERSONAL FINANCE ==="
run_fetch "finance-managing-your-money"     "https://consumer.gov/managing-your-money" &
run_fetch "finance-budgeting-basics"        "https://consumer.gov/managing-your-money/make-budget-work-you" &
run_fetch "finance-saving-money"            "https://consumer.gov/managing-your-money/saving-and-investing" &
run_fetch "finance-credit-basics"           "https://consumer.gov/managing-your-money/credit-and-debt" &
run_fetch "finance-dealing-with-debt"       "https://consumer.gov/managing-your-money/dealing-with-debt" &
run_fetch "finance-understanding-credit"    "https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/" &
run_fetch "finance-buying-home"             "https://www.consumerfinance.gov/owning-a-home/" &
run_fetch "finance-student-loans"           "https://studentaid.gov/resources/repayment-overview" &
run_fetch "finance-irs-tax-basics"          "https://www.irs.gov/individuals/tax-information-for-individuals" &
run_fetch "finance-social-security"         "https://www.ssa.gov/benefits/retirement/" &
run_fetch "finance-medicare-basics"         "https://www.medicare.gov/basics/get-started-with-medicare" &
run_fetch "finance-scam-protection"         "https://consumer.ftc.gov/articles/what-do-if-you-were-scammed" &
wait

echo ""
echo "=== HEALTH & SYMPTOMS ==="
run_fetch "health-when-to-call-doctor"      "https://medlineplus.gov/ency/article/001959.htm" &
run_fetch "health-vital-signs"              "https://medlineplus.gov/ency/article/002341.htm" &
run_fetch "health-fever-basics"             "https://medlineplus.gov/fever.html" &
run_fetch "health-chest-pain"               "https://medlineplus.gov/chestpain.html" &
run_fetch "health-headache"                 "https://medlineplus.gov/headache.html" &
run_fetch "health-back-pain"                "https://medlineplus.gov/backpain.html" &
run_fetch "health-diabetes"                 "https://medlineplus.gov/diabetes.html" &
run_fetch "health-high-blood-pressure"      "https://medlineplus.gov/highbloodpressure.html" &
run_fetch "health-heart-disease"            "https://medlineplus.gov/heartdisease.html" &
run_fetch "health-stroke-signs"             "https://medlineplus.gov/stroke.html" &
run_fetch "health-asthma"                   "https://medlineplus.gov/asthma.html" &
run_fetch "health-allergies"                "https://medlineplus.gov/allergy.html" &
run_fetch "health-mental-health"            "https://medlineplus.gov/mentalhealth.html" &
run_fetch "health-depression"               "https://medlineplus.gov/depression.html" &
run_fetch "health-anxiety"                  "https://medlineplus.gov/anxiety.html" &
run_fetch "health-sleep"                    "https://medlineplus.gov/sleep.html" &
run_fetch "health-nutrition-overview"       "https://medlineplus.gov/nutrition.html" &
run_fetch "health-exercise-fitness"         "https://medlineplus.gov/exerciseandphysicalfitness.html" &
run_fetch "health-first-aid-overview"       "https://medlineplus.gov/firstaid.html" &
run_fetch "health-pain-management"          "https://medlineplus.gov/pain.html" &
wait

echo ""
echo "=== MEDICATIONS ==="
run_fetch "meds-drug-info-overview"         "https://medlineplus.gov/druginformation.html" &
run_fetch "meds-common-otc"                 "https://www.fda.gov/drugs/buying-using-medicine-safely/buying-medicines-online" &
run_fetch "meds-safe-use"                   "https://www.fda.gov/drugs/buying-using-medicine-safely/best-practices-taking-medication" &
run_fetch "meds-storage"                    "https://medlineplus.gov/ency/patientinstructions/000391.htm" &
run_fetch "meds-interactions"               "https://medlineplus.gov/druginteractions.html" &
run_fetch "meds-antibiotics-guide"          "https://www.cdc.gov/antibiotic-use/community/index.html" &
run_fetch "meds-pain-relievers"             "https://medlineplus.gov/painrelievers.html" &
run_fetch "meds-first-aid-kit"              "https://www.redcross.org/get-help/how-to-prepare-for-emergencies/anatomy-of-a-first-aid-kit.html" &
wait

# count results
ok=$(wc -l < /tmp/jarvis-dl-ok-$$ 2>/dev/null || echo 0)
fail=$(wc -l < /tmp/jarvis-dl-fail-$$ 2>/dev/null || echo 0)
rm -f /tmp/jarvis-dl-ok-$$ /tmp/jarvis-dl-fail-$$

echo ""
echo "============================================"
echo "Done. $ok pages saved, $fail failed."
echo "Archive: $pages_dir"
echo "============================================"
