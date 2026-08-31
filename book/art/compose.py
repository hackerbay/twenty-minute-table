"""Turn a recipe's ingredient list into a flat-lay illustration.

Ingredient lines are matched against an ordered rule table to pick icon keys;
the icons are then scattered across the hero area with a seeded, deterministic
layout so the same recipe always produces the same picture.
"""
import math, random, re, sys
from pathlib import Path
from flatten import mix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from food import PART as FOOD
from actions import PART as ACTIONS
from colors import of as colour_of, shade, tone

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


def pick_icons(recipe, lo=5, hi=11):
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

_EL = re.compile(r'<[^>]+/>')
_D = re.compile(r'd="([^"]*)"')


def _is_closed(el):
    """Closed shapes get a fill; open detail strokes stay as line work."""
    if el.startswith(('<circle', '<ellipse', '<rect', '<polygon')):
        return True
    d = _D.search(el)
    return bool(d and 'z' in d.group(1).lower())


def paint(key, sw=2.0):
    """Render one food icon as a flat colour illustration in a 48x48 space."""
    base, accent = colour_of(key)
    line = shade(base, .5)
    out, seen_body = '', False
    for el in _EL.findall(FOOD[key]):
        if _is_closed(el):
            fill = base if not seen_body else accent
            seen_body = True
            out += el.replace('/>', f' fill="{fill}"/>')
        else:
            out += el
    return f'<g stroke="{line}" stroke-width="{sw}" fill="none">{out}</g>'


# --- the plate -------------------------------------------------------------
def _vessel(method, cx, cy, r, surface):
    """A plate, a pan or an air-fryer basket, seen from above.

    `surface` is the hero background the shadow falls on; it is pre-composited
    rather than drawn with alpha, because KDP requires a flattened interior.
    """
    rim, face, edge = '#FFFFFF', '#FDFAF4', '#E4DACA'
    sh = f'<ellipse cx="{cx:.0f}" cy="{cy + r * .10:.0f}" rx="{r * 1.03:.0f}" ry="{r * 1.0:.0f}" fill="{mix("#000000", surface, .07)}"/>'
    if method == 'Air fryer':
        k = r * .96
        return (sh + f'<rect x="{cx-k:.0f}" y="{cy-k:.0f}" width="{k*2:.0f}" height="{k*2:.0f}" rx="{k*.30:.0f}" '
                f'fill="{rim}" stroke="{edge}" stroke-width="2"/>'
                f'<rect x="{cx-k*.84:.0f}" y="{cy-k*.84:.0f}" width="{k*1.68:.0f}" height="{k*1.68:.0f}" '
                f'rx="{k*.24:.0f}" fill="{face}" stroke="{edge}" stroke-width="1.4"/>')
    if method in ('One pan', 'Wok'):
        return (sh + f'<path d="M{cx+r*.99:.0f} {cy-r*.15:.0f}h{r*.42:.0f}a{r*.08:.0f} {r*.08:.0f} 0 0 1 0 {r*.30:.0f}'
                f'h{-r*.42:.0f}z" fill="{edge}"/>'
                f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{rim}" stroke="{edge}" stroke-width="2.4"/>'
                f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*.86:.0f}" fill="{face}" stroke="{edge}" stroke-width="1.4"/>')
    return (sh + f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{rim}" stroke="{edge}" stroke-width="2"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*.80:.0f}" fill="{face}" stroke="{edge}" stroke-width="1.2"/>')


def _place(rng, placed, r, x0, x1, y0, y1, tries=140):
    best, best_d = None, -1
    for _ in range(tries):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if not placed:
            return x, y
        d = min(math.hypot(x - px, y - py) - pr for px, py, pr in placed)
        if d > best_d:
            best_d, best = d, (x, y)
    return best


def _node(key, x, y, size, rng, sw=2.0):
    k = size / 48.0
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({rng.uniform(-14, 14):.1f}) '
            f'scale({k:.4f}) translate(-24 -24)">{paint(key, sw / k)}</g>')


def hero_svg(recipe, color, tint):
    """A plated dish: the star ingredients heaped in the vessel the recipe uses,
    with the supporting cast laid out around it on the counter."""
    keys = pick_icons(recipe)
    rng = random.Random(int(recipe['num']) * 7919 + 17)
    method = recipe['method']

    surface = tone(tint, 1.10)
    left = int(recipe['num']) % 2 == 0
    cx = VB_W * (0.33 if left else 0.67)
    cy = VB_H * 0.50
    R = 74

    on = keys[:4]
    around = keys[4:]

    # a heap of food under the ingredients, so the plate reads as a dish
    mound = ''
    for i in range(3):
        mc = colour_of(on[min(i, len(on) - 1)])[0]
        ang = rng.uniform(0, 180)
        rx, ry = rng.uniform(R * .50, R * .64), rng.uniform(R * .38, R * .50)
        mx = cx + rng.uniform(-R * .18, R * .18)
        my = cy + rng.uniform(-R * .16, R * .16)
        # clipped to the plate shape, so the backdrop is the vessel face
        mound += (f'<ellipse cx="{mx:.0f}" cy="{my:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
                  f'transform="rotate({ang:.0f} {mx:.0f} {my:.0f})" fill="{mix(mc, "#FDFAF4", .30)}"/>')

    plate_items, placed = '', []
    for i, key in enumerate(on):
        size = (70 if i == 0 else rng.uniform(52, 60))
        px, py = _place(rng, placed, size * .5,
                        cx - R * .44, cx + R * .44, cy - R * .42, cy + R * .42)
        placed.append((px, py, size * .40))
        plate_items += _node(key, px, py, size, rng, 2.2)

    counter_items, cplaced = '', [(cx, cy, R * 1.10)]
    for key in around[:8]:
        size = rng.uniform(40, 52)
        px, py = _place(rng, cplaced, size * .5, 30, VB_W - 30, 34, VB_H - 34)
        cplaced.append((px, py, size * .50))
        counter_items += _node(key, px, py, size, rng, 2.1)

    flecks = ''
    for _ in range(34):
        x, y = rng.uniform(10, VB_W - 10), rng.uniform(10, VB_H - 10)
        if math.hypot(x - cx, y - cy) < R * 1.04:
            continue
        a = rng.choice([.18, .24, .3])
        flecks += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(1.2, 2.6):.1f}" '
                   f'fill="{mix(color, surface, a)}"/>')

    clip = f'plate{recipe["num"]}'
    shape = (f'<rect x="{cx-R*.96:.0f}" y="{cy-R*.96:.0f}" width="{R*1.92:.0f}" height="{R*1.92:.0f}" rx="{R*.29:.0f}"/>'
             if method == 'Air fryer' else f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*.84:.0f}"/>')

    return (f'<svg viewBox="0 0 {VB_W} {VB_H}" class="hero-svg" preserveAspectRatio="xMidYMid slice" '
            f'stroke-linecap="round" stroke-linejoin="round">'
            f'<defs><clipPath id="{clip}">{shape}</clipPath></defs>'
            f'<rect width="{VB_W}" height="{VB_H}" fill="{surface}"/>'
            f'{flecks}{_vessel(method, cx, cy, R, surface)}'
            f'<g clip-path="url(#{clip})">{mound}</g>{plate_items}{counter_items}</svg>')


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
