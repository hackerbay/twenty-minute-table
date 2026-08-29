import base64, html, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collections import defaultdict, Counter
from parse import load_all, METHODS, ORDER, inline
from icons import icon, dial, anatomy
sys.path.insert(0, str(Path(__file__).resolve().parent / 'art'))
from compose import pick_icons, hero_svg, step_glyph, action_svg
from pairings import sides_for, mains_for
from pantry_data import SHELVES, KIT, RULES

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
NM = ROOT / 'node_modules'
IMG = ROOT / 'images'
IMG.mkdir(exist_ok=True)

_MIME = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp'}

def photo(stem):
    """Return a data: URI for images/<stem>.<ext> if the user has supplied one."""
    for ext, mime in _MIME.items():
        f = IMG / (stem + ext)
        if f.exists():
            return f'data:image/{mime};base64,' + base64.b64encode(f.read_bytes()).decode()
    return None
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
FR = NM / '@fontsource-variable/fraunces/files'; IN = NM / '@fontsource/inter/files'
FONTS = f"""
@font-face{{font-family:'Fraunces';src:url(data:font/woff2;base64,{b64(FR/'fraunces-latin-full-normal.woff2')}) format('woff2-variations');font-weight:100 900;font-style:normal;font-display:block;}}
@font-face{{font-family:'Fraunces';src:url(data:font/woff2;base64,{b64(FR/'fraunces-latin-full-italic.woff2')}) format('woff2-variations');font-weight:100 900;font-style:italic;font-display:block;}}
""" + "".join(
f"@font-face{{font-family:'Inter';src:url(data:font/woff2;base64,{b64(IN/f'inter-latin-{w}-normal.woff2')}) format('woff2');font-weight:{w};font-style:normal;font-display:block;}}\n"
for w in (400, 500, 600, 700))

DARK = {'Air fryer': '#E58A62', 'One pan': '#98BE7C', 'Wok': '#DDA05F', 'No cook': '#77BFD1'}
CSS = (HERE / 'style.css').read_text()

def page(cls, topcolor, inner, folio=None):
    bar = f'<div class="topbar" style="background:{topcolor}"></div>' if topcolor else ''
    f = (f'<div class="folio">{folio}</div><div class="pageno">{{{{PN}}}}</div>') if folio else ''
    return f'<section class="page {cls}">{bar}<div class="inner">{inner}</div>{f}</section>'

def esc(s): return html.escape(s, quote=False)

def build(recipes):
    mains = [r for r in recipes if int(r['num']) <= 50]
    brek  = [r for r in recipes if 50 < int(r['num']) <= 70]
    puds  = [r for r in recipes if 70 < int(r['num']) <= 85]
    sides = [r for r in recipes if int(r['num']) > 85]
    byn2 = {r['num']: r for r in recipes}
    allc  = len({r['cuisine'] for r in recipes})
    counts = Counter(r['method'] for r in recipes)
    pages = []
    FRONT = 11                      # cover, foreword, pantry, rules, 4 contents, 2 cuisine, when-to-cook
    ORDERED = [mains, sides, brek, puds]   # the order the sections appear in the book
    pageno, _p = {}, FRONT + 1
    for _sec in ORDERED:
        _p += 1                                   # the section divider
        for _i, _r in enumerate(_sec):
            pageno[_r['num']] = _p + 2 * _i
        _p += 2 * len(_sec)

    def texture(rs):
        return ' &nbsp;·&nbsp; '.join(esc(r['title']) for r in rs)

    def chips(rs):
        c = Counter(r['method'] for r in rs)
        return ''.join(
            f'<div class="cchip" style="border-color:{DARK[m]}55;color:{DARK[m]}">{icon(METHODS[m]["key"],"4mm")}'
            f'<b class="d">{c[m]}</b><span>{METHODS[m]["label"]}</span></div>'
            for m in ORDER if c[m])

    # ============================== COVER ==============================
    stats = [(str(len(recipes)), 'Recipes'), (str(allc), 'Cuisines'), ('20', 'Minutes, max'), ('1', 'Pan or basket')]
    pages.append(page('cover', None, f"""
    <div class="cover-rule"></div>
    <div style="margin-top:5mm" class="eyebrow">A cookbook for weeknights, slow mornings and something afterwards</div>
    <h1 class="d">The<br>20&#8209;Minute<br><em>Table</em></h1>
    <p class="cover-sub">Eighty-five fast, whole-food recipes for people who want breakfast in ten minutes, dinner in twenty and pudding in eight &mdash; and who would rather not spend the evening washing up.</p>
    <div style="flex:1.05"></div>
    <div class="stats">{''.join(f'<div class="stat"><div class="sv d">{v}</div><div class="sl">{l}</div></div>' for v,l in stats)}</div>
    <div style="flex:1"></div>
    <div class="texture">{texture(recipes)}</div>
    <div style="height:9mm"></div>
    <div class="cover-chips">{chips(recipes)}</div>
    <div style="height:8mm"></div>
    <div class="cover-rule"></div>
    <div class="cover-foot" style="margin-top:4mm"><div>Compiled for Nawaz Dhandala</div><div>August 2026</div></div>"""))

    # ============================== FOREWORD ==============================
    KEY = [
      ("The ring", "Total time against a twenty-minute dial, so you can see the cost of a recipe before you read it."),
      ("The number", "Every recipe is numbered once. The contents, the cuisine index and the what-to-cook-when list all point back to it."),
      ("The panel", "Everything you need, listed in the order you will reach for it, grouped when the dish has two parts."),
      ("Why it works", "The one piece of technique that makes the dish fast, or good, or both. Read it once; you will not need it again."),
      ("The strip", "Approximate nutrition for a quarter of the finished dish. Estimates, rounded, and worth exactly what estimates are worth."),
      ("Washing up", "What you are actually committing to. This is the number that decides whether a recipe gets cooked twice."),
    ]
    keyhtml = ''.join(
      f'<div class="kitem"><div class="kn">{i+1}</div><div><b>{t}</b>{b}</div></div>'
      for i,(t,b) in enumerate(KEY))
    pages.append(page('', '#A5632A', f"""
    <div class="pkicker">A short note first</div>
    <h2 class="ptitle d">Twenty Minutes<br>Is Plenty</h2>
    <div class="fw">
      <p class="lede">Most of what makes cooking slow has nothing to do with cooking. It is the deciding, the shopping, the hunting for a jar of something at the back of a cupboard, and the twenty minutes of washing up that follow a meal that took thirty to make.</p>
      <p>So this book removes those parts rather than the good ones. Nothing here is a shortcut version of a longer dish &mdash; no simmering-for-an-hour recipe with the hour taken out. These are dishes that were always fast, drawn from the kitchens where fast cooking is not a compromise but the whole tradition: a wok of chicken and holy basil, a basket of cauliflower under harissa, eggs cooked in tomatoes in a pan the size of a dinner plate.</p>
      <p>Everything is built on whole ingredients, which is less an ideology than a practical matter: they cook faster than you think, they taste of what they are, and they let you season a dish rather than negotiate with something already seasoned for you. And every recipe was written to leave one pan or one basket behind. That constraint is the reason these end up in the weekly rotation rather than the someday pile.</p>
      <p>A word on the timings. They are honest, and they assume a cold start: knife out, nothing chopped, the pan not yet on. They also assume you read the recipe through once before you begin, which for a fifteen-minute dish is less a suggestion than the method itself.</p>
      <p class="sign">Cook them in any order. Break them freely. The swap notes exist because you will not have everything, and that has never once mattered.</p>
    </div>
    <div class="anat">
      <div class="anat-fig">{anatomy()}<div class="anat-cap">Every recipe page, without exception</div></div>
      <div class="anat-key"><div class="pkicker" style="margin-bottom:4mm">How a page works</div>{keyhtml}</div>
    </div>""", 'TWENTY MINUTES IS PLENTY'))

    # ============================== PANTRY CHECKLIST ==============================
    shelves_html = ''.join(
        f'<div class="shelf"><h4>{name}</h4>' +
        ''.join(f'<label class="ck"><span class="box"></span>{i}</label>' for i in items) + '</div>'
        for name, items in SHELVES)
    n_items = sum(len(i) for _, i in SHELVES)
    pages.append(page('', '#C1502E', f"""
    <div class="pkicker">Before you start &nbsp;·&nbsp; {n_items} things</div>
    <h2 class="ptitle d">The Fast Pantry</h2>
    <p class="pintro">Twenty-minute cooking only works when the slow part &mdash; the shopping, the searching, the standing in front of an open cupboard &mdash; has already happened. Tick your way through this once and every one of the {len(recipes)} recipes in this book becomes a decision rather than a project. Nothing here is exotic; most of it keeps for months.</p>
    <div class="hrule" style="margin:5mm 0"></div>
    <div class="shelves">{shelves_html}</div>
    <div class="kitwrap">
      <div class="hrule" style="margin:0 0 5mm"></div>
      <div class="pan">
        <div class="pcard"><h4>Buy once, keep for months</h4><p>Everything in the first four columns. Spices lose their edge after about a year, so buy the small jars and use them hard rather than buying the large ones and forgetting them.</p></div>
        <div class="pcard"><h4>Buy weekly, in quantity</h4><p>Lemons, limes, ginger, garlic, spring onions, chillies, a bag of spinach and a bunch each of coriander and parsley. Herbs keep a week if you stand them stems-down in a glass of water in the fridge door.</p></div>
      </div>
    </div>""", 'THE FAST PANTRY'))

    # ============================== FIVE RULES ==============================
    pages.append(page('', '#A5632A', f"""
    <div class="pkicker">And then</div>
    <h2 class="ptitle d">Ten Rules for a<br>Twenty-Minute Dinner</h2>
    <div class="hrule" style="margin:6mm 0 7mm"></div>
    <div class="rules big">{''.join(f'<div class="rule-item"><div class="rn d">{i+1}</div><div class="rt"><b>{t}</b> {b}</div></div>' for i,(t,b) in enumerate(RULES))}</div>
    <div class="kitwrap">
      <div class="hrule" style="margin:0 0 5mm"></div>
      <div class="pkicker" style="margin-bottom:3.5mm">The kit &mdash; and nothing else</div>
      <div class="shelf kit">{''.join(f'<label class="ck"><span class="box"></span>{k}</label>' for k in KIT)}</div>
    </div>""", 'TEN RULES'))

    # ============================== CONTENTS ==============================
    def toc_group(m, rs):
        info = METHODS[m]
        rows = ''.join(
            f'<div class="trow"><span class="n" style="color:{info["color"]}">{r["num"]}</span>'
            f'<span class="t">{esc(r["title"])}</span><span class="lead"></span>'
            f'<span class="mn">{r["minutes"]}&#8202;min</span></div>'
            for r in rs if r['method'] == m)
        n = sum(1 for r in rs if r['method'] == m)
        if not n: return ''
        return (f'<div class="toc-group"><div class="tg-head" style="color:{info["color"]}">'
                f'{icon(info["key"],"4.2mm")}<span class="nm">{info["label"]}</span>'
                f'<span class="ct">{n} {"recipe" if n==1 else "recipes"}</span></div>{rows}</div>')

    pages.append(page('', '#5A7A48', f"""
    <div class="pkicker">Fifty recipes &nbsp;·&nbsp; Section one</div>
    <h2 class="ptitle d">Lunch &amp; Dinner</h2>
    <p class="pintro" style="max-width:130mm">Grouped by how much of your attention they need. The air fryer looks after itself while you set the table; the stove wants five unbroken minutes; the no-cook recipes want nothing but a sharp knife.</p>
    <div class="hrule" style="margin:5.5mm 0"></div>
    <div class="toc">
      <div>{toc_group('Air fryer',mains)}{toc_group('Wok',mains)}{toc_group('No cook',mains)}</div>
      <div>{toc_group('One pan',mains)}</div>
    </div>""", 'CONTENTS &nbsp;·&nbsp; LUNCH &amp; DINNER'))

    pages.append(page('', '#A5632A', f"""
    <div class="pkicker">Twelve recipes &nbsp;·&nbsp; Section two</div>
    <h2 class="ptitle d">On the Side</h2>
    <p class="pintro" style="max-width:134mm">Twelve things to put next to a main course, all of them under fifteen minutes and most of them under ten. Every lunch and dinner in this book names three of them at the foot of its page, and every side names the mains it belongs to.</p>
    <div class="hrule" style="margin:5.5mm 0"></div>
    <div class="toc">
      <div>{toc_group('Air fryer', sides)}{toc_group('No cook', sides)}</div>
      <div>{toc_group('One pan', sides)}{toc_group('Wok', sides)}</div>
    </div>
    <div class="sunday">
      <div class="sun-head"><span class="sun-k">How to cook two things at once</span>
        <span class="sun-s">The whole point of a twelve-minute side is that it costs you nothing</span></div>
      <div class="sun-grid">
        <div><h4>The basket is already hot</h4><p>An air-fryer side goes in after the main comes out, and is done in the time the meat needs to rest. Two of these want nothing but a shake halfway.</p></div>
        <div><h4>Nothing to cook at all</h4><p>Five of the twelve never see heat. Smashed cucumber, a sumac salad, pickled onions &mdash; assembled on the same board you already have out.</p></div>
        <div><h4>One burner, one lid</h4><p>Greens wilt in ninety seconds in a covered pan. Start them when you plate the main and they arrive at the table at the same moment.</p></div>
      </div>
    </div>""", 'CONTENTS &nbsp;·&nbsp; ON THE SIDE'))

    LEGEND = {
      'Air fryer': 'Everything goes in one basket. Preheat, load, walk away, come back to something blistered at the edges.',
      'One pan':   'A single wide pan on the hob, start to finish. Nothing is browned in batches and set aside.',
      'Wok':       'Very high heat and constant movement. Have every ingredient cut and within reach before it goes on.',
      'No cook':   'No heat at all beyond, occasionally, a kettle. A knife, a board, a bowl.',
    }
    legend = ''.join(
      f'<div class="lg"><h5 style="color:{METHODS[m]["color"]}">{icon(METHODS[m]["key"],"4.4mm")}'
      f'{METHODS[m]["label"]}</h5><p>{LEGEND[m]}</p></div>' for m in ORDER)

    pages.append(page('', '#A5632A', f"""
    <div class="pkicker">Twenty recipes &nbsp;·&nbsp; Section three</div>
    <h2 class="ptitle d">Breakfast</h2>
    <p class="pintro" style="max-width:130mm">Savoury more often than sweet, because savoury is faster and keeps you full until lunch. Six of these are on the table in ten minutes; three of them never see heat.</p>
    <div class="hrule" style="margin:5.5mm 0"></div>
    <div class="toc">
      <div>{toc_group('Air fryer',brek)}{toc_group('Wok',brek)}{toc_group('No cook',brek)}</div>
      <div>{toc_group('One pan',brek)}</div>
    </div>
    <div class="sunday">
      <div class="sun-head"><span class="sun-k">Twenty minutes on Sunday</span>
        <span class="sun-s">Three small jobs that turn nine of these breakfasts into five-minute ones</span></div>
      <div class="sun-grid">
        <div><h4>Cook a large pot of rice</h4><p>Cold cooked rice is the backbone of five recipes here &mdash; the congee, the two fried rices, the egg rice and the rice soup. It keeps three days and fries far better cold than warm.</p></div>
        <div><h4>Toast a tray of nuts and seeds</h4><p>Almonds, walnuts, pumpkin and sesame seeds, eight minutes in the air fryer at 160&deg;C. Into a jar, and every bowl and salad in the book gets its finish for free.</p></div>
        <div><h4>Blitz ginger and garlic</h4><p>A whole head of garlic and a thumb of ginger to a paste, frozen in an ice-cube tray. One cube is roughly one recipe, and it removes the only fiddly job most of these have.</p></div>
      </div>
    </div>
    <div class="legend-wrap">
      <div class="legend">{legend}</div>
      <p class="legend-note">A <b>v</b> beside a line in the contents marks a vegetarian recipe &mdash; {sum(1 for r in recipes if r['veg'])} of the {len(recipes)} are. Every recipe serves four, lists metric quantities first with US cups and ounces alongside, and assumes a cold start. The ring beside each title shows the total time against a twenty-minute dial; the strip at the foot of the page gives approximate nutrition per serving, and the line beneath it tells you exactly what you will be washing.</p>
    </div>""", 'CONTENTS &nbsp;·&nbsp; BREAKFAST'))

    # ============================== CONTENTS: DESSERTS ==============================
    pages.append(page('', '#2C6B7B', f"""
    <div class="pkicker">Fifteen recipes &nbsp;·&nbsp; Section four</div>
    <h2 class="ptitle d">Something Afterwards</h2>
    <p class="pintro" style="max-width:132mm">Pudding after a proper dinner should be small, sharp and mostly fruit. Nothing here is a cake. Everything is between {min(r['minutes'] for r in puds)} and {max(r['minutes'] for r in puds)} minutes, and every one of them is under 320 calories a serving.</p>
    <div class="hrule" style="margin:5.5mm 0"></div>
    <div class="toc">
      <div>{toc_group('Air fryer', puds)}{toc_group('Wok', puds)}{toc_group('No cook', puds)}</div>
      <div>{toc_group('One pan', puds)}</div>
    </div>
    <div class="sunday">
      <div class="sun-head"><span class="sun-k">How these are sweetened</span>
        <span class="sun-s">Fruit first, and never more than two tablespoons of anything else across four servings</span></div>
      <div class="sun-grid">
        <div><h4>Ripe fruit does the work</h4><p>A peach at the point of collapse, a mango that gives under the thumb, figs that have gone jammy. Fruit that is properly ripe needs almost nothing added, which is the whole trick.</p></div>
        <div><h4>Dates instead of sugar</h4><p>Medjool dates blitzed with nuts give sweetness, body and fibre in one move. They are the reason the truffles hold together without anything melted into them.</p></div>
        <div><h4>Something sour alongside</h4><p>Thick yoghurt, skyr, ricotta, lime. The sour half is what stops a sweet plate cloying, and it is why nearly every recipe here has a spoonful of something white on it.</p></div>
      </div>
    </div>""", 'CONTENTS &nbsp;·&nbsp; SOMETHING AFTERWARDS'))

    # ============================== BY CUISINE (two pages) ==============================
    by = defaultdict(list)
    for r in recipes: by[r['cuisine']].append(r)
    entries = sorted(by.items())
    weights = [len(rs) + 1.6 for _, rs in entries]
    half, run, cut = sum(weights) / 2, 0, len(entries)
    for i, w in enumerate(weights):
        run += w
        if run >= half:
            cut = i + 1
            break

    def ci_block(items):
        return ''.join(
            f'<div class="ci"><h4>{esc(c)}</h4><div class="u"></div>' +
            ''.join(f'<p><span class="n">{r["num"]}</span><span>{esc(r["title"])}</span>'
                    f'<span class="cp">{pageno[r["num"]]}</span></p>' for r in rs) + '</div>'
            for c, rs in items)

    first, last = entries[0][0], entries[cut - 1][0]
    pages.append(page('', '#2C6B7B', f"""
    <div class="pkicker">{len(by)} kitchens &nbsp;·&nbsp; {esc(first)} to {esc(last)}</div>
    <h2 class="ptitle d">By Cuisine</h2>
    <p class="pintro">Cook your way around the world on a Tuesday. The shortcuts here are in the technique and the cut, never in the seasoning. The number on the left is the recipe; the number on the right is the page.</p>
    <div class="hrule" style="margin:5mm 0"></div>
    <div class="cindex">{ci_block(entries[:cut])}</div>""", 'BY CUISINE &nbsp;·&nbsp; I'))

    pages.append(page('', '#2C6B7B', f"""
    <div class="pkicker">{esc(entries[cut][0])} to {esc(entries[-1][0])}</div>
    <h2 class="ptitle d">By Cuisine <span style="color:var(--ink4)">II</span></h2>
    <p class="pintro">Seventy recipes, {len(by)} kitchens, and not one of them longer than twenty minutes.</p>
    <div class="hrule" style="margin:5mm 0"></div>
    <div class="cindex">{ci_block(entries[cut:])}</div>""", 'BY CUISINE &nbsp;·&nbsp; II'))

    # ============================== WHAT TO COOK WHEN ==============================
    byn = {r['num']: r for r in recipes}
    SHORT = {'16':'Pad Krapow','22':'Shogayaki','37':'Moqueca Express','46':'Vietnamese Summer Roll Bowl',
             '57':'Gyeran Bap','58':'Ginger Congee','65':'Khao Tom','67':'Sinangag','59':'Rava Uttapam',
             '39':'Nasi Goreng Cauliflower Rice','12':'Cajun Blackened Cod','25':'Chana Masala',
             '55':'Crispy Chickpea & Avocado Toast','69':'Danish Rye & Cottage Cheese',
             '70':'Orange, Date & Almond Yoghurt','50':'Turkish Coban Salad','68':'Bircher Muesli',
             '34':'Smoky Paprika Chicken','51':'Sweet Potato, Egg & Chilli Hash','54':'Banana & Oat Bake',
             '02':'Miso-Glazed Salmon','18':'Ginger-Garlic Prawn Stir-Fry','62':'Pan con Tomate & Soft Eggs',
             '09':'Jerk Chicken','36':'Lomo Saltado','48':'Salmon Poke Bowl','33':'Gambas al Ajillo',
             '08':'Sicilian Sea Bass','29':'Prawn Saganaki','49':'Prawn Ceviche Tostada','07':'Chilli-Lime Prawns',
             '11':'Berbere Sweet Potato','31':'Tuscan White Bean & Kale','47':'Fattoush & Crisped Chickpeas',
             '32':'Tuna Puttanesca Beans','63':'Ful Medames','24':'Egg & Spinach Bhurji','26':'Turkish Menemen',
             '27':'Green Shakshuka','60':'Persian Herb & Feta Omelette','66':'Egg & Tomato Stir-Fry',
             '30':'Broccoli Aglio e Olio','42':'Ethiopian Gomen','45':'Georgian Green Beans',
             '05':'Gochujang Tofu','44':'West African Peanut Stew','64':'Buckwheat Galette','53':'Masala Omelette Muffins'}
    def short(n):
        return SHORT.get(n) or byn[n]['title']
    WHEN = [
      ("There is nothing in the house but eggs", "24 26 27 60 66"),
      ("You have ten minutes, and that is the whole budget", "07 18 57 62 66"),
      ("Someone is arriving at eight and it is ten to", "02 07 18 32 62"),
      ("You want it to taste like a holiday", "09 16 33 36 48"),
      ("It is cold, and grey, and has been for weeks", "25 37 44 58 65"),
      ("You want to feel virtuous without feeling deprived", "11 31 46 47 68"),
      ("Payday is Friday and it is Tuesday", "24 25 31 32 63"),
      ("You cannot face the washing up at all", "02 12 50 69 70"),
      ("You want something green on the plate", "05 27 30 42 45"),
      ("You are cooking to impress someone", "08 09 29 36 48"),
      ("It is Sunday and you have twenty unhurried minutes", "49 51 54 59 64"),
      ("You need it to keep you full until two o&rsquo;clock", "51 53 55 63 67"),
      ("It is far too hot to turn anything on", "46 48 49 50 69"),
      ("You want the whole flat to smell extraordinary", "04 09 23 41 59"),
      ("Someone claims not to like vegetables", "16 20 35 61 67"),
      ("There is half a cabbage and a lot of optimism", "05 15 22 48 68"),
    ]
    when_html = ''.join(
      f'<div class="when"><div class="wq d">{q}</div><div class="wl">' +
      ''.join(f'<span><b>{n}</b>{esc(short(n))}</span>' for n in ns.split()) +
      '</div></div>' for q, ns in WHEN)
    pages.append(page('', '#5A7A48', f"""
    <div class="pkicker">The real index</div>
    <h2 class="ptitle d">What to Cook When</h2>
    <p class="pintro">Nobody stands in the kitchen at seven o&rsquo;clock thinking in cuisines. This is the index for the way the question actually arrives.</p>
    <div class="hrule" style="margin:5mm 0"></div>
    <div class="whens">{when_html}</div>""", 'WHAT TO COOK WHEN'))

    # ============================== SECTION DIVIDERS + RECIPES ==============================
    def divider(kicker, title, blurb, rs, size, trio):
        cz = len({r['cuisine'] for r in rs})
        fastest = min(r['minutes'] for r in rs)
        under = sum(1 for r in rs if r['minutes'] <= 12)
        st = [(str(len(rs)), 'Recipes'), (str(cz), 'Cuisines'),
              (str(fastest), 'Minutes, fastest'), (str(under), 'Under twelve minutes')]
        sh = ''.join(f'<div class="stat"><div class="sv d">{v}</div><div class="sl">{l}</div></div>' for v,l in st)
        return page('cover divider', None, f"""
        <div class="cover-rule"></div>
        <div style="margin-top:5mm" class="eyebrow">{kicker}</div>
        <h1 class="d dv {size}">{title}</h1>
        <p class="cover-sub">{blurb}</p>
        <div style="flex:1"></div>
        <div class="stats">{sh}</div>
        <div style="flex:1"></div>
        <div class="starts"><div class="st-k">If you only cook three</div>
          <div class="strio">{''.join(f'<div><div class="sn">{n}</div><h4>{esc(byn2[n]["title"])}</h4><p>{why}</p></div>' for n, why in trio)}</div>
        </div>
        <div style="flex:.7"></div>
        <div class="texture">{texture(rs)}</div>
        <div style="height:9mm"></div>
        <div class="cover-chips">{chips(rs)}</div>
        <div style="height:7mm"></div>
        <div class="cover-rule"></div>""")

    byn2 = {r['num']: r for r in recipes}

    def recipe_pages(r):
        """A recipe is a spread: the plate page, then the method page."""
        c, tint = r['m']['color'], r['m']['tint']
        num, title = r['num'], esc(r['title'])

        # ---------- hero: a supplied photograph, else a composed illustration
        hero_photo = photo(f"{num}-hero")
        hero = f'<div class="hero"><img src="{hero_photo}" alt=""></div>' if hero_photo else ''

        ings = ''
        for g in r['ing_groups']:
            if g['name']:
                ings += f'<div class="ing-group">{inline(g["name"])}</div>'
            ings += ''.join(f'<div class="ing"><span class="bt" style="background:{c}"></span>'
                            f'<span>{inline(x)}</span></div>' for x in g['items'])

        keys = ['Calories', 'Protein', 'Carbs', 'Fat', 'Fibre']
        units = ['kcal', 'g', 'g', 'g', 'g']
        macs = ''.join(f'<div class="mac"><div class="v d" style="color:{c}">{v}'
                       f'<span class="mu"> {u}</span></div><div class="k">{k}</div></div>'
                       for v, k, u in zip(r['macros'], keys, units))
        prep = (f'<span class="sep"></span><span>{r["prep"]} prep / {r["cook"]} cook</span>'
                if r['prep'] else '')
        notes = ''.join(f'<div class="note"><b style="color:{c}">{inline(t)}</b>{inline(bd)}</div>'
                        for t, bd in r['notes'])
        pair = sides_for(num, byn2) if int(num) <= 50 else (
               mains_for(num, byn2, 4) if int(num) > 85 else [])
        if pair:
            lab = 'Goes with' if int(num) <= 50 else 'Goes next to'
            goes = ('<div class="goes"><b style="color:%s">%s</b>%s</div>' % (c, lab, ''.join(
                f'<span class="gitem"><i style="color:{p["m"]["color"]}">{p["num"]}</i>'
                f'{esc(p["title"])}</span>' for p in pair)))
        else:
            goes = ''

        page_a = page('', c, f"""
        {hero}
        <div class="rhead">
          <div class="rnum d" style="color:{c}">{num}</div>
          <div class="rht">
            <h1 class="rtitle d">{title}</h1>
            <div class="rmeta">
              <span class="pill" style="background:{c}">{icon(r['m']['key'],'3.5mm',1.7)}{r['m']['label']}</span>
              <span>{esc(r['cuisine'])}</span>{prep}<span class="sep"></span><span>Serves {r['serves']}</span>
              {'<span class="vpill">Vegetarian</span>' if r['veg'] else ''}
            </div>
          </div>
          <div class="dialwrap">{dial(r['minutes'], c)}
            <div class="dialtext"><div class="dv d" style="color:{c}">{r['minutes']}</div><div class="dl">min</div></div>
          </div>
        </div>
        <p class="hook d" style="border-color:{c};color:{c}">{inline(r['hook'])}</p>
        <div class="rbody rgrid{' wide' if r['ing_count'] >= 13 else ''}">
          <div class="rcol"><div class="blab" style="color:{c}">Ingredients</div>
            <div class="ing-panel{' two' if r['ing_count'] >= 13 else ''}">{ings}</div></div>
          <div class="rcol"><div class="blab" style="color:{c}">Why it works</div>
            <p class="why">{inline(r['why'])}</p></div>
        </div>
        <div class="rfoot">
          <div class="notes">{notes}</div>
          <div class="strip" style="background:{tint}">{macs}</div>
          <div class="wash"><b style="color:{c}">Washing up</b><span>{inline(r['washing'])}</span></div>
          {goes}
        </div>""", f"{num} &nbsp;·&nbsp; {title.upper()}")

        # ---------- method page
        total = len(r['steps'])
        steps = ''
        for i, st in enumerate(r['steps']):
            sp = photo(f"{num}-step-{i+1}")
            if sp:
                mark = f'<div class="sphoto"><img src="{sp}" alt=""></div>'
            else:
                mark = (f'<div class="sglyph" style="background:{tint};color:{c}">'
                        f'{action_svg(step_glyph(st, i, total), c, "100%")}</div>')
            steps += (f'<div class="mstep"><div class="mmark">{mark}'
                      f'<div class="mnum d" style="background:{c}">{i+1}</div></div>'
                      f'<div class="mtext">{inline(st)}</div></div>')

        page_b = page('', c, f"""
        <div class="mhead">
          <div class="mh-num d" style="color:{c}">{num}</div>
          <div class="mh-title d">{title}</div>
          <div class="mh-meta"><span class="pill" style="background:{c}">
            {icon(r['m']['key'],'3.5mm',1.7)}{r['m']['label']}</span>
            <span>{r['minutes']} min</span><span class="sep"></span><span>Serves {r['serves']}</span>
            {'<span class="vpill">Vegetarian</span>' if r['veg'] else ''}</div>
        </div>
        <div class="blab mblab" style="color:{c}">Method</div>
        <div class="rbody msteps">{steps}</div>
        <div class="rfoot">
          <div class="mfoot"><span style="color:{c}">{icon(r['m']['key'],'4mm')}</span>
            <span>{r['m']['label']} &nbsp;·&nbsp; {r['minutes']} minutes &nbsp;·&nbsp; serves {r['serves']}</span>
            <span class="mf-wash">{inline(r['washing'])}</span></div>
        </div>""", f"{num} &nbsp;·&nbsp; METHOD")

        return [page_a, page_b]

    pages.append(divider('Section one &nbsp;·&nbsp; Fifty recipes', 'Lunch<br><em>&amp;</em> Dinner',
        'Everything on the table inside twenty minutes from a cold start, across thirty-six kitchens, leaving one pan or one basket behind.', mains, 'dv-1',
        [('16','Twelve minutes, one wok, and the dish that converts people to cooking fast.'),
         ('01','The whole dinner in one basket, and a sauce you stir in a mug while it cooks.'),
         ('29','Prawns, tomatoes and feta in a pan, on the table before anyone has finished a drink.')]))
    for r in mains: pages += recipe_pages(r)

    pages.append(divider('Section two &nbsp;·&nbsp; Twelve recipes', 'On the<br><em>Side</em>',
        'Twelve fast things to put next to a main course. Five never see heat at all, and every lunch and dinner in this book names three of them.', sides, 'dv-1',
        [('87','Cucumber smashed with the flat of a knife, dressed in garlic and sesame. Eight minutes.'),
         ('92','Potatoes that go crisp in the basket the main has just left.'),
         ('89','Greens, garlic, chilli and lemon, wilted in ninety seconds under a lid.')]))
    for r in sides: pages += recipe_pages(r)

    pages.append(divider('Section three &nbsp;·&nbsp; Twenty recipes', '<em>Breakfast</em>',
        'Savoury more often than sweet, hot more often than cold, and quick enough that eating standing up stops being the only option.', brek, 'dv-2',
        [('57','Ten minutes, one pan, and the best argument there is for keeping cooked rice in the fridge.'),
         ('61','Eggs, beans and a charred tomato salsa. Weekend food that happens to take fifteen minutes.'),
         ('68','Bircher without the overnight wait, because the apple is grated rather than chopped.')]))
    for r in brek: pages += recipe_pages(r)

    pages.append(divider('Section four &nbsp;·&nbsp; Fifteen recipes', 'Something<br><em>Afterwards</em>',
        'Small, sharp and mostly fruit. Nothing over twenty minutes, nothing over 320 calories, and not a cake among them.', puds, 'dv-1',
        [('81','Four ingredients, ten minutes, and nobody guesses what makes it that texture.'),
         ('75','Figs, honey and walnuts in a hot pan for four minutes. The oldest pudding in the book.'),
         ('71','Peaches in the basket while you clear the plates, yoghurt and pistachio on top.')]))
    for r in puds: pages += recipe_pages(r)

    # ============================== ENDNOTE ==============================
    KNOW = [
      ("Salt", "Season the pan, not the plate. A dish salted at the end tastes of salt; a dish salted as it cooks tastes of itself. The exception is anything raw or dressed, which wants it at the last moment or it weeps."),
      ("Acid", "If something tastes flat and you have already salted it, it wants acid, not more salt. Lemon, lime, vinegar, a spoonful of yoghurt. This is the single most useful thing in this book."),
      ("Heat", "Almost every fast recipe that disappoints was cooked in a pan that was not hot enough. Food that steams instead of browning has lost the only advantage speed gives you."),
      ("Crowding", "Two batches in a hot pan beat one batch in a full one, every time. In the air fryer, a single layer with gaps is not a suggestion."),
      ("Resting", "Even four minutes off the heat will do more for a chicken thigh than any amount of extra cooking. Use the time to wash the pan."),
      ("Storing", "Cooked grains, roasted vegetables and cooked pulses keep three days and turn nearly any recipe here into a five-minute one. Dressed leaves and raw marinated fish keep for none."),
      ("Fat", "Do not be frightened of the tablespoon of oil. It carries flavour, it conducts heat, and a dish cooked in too little of it browns unevenly and tastes thin."),
      ("Herbs", "Soft herbs &mdash; coriander, basil, mint, parsley &mdash; go in off the heat or they turn to hay. Hard herbs like thyme and oregano go in early or they taste raw."),
      ("Garlic", "Grated garlic burns in ninety seconds. Sliced garlic takes three minutes. Choose the cut to suit the time the dish has, rather than the other way round."),
      ("Tasting", "Taste at the second-to-last minute, not after plating. Once it is on the plate the only thing you can still add is lemon."),
    ]
    pages.append(page('', '#2C6B7B', f"""
    <div class="pkicker">Afterwards</div>
    <h2 class="ptitle d">A Few Things<br>Worth Knowing</h2>
    <p class="pintro">None of these are recipes. They are the ten things that make the other {len(recipes)} work, and they will make everything else you cook better too.</p>
    <div class="hrule" style="margin:6mm 0"></div>
    <div class="pan">{''.join(f'<div class="pcard"><h4>{t}</h4><p>{b}</p></div>' for t,b in KNOW)}</div>
    <div class="colophon">
      <p class="signoff">The best cooking you will do this year will almost certainly take under twenty minutes, be eaten standing at the counter, and never be photographed. That is rather the point.</p>
      <div class="hrule" style="margin:0 0 5mm"></div>
      <div class="colo-grid">
        <div><h6>The book</h6><p>{len(recipes)} recipes across {allc} cuisines: {len(mains)} for lunch and dinner, {len(sides)} sides, {len(brek)} for breakfast, {len(puds)} for afterwards. {sum(1 for r in recipes if r['veg'])} of them are vegetarian.</p></div>
        <div><h6>The type</h6><p>Set in Fraunces, drawn by Phaedra Charles and Flavia Zimbardi, and Inter, drawn by Rasmus Andersson. Both are open source.</p></div>
        <div><h6>The numbers</h6><p>Nutrition figures are estimates for a quarter of the finished dish, rounded, and exclude anything listed under &ldquo;bulk it out&rdquo;. Cook the food, not the numbers.</p></div>
      </div>
    </div>""", 'A FEW THINGS WORTH KNOWING'))

    pages = [p.replace('{{PN}}', str(i + 1), 1) for i, p in enumerate(pages)]

    doc = (f'<!doctype html><html><head><meta charset="utf-8"><title>The 20-Minute Table</title>'
           f'<style>{FONTS}{CSS}</style></head><body>{"".join(pages)}</body></html>')
    Path(ROOT / 'build' / 'cookbook.html').write_text(doc, encoding='utf-8')
    return len(pages)

if __name__ == '__main__':
    (ROOT / 'build').mkdir(exist_ok=True)
    n = build(load_all())
    print('pages:', n, '| html', round((ROOT/'build'/'cookbook.html').stat().st_size/1e6, 2), 'MB')
