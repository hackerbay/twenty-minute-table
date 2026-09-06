"""What is in a recipe, for somebody deciding what they will eat this week.

The planner lets people say what may appear on the table — vegetarian, chicken,
red meat, fish, shellfish — and it has to answer that question the way a person
with a real reason to ask would answer it. So the tags here are strict rather
than tactful: a chicken stir-fry seasoned with fish sauce carries both `chicken`
and `fish`, and untick either one and it goes. Anchovies melted into oil until
they have disappeared still count. The planner says so on the page, because a
filter that quietly lets something through is worse than no filter.

`main` is a different question — which protein the dish is *about* — and it is
decided by weight, so the 700 g of chicken mince outranks the tablespoon of fish
sauce. That one is used for variety, not for exclusion.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from parse import load_all  # noqa: E402
import grocery as G  # noqa: E402

# The five things a person ticks. Order is the order they appear on the page.
TAGS = ['veg', 'chicken', 'redmeat', 'fish', 'shellfish']

TAG_LABEL = {
    'veg':       'Vegetarian',
    'chicken':   'Chicken & turkey',
    'redmeat':   'Beef, pork & lamb',
    'fish':      'Fish',
    'shellfish': 'Prawns & squid',
}

# Matched against ingredient names, whole words only. Everything that puts an
# animal in a dish has to be here, including the ones that hide.
FLESH = [
    ('chicken', ('chicken', 'turkey', 'poussin', 'duck')),
    # `steak` is deliberately absent: recipe 10 is turkey breast steaks, and
    # every red meat in this book names its animal — beef sirloin, pork loin —
    # so the bare word bought nothing and mis-tagged a turkey dinner as beef.
    ('redmeat', ('beef', 'sirloin', 'rump', 'pork', 'lamb', 'bacon',
                 'chorizo', 'pancetta', 'prosciutto', 'sausage', 'ham', 'lard',
                 'guanciale', 'salami', 'mince')),
    ('fish', ('salmon', 'cod', 'sea bass', 'seabass', 'haddock', 'pollock',
              'hake', 'monkfish', 'mackerel', 'sardine', 'anchovy', 'anchovies',
              'tuna', 'trout', 'herring', 'white fish', 'fish sauce', 'nam pla',
              'bonito', 'katsuobushi', 'dashi', 'worcestershire', 'shrimp paste',
              'belacan', 'oyster sauce', 'fish fillet')),
    ('shellfish', ('prawn', 'prawns', 'shrimp', 'squid', 'calamari', 'mussel',
                   'mussels', 'clam', 'clams', 'crab', 'lobster', 'scallop',
                   'scallops', 'oyster')),
]

# `mince` names an animal only sometimes. Chicken stock needs no entry here:
# `chicken` matches it on its own, which is the right answer.
QUALIFIED = {
    'mince': ('beef', 'pork', 'lamb'),
}

EGG = ('egg', 'eggs', 'mayonnaise', 'mayo')
DAIRY = ('milk', 'yoghurt', 'yogurt', 'skyr', 'butter', 'ghee', 'cream',
         'feta', 'halloumi', 'paneer', 'ricotta', 'parmesan', 'pecorino',
         'cheddar', 'cheese', 'mascarpone', 'gruyère', 'gruyere', 'peynir',
         'crème fraîche', 'creme fraiche', 'buttermilk', 'niter kibbeh')
# `groundnut` is here because groundnut oil is peanut oil. Refined groundnut
# oil is usually tolerated, but a flag named `nuts` that does not know what a
# groundnut is would be wrong in the direction that matters.
NUTS = ('almond', 'almonds', 'walnut', 'walnuts', 'pistachio', 'pistachios',
        'cashew', 'cashews', 'peanut', 'peanuts', 'pecan', 'pecans',
        'hazelnut', 'hazelnuts', 'pine nut', 'pine nuts', 'macadamia',
        'brazil nut', 'nut butter', 'almond butter', 'peanut butter',
        'groundnut')
HONEY = ('honey',)

# What the protein actually is, for variety rather than for exclusion. A week
# of chicken thighs and chicken breasts is a week of chicken.
SOURCES = [
    ('chicken', ('chicken', 'turkey', 'duck')),
    ('beef', ('beef', 'sirloin', 'rump')),
    ('pork', ('pork', 'bacon', 'chorizo', 'pancetta', 'ham')),
    ('lamb', ('lamb',)),
    ('salmon', ('salmon',)),
    ('white fish', ('cod', 'sea bass', 'seabass', 'haddock', 'pollock', 'hake',
                    'monkfish', 'white fish')),
    # Anchovy is not here on purpose. It is a seasoning in this book — melted
    # into oil until it has gone — and calling `Broccoli Aglio e Olio` a fish
    # dinner would misdescribe the week. It still counts under FLESH, so a
    # ticked-off fish filter still removes it.
    ('oily fish', ('mackerel', 'sardine', 'herring', 'tuna')),
    ('prawns', ('prawn', 'prawns', 'shrimp', 'squid', 'calamari', 'mussel',
                'clam', 'crab', 'scallop')),
    ('eggs', ('egg', 'eggs')),
    ('cheese', ('feta', 'halloumi', 'paneer', 'ricotta', 'parmesan', 'pecorino',
                'cheddar', 'peynir', 'gruyère', 'gruyere')),
    ('yoghurt', ('yoghurt', 'yogurt', 'skyr')),
    ('tofu', ('tofu', 'tempeh', 'edamame', 'soya')),
    ('pulses', ('chickpeas', 'lentils', 'black beans', 'cannellini', 'butter beans',
                'kidney beans', 'white beans', 'fava', 'beans')),
    ('nuts & seeds', ('almond', 'walnut', 'pistachio', 'cashew', 'peanut',
                      'hazelnut', 'tahini', 'sesame')),
]

SOURCE_LABEL = {
    'chicken': 'Chicken', 'beef': 'Beef', 'pork': 'Pork', 'lamb': 'Lamb',
    'salmon': 'Salmon', 'white fish': 'White fish', 'oily fish': 'Oily fish',
    'prawns': 'Prawns', 'eggs': 'Eggs', 'cheese': 'Cheese', 'yoghurt': 'Yoghurt',
    'tofu': 'Tofu', 'pulses': 'Pulses', 'nuts & seeds': 'Nuts & seeds',
    'grains': 'Grains',
}


def _has(text, word):
    return re.search(r'(?<![a-z])' + re.escape(word) + r'e?s?(?![a-z])', text) is not None


def _qualified(text, word):
    """`mince` is only meat when something says which animal it came from."""
    if word not in QUALIFIED:
        return True
    return any(_has(text, q) for q in QUALIFIED[word])


def _blob(entries):
    return '\n'.join(e['n'].lower() for e in entries)


def tags_for(recipe, entries):
    """The flesh a recipe contains, strictly read. Vegetarian is the absence."""
    text = _blob(entries)
    found = set()
    for tag, words in FLESH:
        for w in words:
            if _has(text, w) and _qualified(text, w):
                found.add(tag)
                break
    return sorted(found) if found else ['veg']


def _weight(entry):
    """Roughly how much of a thing there is, in grams, for ranking proteins."""
    q, u = entry['q'], entry['u']
    if q is None:
        return 0.0
    if u == 'g':
        return q
    if u == 'kg':
        return q * 1000
    if u in ('ml', 'l', 'litre', 'litres'):
        return q * (1000 if u != 'ml' else 1)
    if u in ('tbsp', 'tsp'):
        return q * (15 if u == 'tbsp' else 5)
    if u in ('tin', 'pouch', 'pack', 'jar'):
        return q * 400
    return q * 120           # a fillet, a breast, an egg: a portion-ish weight


# Meat, fish and shellfish name a dish even when something else outweighs
# them: `Gambas al Ajillo with Chickpeas` is a prawn dish carrying 800 g of
# chickpeas, and calling it a pulse dinner would be a strange thing to tell
# somebody planning a week.
FLESH_SOURCES = ('chicken', 'beef', 'pork', 'lamb', 'salmon', 'white fish',
                 'oily fish', 'prawns')


def main_protein(recipe, entries):
    """Which protein the dish is about: flesh first, then by weight."""
    best, best_rank = None, (-1, -1.0)
    for e in entries:
        name = e['n'].lower()
        for source, words in SOURCES:
            if any(_has(name, w) and _qualified(name, w) for w in words):
                rank = (1 if source in FLESH_SOURCES else 0, _weight(e))
                if rank > best_rank:
                    best, best_rank = source, rank
                break
    return best or 'grains'


def flags_for(entries):
    text = _blob(entries)
    return {
        'egg': any(_has(text, w) for w in EGG),
        'dairy': any(_has(text, w) for w in DAIRY),
        'nuts': any(_has(text, w) for w in NUTS),
        'honey': any(_has(text, w) for w in HONEY),
    }


def profile(recipe):
    """Everything the planner needs to know about what is in one recipe."""
    entries = G.entries_for(recipe)
    tags = tags_for(recipe, entries)
    flags = flags_for(entries)
    veg = tags == ['veg']
    return {
        'tags': tags,
        'source': main_protein(recipe, entries),
        'vegan': veg and not (flags['egg'] or flags['dairy'] or flags['honey']),
        'nuts': flags['nuts'],
        'egg': flags['egg'],
        'dairy': flags['dairy'],
    }


if __name__ == '__main__':
    recipes = load_all()
    disagree = []
    from collections import Counter
    tagc, srcc = Counter(), Counter()
    for r in recipes:
        p = profile(r)
        tagc[','.join(p['tags'])] += 1
        srcc[p['source']] += 1
        marked = r['veg']
        derived = p['tags'] == ['veg']
        if marked != derived:
            disagree.append((r['num'], r['title'], marked, p['tags']))
        if int(r['num']) <= 50:
            print(f"{r['num']} {r['title'][:38]:38} {','.join(p['tags']):22}"
                  f" {p['source']:12} {'vegan' if p['vegan'] else '':6}"
                  f" {'nuts' if p['nuts'] else ''}")
    print('\ntags:', dict(tagc))
    print('sources:', dict(srcc))
    print(f'\n{len(disagree)} recipes where the file marker and the ingredients disagree:')
    for num, title, marked, tags in disagree:
        print(f'   {num} {title}: marker vegetarian={marked}, derived tags={tags}')
