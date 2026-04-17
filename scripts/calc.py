#!/usr/bin/env python3
"""calc.py — instant calculator and unit converter, no LLM needed"""
import sys, re, math

YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

if len(sys.argv) < 2:
    print('Usage: Jarvis calc "expression"')
    print('Examples:')
    print('  Jarvis calc "15% of 84"')
    print('  Jarvis calc "180 lbs to kg"')
    print('  Jarvis calc "72 F to C"')
    print('  Jarvis calc "5 * (3 + 2)"')
    sys.exit(1)

expr = " ".join(sys.argv[1:]).strip().lower()

# ── Unit conversions ──────────────────────────────────────────────────────────
CONVERSIONS = [
    # Weight
    (r'([\d.]+)\s*lbs?\s+to\s+kg',     lambda v: (v * 0.453592,  f"{v} lbs = {v*0.453592:.3f} kg")),
    (r'([\d.]+)\s*kg\s+to\s+lbs?',     lambda v: (v * 2.20462,   f"{v} kg = {v*2.20462:.3f} lbs")),
    (r'([\d.]+)\s*oz\s+to\s+g',        lambda v: (v * 28.3495,   f"{v} oz = {v*28.3495:.2f} g")),
    (r'([\d.]+)\s*g\s+to\s+oz',        lambda v: (v / 28.3495,   f"{v} g = {v/28.3495:.3f} oz")),
    (r'([\d.]+)\s*tons?\s+to\s+lbs?',  lambda v: (v * 2000,      f"{v} ton = {v*2000:,.0f} lbs")),
    # Temperature
    (r'([\d.]+)\s*f\s+to\s+c',         lambda v: ((v-32)*5/9,    f"{v}°F = {(v-32)*5/9:.1f}°C")),
    (r'([\d.]+)\s*c\s+to\s+f',         lambda v: (v*9/5+32,      f"{v}°C = {v*9/5+32:.1f}°F")),
    (r'([\d.]+)\s*c\s+to\s+k',         lambda v: (v+273.15,      f"{v}°C = {v+273.15:.2f} K")),
    # Distance
    (r'([\d.]+)\s*miles?\s+to\s+km',   lambda v: (v * 1.60934,   f"{v} mi = {v*1.60934:.3f} km")),
    (r'([\d.]+)\s*km\s+to\s+miles?',   lambda v: (v / 1.60934,   f"{v} km = {v/1.60934:.3f} mi")),
    (r'([\d.]+)\s*ft\s+to\s+m',        lambda v: (v * 0.3048,    f"{v} ft = {v*0.3048:.3f} m")),
    (r'([\d.]+)\s*m\s+to\s+ft',        lambda v: (v / 0.3048,    f"{v} m = {v/0.3048:.3f} ft")),
    (r'([\d.]+)\s*inches?\s+to\s+cm',  lambda v: (v * 2.54,      f"{v} in = {v*2.54:.2f} cm")),
    (r'([\d.]+)\s*cm\s+to\s+inches?',  lambda v: (v / 2.54,      f"{v} cm = {v/2.54:.3f} in")),
    (r'([\d.]+)\s*yards?\s+to\s+m',    lambda v: (v * 0.9144,    f"{v} yd = {v*0.9144:.3f} m")),
    # Volume
    (r'([\d.]+)\s*gal\w*\s+to\s+l',    lambda v: (v * 3.78541,   f"{v} gal = {v*3.78541:.3f} L")),
    (r'([\d.]+)\s*l\s+to\s+gal\w*',    lambda v: (v / 3.78541,   f"{v} L = {v/3.78541:.3f} gal")),
    (r'([\d.]+)\s*cups?\s+to\s+ml',    lambda v: (v * 236.588,   f"{v} cup = {v*236.588:.1f} mL")),
    (r'([\d.]+)\s*ml\s+to\s+cups?',    lambda v: (v / 236.588,   f"{v} mL = {v/236.588:.3f} cups")),
    (r'([\d.]+)\s*tbsp\w*\s+to\s+ml',  lambda v: (v * 14.7868,   f"{v} tbsp = {v*14.7868:.1f} mL")),
    (r'([\d.]+)\s*tsp\w*\s+to\s+ml',   lambda v: (v * 4.92892,   f"{v} tsp = {v*4.92892:.2f} mL")),
    # Speed
    (r'([\d.]+)\s*mph\s+to\s+kph',     lambda v: (v * 1.60934,   f"{v} mph = {v*1.60934:.2f} km/h")),
    (r'([\d.]+)\s*kph\s+to\s+mph',     lambda v: (v / 1.60934,   f"{v} km/h = {v/1.60934:.2f} mph")),
    # Area
    (r'([\d.]+)\s*acres?\s+to\s+sqft', lambda v: (v * 43560,     f"{v} acres = {v*43560:,.0f} sq ft")),
    (r'([\d.]+)\s*sqft\s+to\s+acres?', lambda v: (v / 43560,     f"{v} sq ft = {v/43560:.4f} acres")),
    # Data
    (r'([\d.]+)\s*gb\s+to\s+mb',       lambda v: (v * 1024,      f"{v} GB = {v*1024:,.0f} MB")),
    (r'([\d.]+)\s*tb\s+to\s+gb',       lambda v: (v * 1024,      f"{v} TB = {v*1024:,.0f} GB")),
    # Percentage helpers
    (r'([\d.]+)%\s+of\s+([\d.]+)',      None),   # handled separately
    (r'([\d.]+)\s+percent\s+of\s+([\d.]+)', None),
]

# Check percentage patterns first
pct_match = re.search(r'([\d.]+)\s*%?\s*(?:percent\s+)?of\s+([\d.]+)', expr)
if pct_match:
    pct = float(pct_match.group(1))
    total = float(pct_match.group(2))
    result = pct / 100 * total
    print()
    print(f"  {BOLD}{pct}% of {total} = {result:g}{RESET}")
    print()
    sys.exit(0)

# Check unit conversions
for pattern, fn in CONVERSIONS:
    if fn is None:
        continue
    m = re.search(pattern, expr)
    if m:
        val = float(m.group(1))
        _, label = fn(val)
        print()
        print(f"  {BOLD}{label}{RESET}")
        print()
        sys.exit(0)

# ── Math expression ────────────────────────────────────────────────────────────
# Clean up natural language
expr_clean = expr
expr_clean = re.sub(r'\btimes\b', '*', expr_clean)
expr_clean = re.sub(r'\bdivided by\b', '/', expr_clean)
expr_clean = re.sub(r'\bplus\b', '+', expr_clean)
expr_clean = re.sub(r'\bminus\b', '-', expr_clean)
expr_clean = re.sub(r'\bsquared\b', '**2', expr_clean)
expr_clean = re.sub(r'\bcubed\b', '**3', expr_clean)
expr_clean = re.sub(r'\bsqrt\s*of\s*([\d.]+)', r'sqrt(\1)', expr_clean)

# Safe eval — only allow numbers and math operators
safe_expr = re.sub(r'[^0-9+\-*/().%^ ]', '', expr_clean).strip()
if not safe_expr:
    print(f"  Couldn't parse: {' '.join(sys.argv[1:])}")
    sys.exit(1)

safe_expr = safe_expr.replace('^', '**')

try:
    result = eval(safe_expr, {"__builtins__": {}}, {
        "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "abs": abs,
    })
    # Format nicely
    if isinstance(result, float) and result == int(result):
        result = int(result)
    elif isinstance(result, float):
        result = round(result, 10)
    print()
    print(f"  {BOLD}{' '.join(sys.argv[1:])} = {result:,}{RESET}")
    print()
except Exception as e:
    print(f"  Couldn't calculate: {e}")
    sys.exit(1)
