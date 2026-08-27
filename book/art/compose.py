"""Turn a recipe's ingredient list into a flat-lay illustration.

Ingredient lines are matched against an ordered rule table to pick icon keys;
the icons are then scattered across the hero area with a seeded, deterministic
layout so the same recipe always produces the same picture.
"""
import math, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from food import PART as FOOD
from actions import PART as ACTIONS

# --- ingredient -> icon ------------------------------------------------------
# Ordered: the first pattern that matches a line wins, so put the specific
# multi-word cases above the generic single words they contain.
RULES = [
    (r'coconut milk|coconut cream', 'coconut-milk'),
    (r'desiccated coconut|coconut\b', 'coconut'),
    (r'cherry tomato|tomatoes on the vine|baby plum', 'cherry-tomatoes'),
    (r'tinned tomato|chopped tomato|passata|tin.*tomato', 'tinned-tomatoes'),
    (r'sun-dried tomato|tomato', 'tomato'),
    (r'spring onion|scallion', 'spring-onion'),
    (r'sweet potato', 'sweet-potato'),
    (r'sesame seed|sesame oil|sesame', 'sesame'),
    (r'anchov', 'anchovy'),
    (r'\bpork\b|pancetta|bacon', 'pork-loin'),
    (r'olive oil|extra virgin|rapeseed oil|groundnut oil|vegetable oil|neutral oil', 'olive-oil'),
    (r'\bolives?\b', 'olives'),
    (r'peanut butter|peanut', 'almond'),
    (r'chicken', 'chicken-thigh'),
    (r'prawn|shrimp', 'prawn'),
    (r'salmon', 'salmon-fillet'),
    (r'\bcod\b|sea bass|white fish|haddock|hake|mackerel|trout|tilapia|pollock', 'white-fish'),
    (r'turkey', 'turkey-breast'),
    (r'beef|steak|bavette|sirloin|rump|bulgogi', 'beef-strips'),
    (r'\beggs?\b', 'egg'),
    (r'tofu', 'tofu'),
    (r'paneer|halloumi', 'paneer'),
    (r'\bfeta\b', 'feta'),
    (r'yoghurt|yogurt|cottage cheese|labneh|kefir', 'yoghurt'),
    (r'\btuna\b', 'tuna-tin'),
    (r'cauliflower|romanesco', 'cauliflower'),
    (r'broccoli|tenderstem|broccolini', 'broccoli'),
    (r'\bonions?\b|shallot', 'onion'),
    (r'garlic', 'garlic'),
    (r'ginger|galangal', 'ginger'),
    (r'chilli|chili|chile|jalape|scotch bonnet|bird.s eye|cayenne', 'chilli'),
    (r'bell pepper|red pepper|green pepper|yellow pepper|romano pepper|piquillo|capsicum|peppers\b', 'bell-pepper'),
    (r'courgette|zucchini', 'courgette'),
    (r'aubergine|eggplant', 'aubergine'),
    (r'mushroom|shiitake', 'mushroom'),
    (r'spinach', 'spinach'),
    (r'kale|collard|gomen|chard|cavolo', 'kale'),
    (r'cabbage|sauerkraut', 'cabbage'),
    (r'pak choi|bok choy|choy sum', 'pak-choi'),
    (r'green bean|runner bean|french bean|long bean', 'green-beans'),
    (r'\bpeas?\b|edamame|mangetout|sugar snap', 'peas'),
    (r'sweetcorn|\bcorn\b', 'sweetcorn'),
    (r'carrot', 'carrot'),
    (r'cucumber', 'cucumber'),
    (r'avocado', 'avocado'),
    (r'radish', 'radish'),
    (r'fennel', 'fennel'),
    (r'\blemons?\b', 'lemon'),
    (r'\blimes?\b', 'lime-wedge'),
    (r'orange', 'orange'),
    (r'pineapple', 'pineapple'),
    (r'banana', 'banana'),
    (r'\bdates?\b', 'date'),
    (r'\bfigs?\b', 'fig'),
    (r'walnut', 'walnut'),
    (r'almond|cashew|pistachio|hazelnut|pine nut|\bnuts?\b', 'almond'),
    (r'chickpea|gram flour', 'chickpeas'),
    (r'black bean|black turtle', 'black-beans'),
    (r'cannellini|butter bean|white bean|haricot|borlotti|fava|\bful\b', 'white-beans'),
    (r'lentil', 'lentils'),
    (r'\brice\b|jasmine|basmati', 'rice-bowl'),
    (r'noodle|soba|vermicelli|rice paper|udon', 'noodles'),
    (r'\boats?\b|porridge|rolled oat', 'oats'),
    (r'couscous|\borzo\b|semolina|rava|bulgur|freekeh|quinoa', 'couscous'),
    (r'pitta|flatbread|tortilla|tostada|\bnaan\b|wrap', 'flatbread'),
    (r'bread|sourdough|\brye\b|\btoast\b|baguette|ciabatta', 'bread'),
    (r'\bnori\b|seaweed|furikake|\bwakame\b', 'nori'),
    (r'soy sauce|tamari|fish sauce|mirin|vinegar|worcester', 'soy-bottle'),
    (r'tahini', 'tahini'),
    (r'harissa|gochujang|\bmiso\b|curry paste|sambal|chipotle|berbere|adobo paste|doubanjiang|chermoula', 'paste-jar'),
    (r'honey|maple syrup|palm sugar|jaggery', 'honey'),
    (r'coriander leaf|fresh coriander|parsley|basil|\bmint\b|\bdill\b|herb|chives|tarragon|curry leaf', 'herbs'),
    (r'cumin|paprika|turmeric|garam|za.atar|sumac|spice|ras el hanout|five.spice|cinnamon|allspice'
     r'|cajun|oregano|thyme|coriander|cardamom|clove|nutmeg|fenugreek|mustard seed|peppercorn|salt', 'spice-jar'),
    (r'pumpkin seed|sunflower seed|\bseeds?\b', 'sesame'),
]
RULES = [(re.compile(p), k) for p, k in RULES]

FILLERS = ['spice-jar', 'olive-oil', 'herbs']

# Tier 0 icons are the ones a reader would call the dish; tier 2 is pantry
# background. Picks are sorted by tier so the largest icon is always the star.
STAR = {'chicken-thigh', 'prawn', 'salmon-fillet', 'white-fish', 'beef-strips', 'pork-loin',
        'turkey-breast', 'egg', 'tofu', 'paneer', 'tuna-tin'}
TIER1 = {'onion', 'spring-onion', 'garlic', 'ginger', 'chilli', 'lemon', 'lime-wedge',
         'herbs', 'honey', 'tahini', 'paste-jar', 'sesame'}
TIER2 = {'olive-oil', 'soy-bottle', 'spice-jar'}


def tier(key):
    return 2 if key in TIER2 else 1 if key in TIER1 else -1 if key in STAR else 0


def pick_icons(recipe, lo=5, hi=9):
    """Icon keys for a recipe: star ingredients first, pantry last."""
    found, seen = [], set()
    lines = [i for g in recipe['ing_groups'] for i in g['items']]
    for order, line in enumerate(lines):
        low = line.lower()
        for rx, key in RULES:
            if rx.search(low):
                if key not in seen:
                    seen.add(key)
                    found.append((tier(key), order, key))
                break
    for order, f in enumerate(FILLERS):
        if f not in seen:
            seen.add(f)
            found.append((tier(f), 900 + order, f))
    found.sort()
    keys = [k for _, _, k in found]
    return keys[:hi] if len(keys) >= lo else keys


# --- layout -----------------------------------------------------------------
VB_W, VB_H = 400, 205          # hero viewBox; ratio sits mid-range of the printed box
PAD = 46                       # generous, so `slice` cropping never bites


def _best_candidate(rng, placed, r, tries=110):
    """Mitchell's best-candidate sampling: the point furthest from what is placed."""
    best, best_d = None, -1
    for _ in range(tries):
        x = rng.uniform(PAD + r * .4, VB_W - PAD - r * .4)
        y = rng.uniform(PAD * .74 + r * .4, VB_H - PAD * .74 - r * .4)
        if not placed:
            return x, y
        d = min(math.hypot(x - px, y - py) - pr for px, py, pr in placed)
        if d > best_d:
            best_d, best = d, (x, y)
    return best


SIZES = [94, 76, 70, 62, 56, 52, 48, 44, 42, 40, 38]


def hero_svg(recipe, color, halo='#ffffff'):
    keys = pick_icons(recipe)
    rng = random.Random(int(recipe['num']) * 7919 + 31)
    n = len(keys)

    placed, nodes = [], []
    for i, key in enumerate(keys):
        size = SIZES[min(i, len(SIZES) - 1)] * rng.uniform(.94, 1.06)
        r = size * .5
        x, y = _best_candidate(rng, placed, r)
        placed.append((x, y, r * .92))
        nodes.append((key, x, y, size))

    haloes = ''
    for _, x, y, sz in nodes[:2]:
        rr = min(sz * .68, x - 4, y - 4, VB_W - x - 4, VB_H - y - 4)
        if rr > sz * .40:
            haloes += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="{halo}" opacity=".42"/>'

    specks = ''
    for _ in range(26):
        x = rng.uniform(10, VB_W - 10); y = rng.uniform(10, VB_H - 10)
        specks += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(.9,1.9):.1f}" '
                   f'fill="{color}" opacity=".2"/>')

    items = ''
    for i, (key, x, y, size) in enumerate(nodes):
        k = size / 48.0
        rot = rng.uniform(-16, 16)
        op = 1.0 if i < 3 else (.78 if i < 6 else .62)
        items += (f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.1f}) scale({k:.4f}) '
                  f'translate(-24 -24)" stroke-width="{2.05/k:.3f}" opacity="{op}">{FOOD[key]}</g>')

    return (f'<svg viewBox="0 0 {VB_W} {VB_H}" class="hero-svg" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round">'
            f'{haloes}{specks}{items}</svg>')


# --- method step -> action glyph --------------------------------------------
STEP_RULES = [
    (r'heat the air fryer|preheat|heat the oven|heat your air fryer|set the air fryer', 'preheat'),
    (r'air fry|air-fry|in the basket|basket for|shaking the basket', 'airfry'),
    (r'\bwok\b|stir-fry|stir fry|very hot|high heat|smoking', 'wok'),
    (r'crack|beat the eggs?|whisk the eggs?|pour the eggs?', 'crack-egg'),
    (r'blitz|blend|food processor|pur[ée]e', 'blend'),
    (r'grate|zest|microplane', 'grate'),
    (r'drain|rinse|colander|pat .{0,12}dry', 'drain'),
    (r'boil|blanch|kettle|boiling water', 'boil'),
    (r'marinate|marinade|rub .{0,12}in|work the rub|coat', 'marinate'),
    (r'whisk|beat ', 'whisk'),
    (r'squeeze|wedges to|juice over|lemon over|lime over', 'squeeze'),
    (r'chop|slice|cut |dice|shred|trim|score|halve|quarter|baton|smash', 'chop'),
    (r'simmer|cover and cook|bubble|reduce (to|by)|thicken|stew', 'simmer'),
    (r'serve|plate|divide between|pile onto|spoon over|lift onto|onto plates|to the table', 'serve'),
    (r'scatter|sprinkle|top with|finish with|garnish|strew', 'scatter'),
    (r'\brest\b|leave .{0,14}minutes|stand for|set aside|off the heat', 'rest'),
    (r'flip|turn(ing)? (the|them|at)|other side', 'flip'),
    (r'fry|sear|brown|sizzle|griddle|saut|in the pan|add the oil', 'fry'),
    (r'toss|turn .{0,14}through|fold .{0,14}through|combine|mix|stir', 'toss'),
]
STEP_RULES = [(re.compile(p), k) for p, k in STEP_RULES]


def step_glyph(text, index, total):
    low = text.lower()
    for rx, key in STEP_RULES:
        if rx.search(low):
            return key
    return 'serve' if index == total - 1 else 'fry'


def action_svg(key, color, size='9mm'):
    return (f'<svg viewBox="0 0 48 48" width="{size}" height="{size}" fill="none" stroke="{color}" '
            f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{ACTIONS[key]}</svg>')
