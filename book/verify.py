import re, glob, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(ROOT, 'recipes', '*.md')),
               key=lambda f: int(os.path.basename(f).split('-', 1)[0]))
print(f"Files: {len(files)}")
nums = [int(os.path.basename(f).split('-', 1)[0]) for f in files]
missing = sorted(set(range(1, len(files) + 1)) - set(nums))
print("Missing numbers:", missing or "none")
def section(t, name):
    m = re.search(r'^## ' + re.escape(name) + r'\s*$(.*?)(?=^## |\Z)', t, re.M | re.S)
    return m.group(1).strip() if m else ''

EXPECT = ["Why it works","Ingredients","Method","Chef's notes","For the toddler",
          "Nutrition (per serving, approx.)","Washing up"]
BANNED = ["delicious","flavorful","flavourful","elevate","game-changer","game changer","whip up","burst of flavour","burst of flavor"]
problems=[]
rows=[]
for f in files:
    t = open(f, encoding='utf-8').read()
    n = os.path.basename(f)
    h1 = re.findall(r'^# (.+)$', t, re.M)
    h2 = re.findall(r'^## (.+)$', t, re.M)
    if len(h1)!=1: problems.append(f"{n}: {len(h1)} H1s")
    if h2 != EXPECT: problems.append(f"{n}: H2 mismatch -> {h2}")
    m = re.search(r'\*\*Cuisine:\*\* (.+?) · \*\*Method:\*\* (.+?) · \*\*Total time:\*\* (.+?) · \*\*Serves:\*\* (\d+)', t)
    if not m:
        problems.append(f"{n}: meta line malformed")
        continue
    cuisine, method, time_s, serves = m.groups()
    if serves != '4': problems.append(f"{n}: serves {serves}")
    mins = int(re.match(r'(\d+)', time_s).group(1))
    if mins > 20: problems.append(f"{n}: {mins} min > 20")
    # macros
    mm = re.search(r'\|\s*(\d+) kcal\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|', t)
    if not mm:
        problems.append(f"{n}: macro row not parsed")
    else:
        kcal,p,c,fat,fib = map(int, mm.groups())
        calc = 4*p+4*c+9*fat
        if abs(calc-kcal)/kcal > 0.12: problems.append(f"{n}: kcal {kcal} vs calc {calc}")
    tod = section(t, 'For the toddler')
    w = len(tod.split())
    if not (28 <= w <= 120): problems.append(f"{n}: toddler note {w} words")
    if re.search(r'\bhoney\b', section(t, 'Ingredients').lower()) and 'honey' not in tod.lower():
        problems.append(f"{n}: honey in recipe but not in the toddler note")
    low = t.lower()
    for b in BANNED:
        if b in low: problems.append(f"{n}: banned word '{b}'")
    if '!' in t: problems.append(f"{n}: contains exclamation mark")
    # method steps
    steps = re.findall(r'^\d+\. ', t.split('## Method')[1].split('## ')[0], re.M)
    if not (3 <= len(steps) <= 7): problems.append(f"{n}: {len(steps)} method steps")
    for note in ['**Swap:**','**Make it faster:**','**On the side:**','**Leftovers:**']:
        if note not in t: problems.append(f"{n}: missing {note}")
    rows.append((os.path.basename(f).split('-', 1)[0], h1[0], cuisine, method, mins))

titles=[r[1] for r in rows]
dupes=[x for x in titles if titles.count(x)>1]
if dupes: problems.append(f"duplicate titles: {set(dupes)}")
print("\nPROBLEMS:" if problems else "\nNo problems found.")
for p in problems: print("  -", p)
print(f"\nMethods: ")
from collections import Counter
print(" ", Counter(r[3] for r in rows))
print(f"Cuisines ({len(set(r[2] for r in rows))} distinct):")
for c,k in sorted(Counter(r[2] for r in rows).items()): print(f"   {c}: {k}")
print("\nTime spread:", Counter(r[4] for r in rows))
