"""Turn ingredient lines into entries a shopping list can add up.

The recipe files are written for a cook standing at a hob, so an ingredient line
carries the amount, the form it is bought in, and what to do to it before it goes
in the pan: `3 x 400 g (14 oz) tins chickpeas, drained and patted dry`. A shopping
list wants only the first two of those, aggregated across a week of dinners and
sorted the way a shop is laid out.

This module does that split. It parses one line into one or more entries of
`quantity, unit, item`, tags each item with the aisle it lives in and whether the
fast pantry already holds it, and hands the result to `site.py`, which embeds it
in the meal planner. Scaling for a different number of servings and adding the
entries up happens in the browser, from this data.

Nothing here throws away a line it cannot read. Anything the grammar does not
recognise keeps its original text and lands on the list verbatim, because a
shopping list that quietly drops an ingredient is worse than an untidy one.
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from parse import load_all  # noqa: E402

# ------------------------------------------------------------------ numbers

VULGAR = {'¼': .25, '½': .5, '¾': .75, '⅓': 1 / 3, '⅔': 2 / 3,
          '⅛': .125, '⅜': .375, '⅝': .625, '⅞': .875}
VF = ''.join(VULGAR)

NUM = r'(?:\d+(?:\.\d+)?[' + VF + r']?|[' + VF + r'])'


def number(s):
    """`2`, `1.5`, `½` and `1½` all become a float."""
    s = s.strip()
    if not s:
        return None
    frac = 0.0
    if s and s[-1] in VULGAR:
        frac = VULGAR[s[-1]]
        s = s[:-1]
    if not s:
        return frac
    try:
        return float(s) + frac
    except ValueError:
        return None


# -------------------------------------------------------------------- units
# Every unit that appears in the book, mapped to the family it adds up in and
# how much of that family's base unit it is worth. Families never mix: six
# tablespoons of oil and 100 ml of oil stay two lines on the list, because
# turning one into the other implies a precision the recipes do not have.

UNITS = {
    'g': ('mass', 1), 'kg': ('mass', 1000),
    'ml': ('vol', 1), 'l': ('vol', 1000), 'litre': ('vol', 1000), 'litres': ('vol', 1000),
    'tsp': ('spoon', 1), 'tbsp': ('spoon', 3),
    'cm': ('cm', 1),
}

# Nouns that describe how a thing is sold rather than how much of it there is.
# `2 x 400 g tins chopped tomatoes` is two tins, and two tins is what you buy.
PACKS = ('tins', 'tin', 'pouches', 'pouch', 'packs', 'pack', 'jars', 'jar',
         'blocks', 'block', 'bunches', 'bunch', 'sheets', 'sheet', 'heads',
         'head', 'punnets', 'punnet', 'tubs', 'tub', 'balls', 'ball',
         'sprigs', 'sprig', 'slices', 'slice')

# Amounts the book gives by feel. They do not add up, so they are carried
# through to the list as words and never summed into a number.
VAGUE = ('pinch', 'handful', 'few sprigs', 'sprig', 'sprigs', 'scrape',
         'splash', 'drizzle', 'squeeze', 'little')

# Words in front of a noun that describe the specimen, not the shopping item.
# `1 large ripe avocado` and `2 avocados` belong on the same line of the list.
# `baby` is not here: baby corn is a different vegetable from corn, and a
# shopping list that drops the word sends somebody home with the wrong tin.
ADJ = ('large', 'small', 'medium', 'big', 'little', 'ripe', 'fat', 'thick',
       'thin', 'long', 'short', 'very', 'good', 'fresh', 'whole',
       'firm', 'soft', 'lean', 'plump', 'generous', 'level', 'heaped')

PLURALS = [('ies', 'y'), ('oes', 'o'), ('ves', 'f'), ('shes', 'sh'),
           ('ches', 'ch'), ('s', '')]

# The words the rules above would mangle. `cloves` is not a clof.
IRREGULAR = {'chillies': 'chilli', 'chilies': 'chilli', 'cloves': 'clove',
             'chives': 'chive', 'leaves': 'leaf', 'loaves': 'loaf',
             'halves': 'half', 'knives': 'knife', 'wolves': 'wolf'}

# Nouns that end in s in the singular, or that are never counted one at a time.
# `chickpeas` must not become `chickpea`, or the same tin lands on the list twice.
NEVER_SINGULAR = (
    'chickpeas', 'peas', 'beans', 'lentils', 'oats', 'greens', 'noodles', 'grains',
    'flakes', 'seeds', 'leaves', 'herbs', 'sprouts', 'crisps', 'olives', 'capers',
    'anchovies', 'sardines', 'prawns', 'nuts', 'almonds', 'cashews', 'walnuts',
    'pistachios', 'peanuts', 'pecans', 'hazelnuts', 'raisins', 'sultanas', 'dates',
    'breadcrumbs', 'cornflakes', 'couscous', 'hummus', 'asparagus', 'watercress',
    'molasses', 'gyoza', 'edamame', 'crackers', 'shallots', 'strawberries',
    'raspberries', 'blueberries', 'blackberries', 'berries', 'cherries', 'grapes',
    'sprigs', 'fronds', 'pods', 'wedges', 'strips', 'ribbons', 'florets',
)


def singular(word):
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word in NEVER_SINGULAR or len(word) < 4 or word.endswith('ss'):
        return word
    for suffix, repl in PLURALS:
        if word.endswith(suffix):
            return word[:-len(suffix)] + repl
    return word


# ------------------------------------------------------------------- aisles
# The order is the order of the printed list, which is roughly the order of a
# shop: the perishable edge first, the middle aisles after, the cupboard last.

AISLE_ORDER = ['produce', 'meat', 'fish', 'dairy', 'bakery', 'frozen',
               'tins', 'dry', 'nuts', 'sauces', 'oils', 'spice', 'other']

AISLE_LABEL = {
    'produce': 'Fruit & vegetables',
    'meat':    'Meat & poultry',
    'fish':    'Fish & seafood',
    'dairy':   'Dairy & eggs',
    'bakery':  'Bread',
    'frozen':  'Freezer',
    'tins':    'Tins & jars',
    'dry':     'Rice, grains & pasta',
    'nuts':    'Nuts, seeds & dried fruit',
    'sauces':  'Pastes, sauces & bottles',
    'oils':    'Oils & vinegars',
    'spice':   'Spices & dried herbs',
    'other':   'Anything else',
}

# Matched longest phrase first, so `coconut milk` beats `coconut` and
# `spring onion` beats `onion`. Word-boundary matched, not substring: `lime`
# must not fire on `lime pickle`'s neighbour `slime` and `oat` must not fire
# on `goat`.
AISLE_RULES = [
    ('fish', (
        'salmon', 'cod', 'sea bass', 'seabass', 'haddock', 'pollock', 'hake',
        'mackerel', 'sardine', 'sardines', 'anchovy', 'anchovies', 'tuna',
        'prawn', 'prawns', 'squid', 'calamari', 'mussel', 'mussels', 'crab',
        'scallop', 'scallops', 'white fish', 'fish fillet', 'fish fillets',
    )),
    ('meat', (
        'chicken thigh', 'chicken thighs', 'chicken breast', 'chicken breasts',
        'chicken mince', 'chicken', 'turkey', 'beef', 'steak', 'steaks', 'mince',
        'pork', 'lamb', 'bacon', 'chorizo', 'sausage', 'sausages', 'ham',
        'pancetta', 'prosciutto',
    )),
    ('dairy', (
        'egg', 'eggs', 'yoghurt', 'yogurt', 'skyr', 'milk', 'butter', 'cream',
        'creme fraiche', 'crème fraîche', 'feta', 'halloumi', 'paneer', 'ricotta',
        'mozzarella', 'parmesan', 'pecorino', 'cheddar', 'cheese', 'mascarpone',
        'cottage cheese', 'ghee', 'niter kibbeh', 'buttermilk', 'soured cream',
        'gruyère', 'gruyere', 'peynir', 'mature cheddar',
    )),
    ('bakery', (
        'bread', 'sourdough', 'flatbread', 'flatbreads', 'pitta', 'pita',
        'tortilla', 'tortillas', 'chapati', 'chapatis', 'naan', 'baguette',
        'rye bread', 'toast', 'bun', 'buns', 'roll', 'rolls', 'crumpet',
        'crumpets', 'muffin', 'muffins', 'tostada', 'tostadas',
    )),
    ('frozen', ('frozen peas', 'frozen edamame', 'frozen sweetcorn', 'edamame',
                'frozen soya beans', 'frozen berries', 'frozen mixed berries')),
    ('tins', (
        'tin', 'tins', 'tinned', 'chickpeas', 'black beans', 'cannellini',
        'butter beans', 'kidney beans', 'borlotti', 'white beans', 'beans',
        'lentils', 'chopped tomatoes', 'passata', 'tomato puree', 'tomato purée',
        'coconut milk', 'coconut cream', 'sweetcorn', 'olives', 'capers',
        'piquillo', 'roasted peppers', 'artichoke', 'artichokes', 'gherkins',
        'jalapenos', 'jalapeños', 'sun-dried tomatoes', 'kimchi', 'tostada',
        'crispy fried shallots', 'adobo',
    )),
    ('dry', (
        'rice', 'couscous', 'orzo', 'pasta', 'spaghetti', 'linguine', 'noodle',
        'noodles', 'oats', 'quinoa', 'bulgur', 'freekeh', 'polenta', 'flour',
        'cornflour', 'semolina', 'rava', 'buckwheat', 'sugar', 'gram flour',
        'split fava', 'fava beans', 'vermicelli', 'rice paper', 'nori', 'panko',
        'breadcrumbs', 'cornflakes', 'granola', 'cocoa', 'cacao', 'chocolate',
        'baking powder', 'bicarbonate', 'gelatine', 'cornstarch', 'penne',
        'rigatoni', 'gnocchi', 'tortellini', 'gim', 'seaweed', 'wonton',
        'rice cake', 'rice cakes', 'crispbread', 'jaggery', 'honeycomb',
        'espresso', 'coffee', 'ground coffee', 'tea',
    )),
    ('nuts', (
        'almond', 'almonds', 'walnut', 'walnuts', 'pistachio', 'pistachios',
        'cashew', 'cashews', 'peanut', 'peanuts', 'pecan', 'pecans', 'hazelnut',
        'hazelnuts', 'pine nut', 'pine nuts', 'sesame seed', 'sesame seeds',
        'pumpkin seed', 'pumpkin seeds', 'sunflower seed', 'sunflower seeds',
        'nigella', 'date', 'dates', 'raisin', 'raisins', 'sultana', 'sultanas',
        'dried apricot', 'coconut flakes', 'desiccated coconut',
        'peanut butter', 'almond butter', 'nuts', 'seeds', 'barberry',
        'barberries', 'sour cherries', 'cranberries', 'prunes', 'goji',
        'linseed', 'flaxseed', 'chia', 'grated coconut', 'coconut chips',
        # bare `coconut` last: `coconut milk`, `coconut oil` and `coconut
        # yoghurt` are all longer phrases and win on their own shelves.
        'coconut',
    )),
    ('sauces', (
        'soy sauce', 'soy', 'tamari', 'fish sauce', 'oyster sauce', 'hoisin',
        'miso', 'gochujang', 'harissa', 'sambal', 'sriracha',
        'chipotle in adobo', 'curry paste', 'mustard', 'ketchup', 'mayonnaise',
        'mayo', 'stock', 'stock cube', 'bouillon', 'honey', 'maple syrup',
        'mirin', 'shaoxing', 'sake', 'wine', 'pomegranate molasses', 'jam',
        'marmalade', 'vanilla extract', 'rosewater', 'rose water', 'orange blossom',
        'ginger-garlic paste', 'tomato ketchup', 'worcestershire', 'doubanjiang',
        'aji amarillo', 'aji amarillo paste', 'tamarind paste', 'horseradish',
        'horseradish sauce', 'chipotle in adobo', 'chipotle chillies in adobo',
        'tahini', 'light tahini',
        'ponzu', 'yuzu', 'pomegranate juice', 'coconut water',
        'rosewater', 'orange blossom water', 'vanilla paste',
    )),
    ('oils', (
        'olive oil', 'sesame oil', 'neutral oil', 'groundnut oil', 'rapeseed oil',
        'vegetable oil', 'sunflower oil', 'coconut oil', 'oil', 'vinegar',
        'red wine vinegar', 'rice vinegar', 'cider vinegar', 'balsamic',
    )),
    ('spice', (
        'salt', 'pepper', 'peppercorn', 'peppercorns', 'cumin', 'coriander seed',
        'ground coriander', 'turmeric', 'paprika', 'cinnamon', 'cardamom',
        'ground clove', 'nutmeg', 'allspice', 'saffron', 'sumac', 'za’atar',
        'zaatar', "za'atar", 'ras el hanout', 'garam masala', 'berbere',
        'five-spice', 'cajun', 'chilli flakes', 'chilli powder', 'chipotle powder',
        'curry powder', 'mustard seed', 'mustard seeds', 'fennel seed',
        'fennel seeds', 'caraway', 'oregano', 'thyme', 'bay leaf', 'bay leaves',
        'dried mint', 'dried herbs', 'furikake', 'shichimi', 'togarashi',
        'onion powder', 'garlic powder', 'garlic granules', 'garlic granule',
        'ginger, ground', 'ground ginger',
        'vanilla', 'star anise', 'sichuan pepper', 'white pepper', 'black pepper',
        'fenugreek', 'pul biber', 'aleppo pepper', 'cayenne', 'mixed spice',
        'nigella seeds', 'ajwain', 'asafoetida', 'kashmiri', 'gochugaru',
        'dried chillies', 'dried red chillies', 'curry powder', 'mace',
        'dried chipotle', 'dried ancho', 'ancho', 'anchos', 'guindilla',
        'dried guindilla', 'cumin seed', 'cumin seeds',
    )),
    ('produce', (
        'garlic clove', 'garlic cloves', 'onion', 'spring onion', 'spring onions', 'shallot', 'shallots', 'garlic',
        'ginger', 'chilli', 'chillies', 'chillis', 'pepper, red', 'red pepper',
        'green pepper', 'yellow pepper', 'romano pepper', 'tomato', 'tomatoes',
        'cucumber', 'courgette', 'aubergine', 'carrot', 'carrots', 'celery',
        'cauliflower', 'broccoli', 'tenderstem', 'broccolini', 'cabbage',
        'pak choi', 'bok choy', 'spinach', 'kale', 'chard', 'lettuce', 'rocket',
        'salad', 'leek', 'leeks', 'potato', 'potatoes', 'sweet potato',
        'mushroom', 'mushrooms', 'green beans', 'sugar snap', 'mangetout',
        'asparagus', 'fennel', 'radish', 'radishes', 'beetroot', 'corn on the cob',
        'sweetcorn cob', 'lemon', 'lemons', 'lime', 'limes', 'orange', 'oranges',
        'grapefruit', 'apple', 'apples', 'pear', 'pears', 'banana', 'bananas',
        'mango', 'pineapple', 'peach', 'peaches', 'nectarine', 'plum', 'plums',
        'fig', 'figs', 'pomegranate', 'avocado', 'avocados', 'grape', 'grapes',
        'berries', 'strawberries', 'raspberries', 'blueberries', 'blackberries',
        'coriander', 'parsley', 'mint', 'basil', 'dill', 'chive', 'chives',
        'lemongrass', 'makrut', 'kaffir', 'curry leaves', 'thai basil',
        'holy basil', 'watercress', 'sprouts', 'beansprouts', 'bean sprouts',
        'herb', 'herbs', 'fronds', 'zest', 'romano pepper', 'bell pepper',
        'bell peppers', 'gem lettuce', 'gem lettuces', 'cos lettuce', 'tofu',
        'tempeh', 'baby corn', 'corn', 'cob', 'cobs', 'sweetcorn kernels',
        'rosemary', 'sage', 'tarragon', 'oregano leaves', 'curry leaves',
        'cavolo nero', 'spring greens', 'collard greens', 'pak choy',
        'scotch bonnet', "bird's eye chilli", "bird's eye chillies",
        'padron pepper', 'padrón peppers', 'padron peppers', 'okra', 'squash',
        'butternut', 'parsnip', 'turnip', 'swede', 'celeriac', 'sprout',
        'coriander leaves', 'coriander stalks',
        'chipotle chilli', 'chipotle chillies', 'green bean', 'beansprout',
        'curry leaf', 'thyme leaf', 'thyme leaves', 'thyme sprig', 'fresh thyme',
        'nectarines', 'calamansi', 'passion fruit', 'melon', 'kiwi', 'papaya',
        'apricot', 'apricots', 'blackcurrant', 'blackcurrants',
        'cherry tomatoes', 'vine tomatoes', 'plum tomatoes', 'tomatoes on the vine',
    )),
]

# The pantry page lists what a stocked kitchen holds. Anything matching these is
# shown under "check the cupboard" rather than in the shopping aisles, because
# telling somebody to buy salt every week is how a list stops being read.
STAPLE_WORDS = (
    'salt', 'pepper', 'peppercorn', 'olive oil', 'neutral oil', 'sesame oil',
    'groundnut oil', 'rapeseed oil', 'vegetable oil', 'sunflower oil',
    'vinegar', 'soy sauce', 'soy', 'tamari', 'fish sauce', 'oyster sauce', 'stock',
    'mirin', 'honey', 'maple syrup', 'harissa', 'gochujang', 'miso', 'tahini',
    'sambal', 'curry paste', 'chipotle in adobo', 'stock', 'stock cube',
    'bouillon', 'cumin', 'coriander seed', 'ground coriander', 'turmeric',
    'paprika', 'cinnamon', 'cardamom', 'nutmeg', 'allspice', 'sumac', 'zaatar',
    'za’atar', "za'atar", 'ras el hanout', 'garam masala', 'berbere',
    'five-spice', 'cajun', 'chilli flakes', 'chilli powder', 'chipotle powder',
    'curry powder', 'mustard seed', 'fennel seed', 'caraway', 'oregano', 'thyme',
    'cayenne', 'fenugreek', 'mixed spice', 'pul biber', 'aleppo pepper',
    'kashmiri', 'dried chilli', 'dried red chilli', 'cardamom pod', 'cinnamon stick',
    'bay leaf', 'bay leaves', 'dried mint', 'saffron', 'star anise',
    'sichuan pepper', 'white pepper', 'black pepper', 'cornflour', 'sugar',
    'flour', 'baking powder', 'vanilla', 'ground cloves', 'ginger, ground',
    'ground ginger', 'nigella', 'gochugaru', 'furikake', 'shichimi', 'togarashi',
    'sesame seed', 'sesame seeds', 'cornstarch', 'water',
)


# Around eight hundred phrases are matched against every ingredient name, which
# is more distinct patterns than `re` keeps in its own cache — without this they
# were recompiled on every call and the site build took two minutes.
@lru_cache(maxsize=None)
def _pattern(phrase):
    return re.compile(r'(?<![a-z])' + re.escape(phrase) + r'e?s?(?![a-z])')


def _has(text, phrase):
    """Whole-phrase match, tolerating the plural. `oat` never fires on `goat`."""
    return _pattern(phrase).search(text) is not None


# A few things are named after something that lives in a different aisle.
# Chicken stock is not chicken, and a tin of anchovies in olive oil is not oil,
# so the head of the name decides before the longest match gets a say.
FIRST_CALL = (
    (re.compile(r'\bstock\b|\bbouillon\b'), 'sauces'),
    (re.compile(r'^frozen\b'), 'frozen'),
)


@lru_cache(maxsize=4096)
def aisle_for(name):
    """The aisle an item belongs to, by the longest phrase that matches it.

    Matched against the name as written and against its singular key, so a rule
    written as `red pepper` still finds `2 red peppers, sliced`.
    """
    low = name.lower()
    for pattern, aisle in FIRST_CALL:
        if pattern.search(low):
            return aisle
    # `tuna in olive oil` is tuna. What a thing is packed in never names it.
    head = re.split(r'\s+in\s+(?=olive oil|oil|brine|water|spring water|syrup)'
                    r'|\s+with\s+', low)[0]
    t = head + '\n' + _key(head)
    best, best_len = 'other', 0
    for key, words in AISLE_RULES:
        for w in words:
            if len(w) > best_len and _has(t, w):
                best, best_len = key, len(w)
    if best == 'other':
        t = low + '\n' + _key(name)
        for key, words in AISLE_RULES:
            for w in words:
                if len(w) > best_len and _has(t, w):
                    best, best_len = key, len(w)
    return best


# The cupboard aisles. Nothing fresh is ever a staple however it is named: a
# red pepper is not the black pepper in the spice tin, and sugar snap peas are
# not the sugar. Gating on the aisle first is what keeps those apart.
CUPBOARD = ('tins', 'dry', 'nuts', 'sauces', 'oils', 'spice')


@lru_cache(maxsize=4096)
def staple(name):
    if aisle_for(name) not in CUPBOARD:
        return False
    t = name.lower() + '\n' + _key(name)
    return any(_has(t, w) for w in STAPLE_WORDS)


# ------------------------------------------------------------------ parsing

# The imperial equivalent, and the weight given as a sanity check on a whole
# vegetable, ride along in brackets. They are for the cook, not the shopper.
BRACKET = re.compile(
    r'\s*\((?:~|about |approx\.? |scant |generous )?[^()]*?'
    r'(?:\boz\b|\blb\b|\bcups?\b|\bg\b|\bml\b|\bfl oz\b|\bin\b|\binch\b'
    # `75 ml (5 tbsp) olive oil` is metric-first with a spoon conversion. Left
    # in, the bracket becomes part of the product name and the list then reads
    # `olive oil (5 tbsp) — 9 tbsp`, two amounts for one bottle.
    r'|\btbsps?\b|\btsps?\b)[^()]*\)')

# A range is written for a cook deciding in the moment. A shopping list has to
# commit, and it commits upwards: nobody wants to be one chilli short.
RANGE = re.compile(r'(' + NUM + r')\s*[-–—]\s*(' + NUM + r')(?=\s|$)')

# What a note looks like when it starts. Every comma in these files is followed
# by one of these, and the few that are not — `boneless, skinless chicken
# thighs` — are caught by CONTINUES rather than by listing every exception.
PREP = frozenset([
    'finely', 'cut', 'sliced', 'halved', 'chopped', 'drained', 'roughly',
    'grated', 'rinsed', 'thinly', 'torn', 'coarsely', 'crushed', 'peeled',
    'deseeded', 'crumbled', 'shredded', 'diced', 'topped', 'stoned',
    'quartered', 'scrubbed', 'patted', 'toasted', 'split', 'podded', 'snipped',
    'broken', 'butterflied', 'trimmed', 'squashed', 'matchsticked', 'thickly',
    'beaten', 'skinned', 'juiced', 'unpeeled', 'cored', 'washed', 'lightly',
    'stirred', 'slivered', 'chilled', 'softened', 'stripped', 'removed',
    'separated', 'kept', 'reserved', 'smashed', 'bashed', 'pounded', 'rolled',
    'sifted', 'zested', 'pitted', 'whole', 'cold', 'warm', 'hot', 'plain',
])

# Words that carry on the name of the thing rather than starting a note about it.
CONTINUES = frozenset([
    'boneless', 'skinless', 'skin-on', 'bone-in', 'extra-firm', 'free-range',
    'organic', 'wild', 'unsalted',
])

# A note can name a second thing to buy — `1 tsp coconut oil, 1 tsp black
# mustard seeds, 8 curry leaves`. It is only read that way when it opens with a
# quantity and a word that is not a preparation, so `5 garlic cloves — 4 thinly
# sliced, 1 halved for the toast` stays a single entry for garlic.
NOTE_STOP = frozenset([
    'or', 'plus', 'about', 'more', 'each', 'per', 'from', 'to', 'in', 'for',
    'and', 'the', 'both', 'only', 'if', 'such', 'not', 'left', 'half', 'mixed',
    'stalks', 'leaves', 'tops', 'stems', 'sprigs', 'fronds', 'wedges',
])
NOTE_ITEM = re.compile(r'^(' + NUM + r')\s+([a-z][\w-]*)\b(.*)$', re.I)
NOTE_VAGUE = re.compile(r'^(?:and\s+)?an?\s+(handful|few|pinch)\s+of\s+(.+)$', re.I)

CITRUS = ('lemon', 'lime', 'orange', 'grapefruit', 'clementine', 'calamansi')

ZEST = re.compile(
    r'^(?:finely grated |coarsely grated |grated |pared |shredded )?'
    r'(zest and juice|juice and zest|zest|juice)\s+of\s+'
    r'(?:(' + NUM + r')|an?|half a|half)?\s*(.+)$', re.I)

VAGUE_OF = re.compile(
    r'^(?:an?\s+)?(?:good\s+|small\s+|large\s+|generous\s+|big\s+|few\s+)?'
    r'(' + '|'.join(VAGUE) + r')s?\s+of\s+(.+)$', re.I)

SEEDS_OF = re.compile(r'^seeds\s+of\s+(' + NUM + r')\s+(.+)$', re.I)

# `2 x 400 g tins chickpeas`: a count of packs, each of a stated size.
MULTI = re.compile(
    r'^(' + NUM + r')\s*[x×]\s*(' + NUM + r')\s*([a-z]+)\s+(' +
    '|'.join(PACKS) + r')\s+(.+)$', re.I)

# `400 g tin chickpeas`: one pack, its size given first.
SINGLE_PACK = re.compile(
    r'^(' + NUM + r')\s*(g|kg|ml|l)\s+(' + '|'.join(PACKS) + r')\s+(.+)$', re.I)

# `2 heads broccoli`, `4 sheets gim`: a count of packs of no stated size.
PACK_ONLY = re.compile(
    r'^(' + NUM + r')\s+(' + '|'.join(PACKS) + r')\s+(?:of\s+)?(.+)$', re.I)

UNIT_WORDS = '|'.join(sorted(list(UNITS) + list(PACKS), key=len, reverse=True))

QTY_UNIT = re.compile(r'^(' + NUM + r')\s*([a-zA-Z]+)\b\s*(.*)$')
QTY_ONLY = re.compile(r'^(' + NUM + r')\s+(.+)$')

# Where a line names two things — `Flaky sea salt and black pepper`, or `1 tsp
# ground cinnamon and ¼ tsp chipotle powder` — each half is a shopping item of
# its own. Splitting only where the right half opens a new quantity, or where
# the line never had one, leaves `toasted white and black sesame seeds` whole.
AND_QTY = re.compile(r'\s+and\s+(?=' + NUM + r'(?:\s|$))', re.I)
# `1 tsp rice vinegar and a pinch of salt` names two things whatever came
# before the `and`, because a pinch is never part of the thing before it.
AND_VAGUE = re.compile(
    r'\s+and\s+(?=(?:plenty\s+of\b|(?:an?\s+)?(?:' + '|'.join(VAGUE) + r')\b))', re.I)
AND_PLAIN = re.compile(
    r'\s+and\s+(?=(?:an?\s|plenty\s|a few\s|a little\s|good\s|plain\s|'
    r'black\s|white\s|flaky\s|fine\s|freshly\s|coarsely\s|ground\s|'
    r'dried\s|pinch\s|salt\b|pepper\b))', re.I)

# A colour on its own is the first of a list sharing one noun: `1 red, 1 green
# and 1 yellow pepper` is three peppers, not two colours and a pepper.
COLOURS = ('red', 'green', 'yellow', 'orange', 'white', 'black', 'purple')

COLOUR_LIST = re.compile(
    r'^((?:' + NUM + r'\s+(?:' + '|'.join(COLOURS) + r')\s*(?:,\s*|\s+and\s+))+)'
    r'(' + NUM + r')\s+(' + '|'.join(COLOURS) + r')\s+([a-z]+)\b', re.I)

# Lines that are not a purchase. Reserved fronds come off a bulb the list
# already carries, and no shop sells the water the couscous is steeped in.
NOT_SHOPPING = re.compile(
    r'^(?:any\s+)?(?:reserved|the reserved|leftover|remaining|saved)\b', re.I)
PLAIN_WATER = re.compile(r'^(?:[a-z-]+ )?water$')
SOLD_WATER = frozenset(['coconut water', 'rose water', 'rosewater',
                        'orange blossom water', 'sparkling water', 'tonic water'])
NOT_SOLD = frozenset(['ice', 'ice cube'])


def _not_sold(key):
    if key in NOT_SOLD:
        return True
    return bool(PLAIN_WATER.match(key)) and key not in SOLD_WATER


# A line that opens an ingredient list gets a capital in the recipe file —
# `Flaky sea salt and black pepper`. On a shopping list beside `fine sea salt`
# it reads as a different thing, so the capital comes off. Only these words:
# `Greek`, `Thai` and `Medjool` are capitals the shopping list should keep.
SENTENCE_START = frozenset([
    'salt', 'black', 'flaky', 'fine', 'coarse', 'coarsely', 'freshly', 'plenty',
    'pinch', 'juice', 'zest', 'warm', 'thick', 'cold', 'good', 'small', 'any',
    'a', 'seeds', 'pared', 'finely',
])


# A preparation that comes before the noun rather than after the comma:
# `finely grated fresh ginger` and `fresh ginger, grated` are one item on a
# shopping list, and keying them apart puts ginger on it twice.
LEADING_PREP = ('finely', 'coarsely', 'roughly', 'freshly', 'thinly', 'thickly',
                'grated', 'chopped', 'sliced', 'crushed', 'toasted', 'roasted',
                'shredded', 'ground', 'cooked', 'drained', 'rinsed', 'peeled',
                'unsalted', 'shelled', 'pared')


def _clean(name):
    """Strip the descriptors that belong to a specimen rather than a product."""
    n = name.strip().strip(',.;').strip()
    n = re.sub(r'^plenty\s+of\s+', '', n, flags=re.I)
    for _ in range(4):
        n = re.sub(r'^(?:' + '|'.join(ADJ + LEADING_PREP) + r')\s+', '', n, flags=re.I)
        # `ripe but firm bananas` loses `ripe` above and `but` here; `fresh or
        # frozen grated coconut` loses `fresh` and then the `or` it left behind.
        n = re.sub(r'^(?:but|or)\s+', '', n, flags=re.I)
    n = n.strip()
    first = n.split(' ', 1)[0].lower()
    if first in SENTENCE_START and n[:1].isupper():
        n = n[0].lower() + n[1:]
    return n


@lru_cache(maxsize=4096)
def _key(name):
    """The form two lines have to share to be added together."""
    k = _clean(name).lower()
    k = re.sub(r'\([^)]*\)', ' ', k)              # `cornflour (cornstarch)`
    # An `or` is kept whole. `groundnut or vegetable oil` is one thing to buy,
    # and cutting it at the `or` would file it under groundnut.
    k = re.sub(r'[^\w\s-]', ' ', k, flags=re.UNICODE)
    k = re.sub(r'\s+', ' ', k).strip()
    return ' '.join(singular(w) for w in k.split())


def _fmt_plain(x):
    if x is None:
        return ''
    return str(int(x)) if abs(x - round(x)) < 1e-6 else ('%g' % x)


def _entry(qty, unit, name, note, raw, pack=''):
    name = _clean(name)
    if not name or _not_sold(_key(name)):
        return None
    return {
        'q': round(qty, 4) if isinstance(qty, float) else qty,
        'u': unit,
        'pack': pack,
        'n': name,
        'k': _key(name),
        'a': aisle_for(name),
        's': staple(name),
        'note': note,
        'raw': raw,
    }


def _parse_one(text, note, raw):
    """One half of a line, already split from its note and from any `and`."""
    t = text.strip()
    if not t or NOT_SHOPPING.match(t):
        return None

    m = MULTI.match(t)
    if m:
        n, size, unit, pack, name = m.groups()
        return _entry(number(n), singular(pack.lower()), name, note, raw,
                      pack='%s %s' % (_fmt_plain(number(size)), unit))

    m = SEEDS_OF.match(t)
    if m:
        return _entry(number(m.group(1)), '', m.group(2), 'seeds only', raw)

    m = ZEST.match(t)
    if m:
        part, n, fruit = m.group(1).lower(), m.group(2), m.group(3)
        q = number(n) if n else (0.5 if re.search(r'\bhalf\b', t[:26], re.I) else 1)
        return _entry(q, '', fruit, part if not note else '%s, %s' % (part, note), raw)

    m = VAGUE_OF.match(t)
    if m:
        return _entry(None, m.group(1).lower(), m.group(2), note, raw)

    m = re.match(r'^an?\s+(?:little|few)\s+(.+)$', t, re.I)
    if m:
        return _entry(None, 'little', m.group(1), note, raw)

    m = SINGLE_PACK.match(t)
    if m:
        size, unit, pack, name = m.groups()
        return _entry(1, singular(pack.lower()), name, note, raw,
                      pack='%s %s' % (_fmt_plain(number(size)), unit))

    m = PACK_ONLY.match(t)
    if m:
        return _entry(number(m.group(1)), singular(m.group(2).lower()),
                      m.group(3), note, raw)

    m = QTY_UNIT.match(t)
    if m and m.group(2).lower() in UNITS:
        return _entry(number(m.group(1)), m.group(2).lower(), m.group(3), note, raw)

    m = QTY_ONLY.match(t)
    if m:
        return _entry(number(m.group(1)), '', m.group(2), note, raw)

    # No quantity at all: `Flaky sea salt`, `Black pepper`, `warm flatbread`.
    return _entry(None, '', t, note, raw)


def _head_wants_more(head):
    """True when a comma fell inside the name — `800 g boneless, skinless ...`."""
    rest = re.sub(r'^' + NUM + r'\s*(?:' + UNIT_WORDS + r')?\s*', '',
                  head.strip(), flags=re.I)
    words = [w.lower().strip('-') for w in rest.split()]
    return not words or all(w in CONTINUES or w in ADJ for w in words)


PLUS_MORE = re.compile(r'^plus\s+(' + NUM + r')\s+more\b', re.I)


def _extra_from_note(note, raw, head=None):
    """A second thing to buy, hiding in what looked like a note."""
    out = []
    for chunk in [c.strip() for c in note.split(',')]:
        if not chunk:
            continue
        # `plus 1 more cut into wedges` is more of the thing already named, so
        # it is added to that entry rather than becoming a line of its own.
        m = PLUS_MORE.match(chunk)
        if m and head is not None and head['u'] == '':
            head['q'] = (head['q'] or 0) + (number(m.group(1)) or 0)
            continue
        m = NOTE_VAGUE.match(chunk)
        if m:
            e = _entry(None, m.group(1).lower(), m.group(2), '', raw)
            if e:
                out.append(e)
            continue
        z = ZEST.match(chunk)
        if z:
            # `zest of both` refers back; `juice of ½ lemon` is a lemon to buy.
            if _key(z.group(3)) in [_key(c) for c in CITRUS]:
                e = _parse_one(chunk, '', raw)
                if e:
                    out.append(e)
            continue
        m = NOTE_ITEM.match(chunk)
        if m and m.group(2).lower() not in PREP and m.group(2).lower() not in NOTE_STOP:
            e = _parse_one(chunk, '', raw)
            if e:
                out.append(e)
    return out


def parse_line(raw):
    """One ingredient line to the shopping entries it implies."""
    line = re.sub(r'\*\*|\*', '', raw.strip())
    line = BRACKET.sub(' ', line)
    line = re.sub(r'\s+', ' ', line).strip()

    # A comma inside a bracket belongs to the bracket: `firm white fish (cod,
    # hake or monkfish)` is one fish to buy, not a fish and then a hake.
    holes = []

    def _stash(m):
        holes.append(m.group(0))
        return '\x00%d\x00' % (len(holes) - 1)

    def _unstash(s):
        return re.sub(r'\x00(\d+)\x00', lambda m: holes[int(m.group(1))], s)

    line = re.sub(r'\([^()]*\)', _stash, line)

    m = COLOUR_LIST.match(_unstash(line))
    if m:
        noun = m.group(4)
        out = [_entry(number(n), '', '%s %s' % (c, noun), '', raw)
               for n, c in re.findall(r'(' + NUM + r')\s+(' + '|'.join(COLOURS) + r')',
                                      m.group(1), re.I)]
        out.append(_entry(number(m.group(2)), '', '%s %s' % (m.group(3), noun), '', raw))
        return [e for e in out if e]

    # Split the name from its note, rejoining where the comma fell inside the
    # name rather than after it.
    parts = re.split(r'\s*(?:,|\s—\s|\s--\s)\s*', line)
    head, i = parts[0], 1
    while i < len(parts) and _head_wants_more(head):
        head = '%s, %s' % (head, parts[i])
        i += 1
    head, note = _unstash(head), _unstash(', '.join(parts[i:]).strip())
    head = RANGE.sub(r'\2', head)

    chunks = AND_QTY.split(head)
    if len(chunks) == 1:
        chunks = AND_VAGUE.split(head)
    if len(chunks) == 1 and not re.match(r'^' + NUM, head):
        chunks = AND_PLAIN.split(head)

    out, carried = [], note
    for chunk in chunks:
        e = _parse_one(chunk, carried, raw)
        if e:
            out.append(e)
        # The note belongs to the first name only. In `salt and black pepper, to
        # finish`, repeating it would read as two separate instructions.
        carried = ''

    # `1 red, 1 green and 1 yellow pepper`: the colours borrow the last noun.
    if len(out) > 1:
        tail = out[-1]['n'].split()
        for e in out[:-1]:
            if e['n'].lower() in COLOURS and len(tail) > 1:
                e['n'] = '%s %s' % (e['n'], ' '.join(tail[1:]))
                e['k'] = _key(e['n'])
                e['a'] = aisle_for(e['n'])
                e['s'] = staple(e['n'])

    out.extend(_extra_from_note(note, raw, out[0] if out else None))
    return out


# ------------------------------------------------------------------ the data

def entries_for(recipe):
    """Every shopping entry a recipe implies, in the order it lists them."""
    out = []
    for group in recipe['ing_groups']:
        for item in group['items']:
            out.extend(parse_line(item))
    return out


def payload(recipes):
    """The planner's data: one record per recipe, ready to be embedded as JSON."""
    return {r['num']: [
        {k: v for k, v in e.items() if k not in ('note',)}
        for e in entries_for(r)
    ] for r in recipes}


if __name__ == '__main__':
    recipes = load_all()
    total, unknown, other = 0, [], []
    for r in recipes:
        for group in r['ing_groups']:
            for item in group['items']:
                es = parse_line(item)
                total += 1
                if not es:
                    unknown.append((r['num'], item, 'dropped'))
                for e in es:
                    if e['a'] == 'other':
                        other.append((r['num'], item, e['n']))
    print(f'{total} ingredient lines parsed')
    print(f'{len(unknown)} dropped as not-shopping')
    for n, i, why in unknown:
        print(f'   {n}  {i}')
    print(f'\n{len(other)} entries with no aisle:')
    for n, i, name in other:
        print(f'   {n}  {name:38.38s} <- {i}')
