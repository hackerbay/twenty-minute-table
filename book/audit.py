"""A deeper pass than verify.py: checks the content, not just the shape.

verify.py guarantees every file has the right sections and that the macro
arithmetic closes. This one goes after the things that are actually wrong in
cookbooks: metric-to-imperial conversions that drifted, ingredients listed but
never used, steps that call for something the list does not have, meat without
a doneness cue, and timings that do not add up.
"""
import re, sys, glob, os
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse import load_all

FRAC = {'½': .5, '¼': .25, '¾': .75, '⅓': 1/3, '⅔': 2/3, '⅛': .125, '⅜': .375, '⅝': .625, '⅞': .875}


def num(s):
    """Parse '1½', '2.5', '¾' into a float."""
    s = s.strip()
    if not s:
        return None
    total, digits = 0.0, ''
    for ch in s:
        if ch in FRAC:
            total += FRAC[ch]
        elif ch.isdigit() or ch == '.':
            digits += ch
        elif ch in ' -–':
            continue
        else:
            return None
    if digits:
        try:
            total += float(digits)
        except ValueError:
            return None
    return total or None


NUMRE = r'([\d.]*[½¼¾⅓⅔⅛⅜⅝⅞]?[\d.]*)'
CONV = [
    (rf'{NUMRE}\s*g\s*\(\s*{NUMRE}\s*oz\)',        lambda g: g / 28.3495,  'g→oz',   .13),
    (rf'{NUMRE}\s*g\s*\(\s*{NUMRE}\s*lb\s*{NUMRE}\s*oz', None,             'g→lb+oz',.12),
    (rf'{NUMRE}\s*g\s*\(\s*{NUMRE}\s*lb\s*\)',   lambda g: g / 453.592,  'g→lb',   .13),
    (rf'{NUMRE}\s*kg\s*\(\s*{NUMRE}\s*lb',         lambda k: k * 2.20462,  'kg→lb',  .10),
    (rf'{NUMRE}\s*ml\s*\(\s*{NUMRE}\s*cup',        lambda m: m / 236.588,  'ml→cup', .14),
    (rf'{NUMRE}\s*ml\s*\(\s*{NUMRE}\s*fl oz',      lambda m: m / 29.5735,  'ml→floz',.13),
    (rf'{NUMRE}\s*cm\s*\(\s*{NUMRE}\s*in\)',       lambda c: c / 2.54,     'cm→in',  .34),
    (rf'{NUMRE}\s*°C\s*\(\s*{NUMRE}\s*°F\)',       lambda c: c * 9 / 5 + 32,'°C→°F', .03),
]

STOP = set("""a an and or of the with to for in into on at from plus about roughly finely
thinly small large medium good fresh dried ground whole halved quartered sliced chopped
diced grated crushed torn cut trimmed peeled deseeded drained rinsed rough tsp tbsp g kg ml
l cup cups oz lb pinch handful bunch tin tins jar packed level heaped free range
sea fine flaky extra virgin best quality""".split())

MEAT = r'\bchicken\b|\bpork\b|\bturkey\b|\bbeef\b|\blamb\b|\bmince\b|\bprawns?\b|\bsalmon\b|\bcod\b|\bfish\b'

# Recipes where the doneness check fires on something that is never cooked.
# Reviewed by hand; each entry records why the finding does not apply.
NO_DONENESS_NEEDED = {
    '40': 'the only trigger is fish sauce; nothing here is meat or fish',
    '46': 'no-cook bowl, and the trigger is fish sauce in the nuoc cham',
    '48': 'sashimi-grade salmon, marinated raw and never heated',
    '49': 'built on ready-cooked cold prawns steeped in lime; nothing is cooked',
}
DONE = (r'cooked through|cooked all the way|no pink|not pink|opaque|flakes?\b|firm to the touch'
        r'|juices run clear|165|74|75|springs back|white all the way|until it is done'
        r'|core temperature|probe|until just set|curled|turned pink|pink through|browned through'
        r'|no longer (pink|translucent)|until the .{0,24}is cooked|cooked in the middle'
        r'|comes away|resists|firm and')


def head_words(line):
    """The content words of an ingredient line, before any parenthesis or comma."""
    s = line.split('(')[0].split(',')[0].lower()
    s = re.sub(r'[^a-z\s-]', ' ', s)
    return [w for w in s.split() if w not in STOP and len(w) > 2]


def main():
    rs = load_all()
    problems = defaultdict(list)

    for r in rs:
        n = r['num']
        text = ' '.join(r['steps'])
        low = text.lower()
        ing_lines = [i for g in r['ing_groups'] for i in g['items']]
        all_ing = ' '.join(ing_lines).lower()

        # --- 1. unit conversions -------------------------------------------
        for line in ing_lines + r['steps']:
            for pat, fn, label, tol in CONV:
                for m in re.finditer(pat, line):
                    a, b = num(m.group(1)), num(m.group(2))
                    if a is None or b is None or a == 0:
                        continue
                    if fn is None:                       # "700 g (1 lb 9 oz)"
                        oz = num(m.group(3))
                        if oz is None:
                            continue
                        b, want = b * 16 + oz, a / 28.3495
                    else:
                        want = fn(a)
                    if want and abs(want - b) / want > tol:
                        problems[n].append(
                            f'conversion {label}: "{m.group(0).strip()}" — {a:g} is {want:.2f}, not {b:g}')

        # --- 2. ingredients listed but never used --------------------------
        # A method may refer to a whole sub-group ("stir every rub ingredient
        # together", "add the spices"), which counts as using its members.
        COLLECTIVE = (r'\bthe (rub|spice|spices|marinade|paste|dressing|glaze|sauce|batter|'
                      r'seasoning|dry ingredients|remaining|rest)\b|everything|all the|both soys')
        collective = bool(re.search(COLLECTIVE, low))
        SPICE = (r'cumin|paprika|coriander|turmeric|cinnamon|nutmeg|allspice|clove|cardamom|'
                 r'oregano|thyme|sumac|za.atar|ras el|garam|berbere|five.spice|cayenne|fennel seed|'
                 r'mustard seed|peppercorn|chilli flakes|chilli powder|bay')
        for line in ing_lines:
            words = head_words(line)
            if not words:
                continue
            if any(w.rstrip('s') in low or w in low for w in words):
                continue
            if collective and re.search(SPICE, line.lower()):
                continue                       # folded into "the spices" / "the rub"
            problems[n].append(f'listed but not used in the method: "{line[:56]}"')

        # --- 3. doneness cue for meat and fish ------------------------------
        if (re.search(MEAT, all_ing) and not re.search(DONE, low)
                and n not in NO_DONENESS_NEEDED):
            problems[n].append('meat or fish with no doneness cue in the method')

        # --- 4. the stated split must equal the total -----------------------
        if r['prep']:
            if int(r['prep']) + int(r['cook']) != r['minutes']:
                problems[n].append(
                    f"time split {r['prep']}+{r['cook']} does not equal {r['minutes']}")

        # --- 5. plausible portions by section --------------------------------
        kcal = int(r['macros'][0]); pro = int(r['macros'][1]); fib = int(r['macros'][4])
        i = int(n)
        if i <= 50 and not (560 <= kcal <= 820):
            problems[n].append(f'main course at {kcal} kcal, outside 560-820')
        if i <= 50 and pro < 28:
            problems[n].append(f'main course with only {pro} g protein')
        if 70 < i <= 85 and kcal > 330:
            problems[n].append(f'pudding at {kcal} kcal, over 330')
        if i > 85 and kcal > 250:
            problems[n].append(f'side at {kcal} kcal, over 250')
        if fib < 1:
            problems[n].append(f'fibre of {fib} g looks low')

    # --- 6. duplicated prose across the book -------------------------------
    hooks = Counter(r['hook'] for r in rs)
    for h, c in hooks.items():
        if c > 1:
            problems['book'].append(f'hook used {c} times: "{h[:60]}"')
    sents = Counter()
    for r in rs:
        for s in re.split(r'(?<=[.!?])\s+', r['why'] + ' ' + ' '.join(r['steps'])):
            s = s.strip()
            if len(s) > 60:
                sents[s] += 1
    for s, c in sents.items():
        if c > 1:
            problems['book'].append(f'sentence repeated {c}x: "{s[:70]}"')

    titles = Counter(r['title'].lower() for r in rs)
    for t, c in titles.items():
        if c > 1:
            problems['book'].append(f'duplicate title: {t}')

    total = sum(len(v) for v in problems.values())
    print(f'{len(rs)} recipes audited — {total} findings\n')
    for n in sorted(problems, key=lambda x: (x == 'book', x)):
        print(f'  {n}:')
        for p in problems[n]:
            print(f'      {p}')
    return total


if __name__ == '__main__':
    sys.exit(0 if main() == 0 else 1)
