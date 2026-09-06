"""The data behind the meal planner, and the week the page ships with.

`site.py` embeds `payload()` in `plan.html` and the browser does the rest —
filtering, picking, adding the shopping list up and writing the PDF. Everything
that has to be derived from a recipe rather than read off it is derived here, in
Python, once, at build time: what protein a dish is built on, which region its
cuisine belongs to, and what each ingredient line means to somebody holding a
basket.

The page also arrives with a week already chosen. That is not a placeholder —
it is a real week, picked by `default_week()` below, so the page is a finished
thing before anyone touches a control, and so it still says something with
JavaScript turned off.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from parse import load_all, METHODS  # noqa: E402
import grocery as G  # noqa: E402
import diet as D  # noqa: E402

# Recipes 01-50 are the lunches and dinners. The planner picks from those and
# leaves breakfast, pudding and the sides where they are.
MAINS = 50

# Thirty-six cuisines over fifty dinners means a week of six distinct cuisines
# is nearly free, and says nothing. Grouped into regions it becomes a real
# measure of whether the week wanders.
# Order matters: the first list that matches wins. `Hawaiian-Japanese` is a
# poke bowl and belongs with the Americas, so the Americas are tested before
# East Asia would claim it for the `japanese` half of the name.
REGIONS = [
    ('The Americas', ('mexican', 'peruvian', 'brazilian', 'jamaican', 'american',
                      'louisiana', 'hawaiian', 'caribbean', 'cuban', 'argentin')),
    ('East Asia', ('chinese', 'japanese', 'korean', 'cantonese', 'sichuan')),
    ('South-East Asia', ('thai', 'vietnamese', 'filipino', 'indonesian',
                         'malaysian', 'burmese', 'singaporean', 'cambodian')),
    ('South Asia', ('indian', 'sri lankan', 'pakistani', 'nepali', 'bangladeshi')),
    ('Africa & North Africa', ('ethiopian', 'moroccan', 'tunisian', 'north african',
                               'ghanaian', 'senegalese', 'mozambican', 'nigerian',
                               'egyptian', 'south african')),
    ('Middle East & the Levant', ('turkish', 'lebanese', 'levantine', 'israeli',
                                  'middle eastern', 'persian', 'iranian', 'syrian',
                                  'georgian', 'armenian')),
    ('Europe', ('italian', 'greek', 'spanish', 'portuguese', 'french', 'danish',
                'sicilian', 'tuscan', 'british', 'german', 'swedish', 'polish')),
]

# The five families the concentration test uses. Two chicken nights and two
# turkey nights are four poultry nights, whatever the recipe titles say.
FAMILIES = {
    'chicken': 'poultry',
    'beef': 'red meat', 'pork': 'red meat', 'lamb': 'red meat',
    'salmon': 'seafood', 'white fish': 'seafood', 'oily fish': 'seafood',
    'prawns': 'seafood',
    'eggs': 'eggs & dairy', 'cheese': 'eggs & dairy', 'yoghurt': 'eggs & dairy',
    'tofu': 'plants', 'pulses': 'plants', 'nuts & seeds': 'plants',
    'grains': 'plants',
}


def region_for(cuisine):
    """Which part of the world a cuisine string belongs to."""
    low = cuisine.lower()
    # Portuguese-Mozambican is peri-peri, which is an African dish however the
    # name is ordered, so Africa is tested before Europe by list order above.
    for name, words in REGIONS:
        if any(w in low for w in words):
            return name
    return 'Elsewhere'


def slug(recipe):
    return re.sub(r'[^a-z0-9]+', '-', recipe['title'].lower()).strip('-')


def record(recipe):
    """One recipe, as the planner needs it. Short keys: this is embedded."""
    p = D.profile(recipe)
    m = recipe['m']
    macros = [int(x) for x in recipe['macros']]
    return {
        'n': recipe['num'],
        't': recipe['title'],
        's': slug(recipe),
        'c': recipe['cuisine'],
        'g': region_for(recipe['cuisine']),
        'm': m['key'],
        'ml': m['label'],
        'col': m['color'],
        'min': recipe['minutes'],
        'kc': macros[0], 'pr': macros[1], 'cb': macros[2],
        'fa': macros[3], 'fb': macros[4],
        'tg': p['tags'],
        'src': D.SOURCE_LABEL.get(p['source'], p['source']),
        'fam': FAMILIES.get(p['source'], 'plants'),
        'vg': 1 if p['vegan'] else 0,
        'nu': 1 if p['nuts'] else 0,
        'ing': [
            {'q': e['q'], 'u': e['u'], 'p': e['pack'], 'n': e['n'],
             'k': e['k'], 'a': e['a'], 's': 1 if e['s'] else 0}
            for e in G.entries_for(recipe)
        ],
    }


def default_week(records, n=5):
    """The week the page is built with, chosen the same way every time.

    Deliberately not random: the committed HTML has to be reproducible, or the
    build check that compares `site/` against what the sources generate would
    fail on every run. It walks the dinners in order and takes each one that
    brings a protein, a method and a region the week does not have yet,
    loosening the test each pass until it has enough.
    """
    week = []
    for wanted in (3, 2, 1, 0):
        for r in records:
            if len(week) >= n:
                break
            if r in week:
                continue
            fresh = ((r['fam'] not in [w['fam'] for w in week]) +
                     (r['m'] not in [w['m'] for w in week]) +
                     (r['g'] not in [w['g'] for w in week]))
            if fresh >= wanted:
                week.append(r)
        if len(week) >= n:
            break
    return [r['n'] for r in week[:n]]


def full(recipe):
    """A whole recipe, for the printable pack the planner can build.

    Kept out of `payload()` and written to its own asset: only somebody who
    asks for the recipes needs it, and it is twice the size of everything else
    on the page put together.
    """
    m = recipe['m']
    return {
        'n': recipe['num'],
        't': recipe['title'],
        'c': recipe['cuisine'],
        'ml': m['label'],
        'time': recipe['time'],
        'serves': recipe['serves'],
        'veg': 1 if recipe['veg'] else 0,
        'hook': recipe['hook'],
        'why': recipe['why'],
        'groups': [{'name': g['name'] or '', 'items': g['items']}
                   for g in recipe['ing_groups']],
        'steps': recipe['steps'],
        'notes': [[t, b] for t, b in recipe['notes']],
        'toddler': recipe['toddler'],
        'macros': recipe['macros'],
        'washing': recipe['washing'],
    }


def recipe_pack(recipes):
    """Every dinner in full, keyed by number, for the recipe asset."""
    return {r['num']: full(r) for r in recipes if int(r['num']) <= MAINS}


def payload(recipes):
    """Everything plan.html embeds, ready for json.dumps."""
    records = [record(r) for r in recipes if int(r['num']) <= MAINS]
    return {
        'recipes': records,
        'aisles': [[k, G.AISLE_LABEL[k]] for k in G.AISLE_ORDER],
        'week': default_week(records),
        'serves': int(recipes[0]['serves']) if recipes else 4,
    }


def tag_counts(records):
    """How many dinners carry each protein tag, for the filter chips."""
    return {t: sum(1 for r in records if t in r['tg']) for t in D.TAGS}


if __name__ == '__main__':
    import json
    recipes = load_all()
    data = payload(recipes)
    by = {r['n']: r for r in data['recipes']}
    pack = recipe_pack(recipes)
    print(f"recipe pack: {len(json.dumps(pack, separators=(',', ':')))/1000:.1f} kB")
    print(f"{len(data['recipes'])} dinners, "
          f"{sum(len(r['ing']) for r in data['recipes'])} ingredient entries, "
          f"{len(json.dumps(data, separators=(',', ':')))/1000:.1f} kB of JSON")
    print('\ntag counts:', tag_counts(data['recipes']))
    from collections import Counter
    print('regions:', dict(Counter(r['g'] for r in data['recipes'])))
    print('families:', dict(Counter(r['fam'] for r in data['recipes'])))
    print('\nthe week the page ships with:')
    for n in data['week']:
        r = by[n]
        print(f"   {r['n']} {r['t'][:40]:42} {r['ml']:10} {r['g']:26} "
              f"{r['src']:12} {r['min']} min")
    unknown = [r for r in data['recipes'] if r['g'] == 'Elsewhere']
    if unknown:
        print('\ncuisines with no region:', [(r['n'], r['c']) for r in unknown])
