"""Generate a static website from the same recipe files that make the book.

Output lands in site/ as plain files — no server, no build step, no external
requests. Fonts are embedded in the stylesheet, so the whole thing can be
dropped on any static host.
"""
import base64, html, json, re, shutil, sys
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'art'))

from parse import load_all, METHODS, ORDER, inline
from icons import icon
from compose import step_glyph, action_svg
from pairings import sides_for, mains_for
from pantry_data import SHELVES, KIT, RULES
import planner as PLANNER
from diet import TAGS as DIET_TAGS, TAG_LABEL
from toddler_data import INTRO as TOD_INTRO, POINTS as TOD_POINTS, DISCLAIMER as TOD_DISC
import mission as MISSION
import imprint as IMP
from version import VERSION

SITE = ROOT / 'site'
ASSETS = SITE / 'assets'
NM = ROOT / 'node_modules'

PDF_NAME = 'The-20-Minute-Table.pdf'
PDF_SRC = ROOT / 'dist' / PDF_NAME

EPUB_NAME = 'The-20-Minute-Table.epub'
EPUB_SRC = ROOT / 'dist' / EPUB_NAME

GH_URL = 'https://github.com/hackerbay/twenty-minute-table'
REPO_TEXT = 'github.com/hackerbay/twenty-minute-table'

GH_ICON = ('<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" '
           'aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 '
           '7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09'
           '-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 '
           '1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59'
           '.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36'
           '.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 '
           '2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 '
           '.21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>')

STAR_ICON = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" '
             'aria-hidden="true"><path d="m12 3 2.85 5.78 6.38.93-4.62 4.5 1.09 6.35L12 '
             '17.56l-5.7 3 1.09-6.35-4.62-4.5 6.38-.93L12 3Z"/></svg>')

DL_ICON = ('<svg class="ico" width="14" height="14" viewBox="0 0 24 24" fill="none" '
           'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true">'
           '<path d="M12 3v12"/><path d="m7 12 5 5 5-5"/><path d="M5 21h14"/></svg>')

CHEV_ICON = ('<svg class="chev" width="12" height="12" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>')


def pdf_pages():
    """Page count read out of the built PDF, so the copy cannot drift from it."""
    if not PDF_SRC.exists():
        return None
    counts = [int(m) for m in re.findall(rb'/Count\s+(\d+)', PDF_SRC.read_bytes())]
    return max(counts) if counts else None

esc = lambda s: html.escape(s, quote=False)
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()

SECTIONS = [
    ('mains',      'Lunch & Dinner',       lambda n: n <= 50),
    ('sides',      'On the Side',          lambda n: n > 85),
    ('breakfast',  'Breakfast',            lambda n: 50 < n <= 70),
    ('afterwards', 'Something Afterwards', lambda n: 70 < n <= 85),
]


def slug(r):
    return re.sub(r'[^a-z0-9]+', '-', r['title'].lower()).strip('-')


def fonts_css():
    FR = NM / '@fontsource-variable/fraunces/files'
    IN = NM / '@fontsource/inter/files'
    css = (f"@font-face{{font-family:'Fraunces';src:url(data:font/woff2;base64,"
           f"{b64(FR/'fraunces-latin-full-normal.woff2')}) format('woff2-variations');"
           f"font-weight:100 900;font-style:normal;font-display:swap}}\n"
           f"@font-face{{font-family:'Fraunces';src:url(data:font/woff2;base64,"
           f"{b64(FR/'fraunces-latin-full-italic.woff2')}) format('woff2-variations');"
           f"font-weight:100 900;font-style:italic;font-display:swap}}\n")
    for w in (400, 500, 600, 700):
        css += (f"@font-face{{font-family:'Inter';src:url(data:font/woff2;base64,"
                f"{b64(IN/f'inter-latin-{w}-normal.woff2')}) format('woff2');"
                f"font-weight:{w};font-style:normal;font-display:swap}}\n")
    return css


def shell(title, body, depth=0, desc='', extra_head='', scripts=()):
    up = '../' * depth
    # The pages are served no-cache and the assets for an hour, so without a
    # key that changes with the release a returning visitor gets today's HTML
    # driven by yesterday's script. On the planner that is not cosmetic: the
    # week is rendered into the HTML at build time and re-rendered by plan.js,
    # and the two have to be the same version to agree.
    v = f'?v={VERSION}'
    more = ''.join(f'\n<script src="{up}assets/{s}{v}" defer></script>' for s in scripts)
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#1B201D">
<link rel="stylesheet" href="{up}assets/style.css{v}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='26'%3E%F0%9F%A5%A3%3C/text%3E%3C/svg%3E">
{extra_head}
</head>
<body>
{body}
<script src="{up}assets/app.js{v}" defer></script>{more}
</body>
</html>"""


def nav(depth=0, active=''):
    up = '../' * depth
    items = [('index.html', 'Recipes'), ('plan.html', 'Plan'),
             ('pantry.html', 'Pantry'), ('toddlers.html', 'Toddlers'),
             ('about.html', 'About')]
    parts = []
    for h, t in items:
        cls = ' class="on"' if active and h.startswith(active) else ''
        parts.append(f'<a href="{up}{h}"{cls}>{t}</a>')
    links = ''.join(parts)
    # The download menu is a sibling of <nav>, not a child of it. On a phone the
    # brand and the menu share the first row and the links get the second, which
    # is what makes a fifth link cost nothing: five links fit one row at 320px.
    # <details> rather than a scripted menu, so it opens, closes and takes the
    # keyboard on its own and the downloads still work with JavaScript off.
    menu = (f'<details class="dlm"><summary>{DL_ICON}<span>Download</span>{CHEV_ICON}</summary>'
            f'<div class="dlm-list">'
            f'<a href="{up}{PDF_NAME}" download>'
            f'<b>PDF</b><span>The printable book, laid out in spreads</span></a>'
            f'<a href="{up}{EPUB_NAME}" download>'
            f'<b>EPUB</b><span>Reflowable, for a phone or an e-reader</span></a>'
            f'</div></details>')
    return (f'<header class="nav"><a class="brand" href="{up}index.html">'
            f'<span class="brand-d">The 20-Minute Table</span></a>'
            f'{menu}<nav>{links}</nav></header>')


def footer(depth=0):
    up = '../' * depth
    return (f'<footer class="foot"><div class="wrap">'
            f'<p class="foot-t">The 20-Minute Table</p>'
            f'<p>Every recipe serves four, is on the table inside twenty minutes from a cold start, '
            f'and is built on whole ingredients. Nutrition figures are estimates. '
            f'<a href="{up}toddlers.html">Cooking for a toddler</a> &nbsp;·&nbsp; '
            f'<a href="{up}about.html">More about the book</a>.</p>'
            f'<p>Also on Amazon in '
            f'<a href="{IMP.amazon_url("paperback")}">paperback</a>, '
            f'<a href="{IMP.amazon_url("hardback")}">hardcover</a> and for '
            f'<a href="{IMP.amazon_url("kindle")}">Kindle</a>.</p>'
            f'<p class="foot-gh">{GH_ICON}<span>Open source &mdash; the recipes and the '
            f'typesetter that builds this are '
            f'<a href="{GH_URL}">on GitHub</a>. Fork it, fix it, add a dinner. '
            f'<span class="ver">v{VERSION}</span></span></p>'
            f'</div></footer>')


def contribute(depth=0):
    """The open-source invitation, shown at the foot of the longer pages."""
    return (f'<section class="gh"><div class="wrap"><div class="gh-card">'
            f'<p class="eyebrow">Open source</p>'
            f'<h2 class="d">Take it, cook it, change it</h2>'
            f'<p class="gh-lede">Every recipe, the typesetter that turns them into the '
            f'book, and this website are on GitHub. The code is MIT, the recipes are '
            f'CC&nbsp;BY&nbsp;4.0. Fork it, add the dinners your family actually eats, '
            f'translate it, print it for the inside of a cupboard door. Nobody should '
            f'have to choose between eating well and having twenty minutes.</p>'
            f'<div class="gh-actions">'
            f'<a class="btn btn-p" href="{GH_URL}">{GH_ICON}<span>View the repository</span></a>'
            f'<a class="btn btn-s" href="{GH_URL}/stargazers">{STAR_ICON}<span>Star it</span></a>'
            f'<a class="btn btn-s" href="{GH_URL}/blob/main/CONTRIBUTING.md">'
            f'<span>Add a recipe</span></a>'
            f'</div></div></div></section>')


# ---------------------------------------------------------------- index page
def build_index(recipes):
    counts = Counter(r['method'] for r in recipes)
    veg = sum(1 for r in recipes if r['veg'])
    cuisines = len({r['cuisine'] for r in recipes})

    chips = ''.join(
        f'<button class="chip" data-filter="method" data-value="{METHODS[m]["key"]}" '
        f'style="--c:{METHODS[m]["color"]}">{icon(METHODS[m]["key"],"1em",1.7)}'
        f'{METHODS[m]["label"]}<i>{counts[m]}</i></button>' for m in ORDER if counts[m])

    sect_chips = ''.join(
        f'<button class="chip" data-filter="section" data-value="{key}">{label}'
        f'<i>{sum(1 for r in recipes if test(int(r["num"])))}</i></button>'
        for key, label, test in SECTIONS)

    cards = ''
    for key, label, test in SECTIONS:
        rows = [r for r in recipes if test(int(r['num']))]
        cards += f'<h2 class="sect d" id="{key}">{esc(label)}<span>{len(rows)}</span></h2><div class="grid">'
        for r in rows:
            m = r['m']
            ing = ' '.join(i for g in r['ing_groups'] for i in g['items']).lower()
            cards += (
                f'<a class="card" href="r/{slug(r)}.html" '
                f'data-section="{key}" data-method="{m["key"]}" data-veg="{int(r["veg"])}" '
                f'data-min="{r["minutes"]}" data-kcal="{r["macros"][0]}" '
                f'data-search="{esc(r["title"].lower())} {esc(r["cuisine"].lower())} {esc(ing[:400])}" '
                f'style="--c:{m["color"]};--t:{m["tint"]}">'
                f'<div class="card-top"><span class="cnum d">{r["num"]}</span>'
                f'<span class="cmin d">{r["minutes"]}<i>min</i></span></div>'
                f'<h3 class="d">{esc(r["title"])}</h3>'
                f'<p class="chook">{esc(r["hook"])}</p>'
                f'<div class="cmeta"><span class="pill">{icon(m["key"],"1em",1.8)}{m["label"]}</span>'
                f'<span class="cui">{esc(r["cuisine"])}</span>'
                + (f'<span class="vtag">Veg</span>' if r['veg'] else '')
                + f'<span class="kcal">{r["macros"][0]} kcal</span></div></a>')
        cards += '</div>'

    body = f"""{nav(0, 'index')}
<section class="hero">
  <div class="wrap">
    <p class="eyebrow">One dinner &middot; the adults, and the toddler</p>
    <h1 class="d">The<br>20&#8209;Minute<br><em>Table</em></h1>
    <p class="lede">{len(recipes)} fast, whole-food recipes for the years when dinner has to happen anyway.
    Nothing over twenty minutes from a cold start, one pan or basket to wash, and every recipe tells you
    how to lift a toddler&rsquo;s portion out of the same pan &mdash; before the salt, before the chilli.</p>
    <div class="stats">
      <div><b class="d">{len(recipes)}</b><span>Recipes</span></div>
      <div><b class="d">{cuisines}</b><span>Cuisines</span></div>
      <div><b class="d">20</b><span>Minutes, max</span></div>
      <div><b class="d">{veg}</b><span>Vegetarian</span></div>
    </div>
  </div>
</section>

<div class="filters" id="filters">
  <div class="wrap">
    <div class="frow">
      <input type="search" id="q" placeholder="Search a dish, a cuisine, an ingredient…" autocomplete="off">
      <button class="chip" data-filter="veg" data-value="1">Vegetarian</button>
      <button class="chip" data-filter="max" data-value="12">Under 12 min</button>
    </div>
    <div class="frow">{sect_chips}</div>
    <div class="frow">{chips}</div>
    <div class="frow ftail"><span id="count"></span>
      <button class="clear" id="clear" hidden>Clear all</button></div>
  </div>
</div>

<main class="wrap" id="results">{cards}
  <p class="empty" id="empty" hidden>Nothing matches that. <button class="clear" data-clear>Clear the filters</button></p>
</main>
{contribute(0)}
{footer(0)}"""
    (SITE / 'index.html').write_text(shell(
        'The 20-Minute Table', body, 0,
        f'{len(recipes)} fast, whole-food recipes for new parents. Twenty minutes, one pan, '
        f'and a toddler portion out of the same pan.'), encoding='utf-8')


# --------------------------------------------------------------- recipe page
def build_recipe(r, prev, nxt):
    m = r['m']
    ings = ''
    for g in r['ing_groups']:
        if g['name']:
            ings += f'<h4 class="ing-h">{inline(g["name"])}</h4>'
        ings += ''.join(
            f'<li><label><input type="checkbox"><span>{inline(x)}</span></label></li>'
            for x in g['items'])
    total = len(r['steps'])
    steps = ''.join(
        f'<li class="step"><button class="sdone" aria-label="Mark step {i+1} done">'
        f'<span class="sglyph">{action_svg(step_glyph(s, i, total), "currentColor", "100%")}</span>'
        f'<span class="snum d">{i+1}</span></button>'
        f'<div class="stext">{inline(s)}</div></li>'
        for i, s in enumerate(r['steps']))
    notes = ''.join(f'<div class="note"><b>{inline(t)}</b><p>{inline(b)}</p></div>'
                    for t, b in r['notes'])
    keys = ['Calories', 'Protein', 'Carbs', 'Fat', 'Fibre']
    units = ['kcal', 'g', 'g', 'g', 'g']
    macs = ''.join(f'<div><b class="d">{v}<i>{u}</i></b><span>{k}</span></div>'
                   for v, k, u in zip(r['macros'], keys, units))
    prep = (f'<span class="dot"></span><span>{r["prep"]} prep · {r["cook"]} cook</span>'
            if r['prep'] else '')
    pair = sides_for(r['num'], BYN) if int(r['num']) <= 50 else (
           mains_for(r['num'], BYN, 6) if int(r['num']) > 85 else [])
    if pair:
        lab = 'Goes with' if int(r['num']) <= 50 else 'Goes next to'
        cards = ''.join(
            f'<a class="gcard" href="{slug(p)}.html" style="--gc:{p["m"]["color"]}">'
            f'<b>{p["num"]}</b><span>{esc(p["title"])}'
            f'<em>{p["minutes"]} min · {p["m"]["label"]}</em></span></a>' for p in pair)
        goes = f'<section class="goeswith"><h2>{lab}</h2><div class="gcards">{cards}</div></section>'
    else:
        goes = ''
    pager = ''
    if prev:
        pager += f'<a class="pg prev" href="{slug(prev)}.html"><span>Previous</span><b>{esc(prev["title"])}</b></a>'
    if nxt:
        pager += f'<a class="pg next" href="{slug(nxt)}.html"><span>Next</span><b>{esc(nxt["title"])}</b></a>'

    body = f"""{nav(1)}
<article class="recipe" style="--c:{m['color']};--t:{m['tint']}">
  <header class="rhero">
    <div class="wrap">
      <div class="rnum d">{r['num']}</div>
      <h1 class="d">{esc(r['title'])}</h1>
      <div class="rmeta">
        <span class="pill">{icon(m['key'],'1em',1.8)}{m['label']}</span>
        <span>{esc(r['cuisine'])}</span><span class="dot"></span>
        <span>Serves {r['serves']}</span>{prep}
        {'<span class="vtag">Vegetarian</span>' if r['veg'] else ''}
        <span class="rtime d">{r['minutes']}<i>min</i></span>
      </div>
      <p class="rhook d">{inline(r['hook'])}</p>
    </div>
  </header>

  <div class="wrap rbody">
    <aside class="ings">
      <h2>Ingredients <button class="mini" id="reset-ings">reset</button></h2>
      <ul class="inglist">{ings}</ul>
      <div class="macros">{macs}</div>
      <p class="wash"><b>Washing up</b> {inline(r['washing'])}</p>
    </aside>
    <div class="main">
      <section class="why"><h2>Why it works</h2><p>{inline(r['why'])}</p></section>
      <section class="method"><h2>Method</h2><ol class="steps">{steps}</ol></section>
      <section class="todbox"><h2>For the toddler</h2><p>{inline(r['toddler'])}</p>
        <a class="todlink" href="../toddlers.html">How the toddler notes work</a></section>
      <section class="notes"><h2>Chef&rsquo;s notes</h2><div class="ngrid">{notes}</div></section>
      {goes}
    </div>
  </div>
  <nav class="pager wrap">{pager}</nav>
</article>
{footer(1)}"""
    (SITE / 'r' / f'{slug(r)}.html').write_text(
        shell(f"{r['title']} — The 20-Minute Table", body, 1, r['hook']), encoding='utf-8')


# ------------------------------------------------------------- the planner
# The page arrives with a week already on it. That is not a placeholder: it is
# a real week chosen by planner.default_week(), which is deterministic, so the
# committed plan.html is the same file every build and CI's check that site/
# matches its sources still passes. With JavaScript off it stays a complete
# week of dinners, each one a link to its recipe.

PLAN_INTRO = (
    'Say how many dinners you want, how many you are feeding, and what the house '
    'eats. This picks that many out of the fifty lunches and dinners in the book, '
    'spreads the protein, the pan and the part of the world they come from, and '
    'adds every ingredient into one list in the order a shop is walked. Swap any '
    'night you do not fancy and the list follows.')


def night_tags(r):
    """The kind of dinner it is, said in the words somebody would use.

    Mirrors nightTags() in web/plan.js. The first tag is what the dish is built
    on — beef, prawns, vegetarian. Any further one is a protein the dish carries
    without being about it, which is exactly what the filter above acts on, so
    it is shown rather than left to surprise anybody.
    """
    veg = r['tg'] == ['veg']
    out = [('<span class="ntag ntag-veg">Vegetarian</span>' if veg
            else f'<span class="ntag">{esc(r["src"])}</span>')]
    extra = {'fish': 'fish', 'shellfish': 'shellfish', 'chicken': 'chicken',
             'redmeat': 'red meat'}
    fam = {'seafood': ('fish', 'shellfish'), 'poultry': ('chicken',),
           'red meat': ('redmeat',)}.get(r['fam'], ())
    for t in r['tg']:
        if t in extra and t not in fam:
            out.append(f'<span class="ntag ntag-also">also {extra[t]}</span>')
    return ''.join(out)


def night_row(r, i, ordinals):
    """One night. Mirrors renderWeek() in web/plan.js exactly."""
    return (
        f'\n      <li class="night" data-num="{r["n"]}" style="--c:{r["col"]}">'
        f'\n        <span class="n-ord">{ordinals[i]}</span>'
        f'\n        <span class="cnum d">{r["n"]}</span>'
        f'\n        <div class="n-body">'
        f'\n          <a class="n-title d" href="r/{r["s"]}.html">{esc(r["t"])}</a>'
        f'\n          <p class="n-tags">{night_tags(r)}</p>'
        f'\n          <p class="n-meta"><span>{esc(r["ml"])}</span><span class="dot"></span>'
        f'\n            <span>{esc(r["c"])}</span><span class="dot"></span>'
        f'\n            <span>{r["pr"]} g protein a serving</span></p>'
        f'\n        </div>'
        f'\n        <span class="cmin d">{r["min"]}<i>min</i></span>'
        f'\n        <div class="n-act"><button class="swap" type="button" data-slot="{i}"'
        f'\n          aria-label="Swap the {ordinals[i].lower()} dinner">Swap</button></div>'
        f'\n      </li>')


def build_plan(recipes):
    data = PLANNER.payload(recipes)
    by = {r['n']: r for r in data['recipes']}
    week = [by[n] for n in data['week']]
    counts = PLANNER.tag_counts(data['recipes'])
    ordinals = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh',
                'Eighth', 'Ninth', 'Tenth']
    words = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
             'nine', 'ten']
    n = len(week)
    serves = data['serves']

    def chips(name, values, current):
        return ''.join(
            f'<label class="chip"><input type="radio" name="{name}" value="{v}"'
            f'{" checked" if v == current else ""}>{v}</label>' for v in values)

    ticks = ''.join(
        f'<label class="chip"><input type="checkbox" name="eat" value="{t}" checked>'
        f'{TAG_LABEL[t]}<i>{counts[t]}</i></label>' for t in DIET_TAGS)

    pans = ''.join(
        f'<label class="chip" style="--c:{m["col"]}">'
        f'<input type="checkbox" name="pan" value="{m["key"]}" checked>'
        f'{m["label"]}<i>{m["n"]}</i></label>'
        for m in PLANNER.method_counts(data['recipes']))

    # Every figure on the band is read straight off the recipes, so the build
    # and the browser can agree on it without the shopping list being worked
    # out twice — once here in Python and once in the browser.
    band = [
        (n, 'Dinners'),
        (sum(r['min'] for r in week), 'Minutes, all in'),
        ('%d g' % round(sum(r['pr'] for r in week) / n), 'Protein a serving, average'),
        ('%d g' % round(sum(r['fb'] for r in week) / n), 'Fibre a serving, average'),
        (serves, 'Serves'),
    ]
    band_html = ''.join(f'<div><b class="d">{v}</b><span>{k}</span></div>'
                        for v, k in band)
    rows = ''.join(night_row(r, i, ordinals) for i, r in enumerate(week))
    blob = json.dumps(data, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).replace('</', r'<\/')

    body = f"""{nav(0, 'plan')}
<section class="phero"><div class="wrap">
  <p class="eyebrow">Decide once &middot; shop once</p>
  <h1 class="d">Pick My Meals<br>for a <em>Week</em></h1>
  <p class="lede">{PLAN_INTRO}</p>
  <p class="pnote">A week is already picked below. Nothing is stored: the week you are
  looking at is in the address bar, so you can bookmark it or send it to whoever is going
  to the shop. <a class="jump" href="#shop">Straight to the list</a></p>
</div></section>

<form class="pctl" id="pctl"><div class="wrap">
  <div class="pctl-row">
    <span class="pctl-k">Dinners</span>
    <div class="pchips pnum" role="group" aria-label="How many dinners">{chips('nights', [3, 4, 5, 6, 7], n)}</div>
    <p class="pctl-h">Most weeks are not seven dinners. Pick the number you will actually
    cook. Picked from the fifty lunches and dinners; breakfasts, puddings and the sides
    stay where they are.</p>
  </div>
  <div class="pctl-row">
    <span class="pctl-k">Serves</span>
    <div class="pchips pnum" role="group" aria-label="How many servings">{chips('serves', [2, 4, 6, 8], serves)}</div>
    <p class="pctl-h">Every recipe in the book is written for four. Another number scales
    the shopping list &mdash; whole things and tins round up, since you cannot buy two
    thirds of a tin, and weights round to the nearest sensible figure. The recipe pages
    still read for four, so halve or double as you cook.</p>
  </div>
  <div class="pctl-row">
    <span class="pctl-k">On the table</span>
    <div class="pchips pticks" role="group" aria-label="What the house eats">{ticks}</div>
    <p class="pctl-h">Untick anything nobody in the house eats. The numbers are how many
    dinners contain each thing, and they add up to more than fifty because some dishes are
    on two lists &mdash; a chicken stir-fry seasoned with fish sauce is chicken and fish,
    and unticking either one drops it. Anchovies melted into oil until they have vanished
    still count; eight of the fifty carry fish only as a seasoning. It is a filter on what
    the recipes list, not an allergen check &mdash; a jar of kimchi or a shop-bought curry
    paste can carry shrimp without the recipe saying so &mdash; so read the ingredients if
    it matters.</p>
  </div>
  <div class="pctl-row">
    <span class="pctl-k">The pan</span>
    <div class="pchips pticks ppans" role="group" aria-label="What you feel like washing up">{pans}</div>
    <p class="pctl-h">Half the dinners in the book are one pan and only four need no heat at all,
    so unticking is quick work &mdash; the counts say how much of the book each one is. Leave them
    all on unless the air fryer is in use or the hob is not.</p>
  </div>
  <div class="pctl-tail">
    <p class="poolline" id="pool">{len(data['recipes'])} of the {len(data['recipes'])} dinners match. Enough for {words[n]}.</p>
    <button class="btn btn-p" id="pick" type="submit">Pick these meals</button>
    <p class="pctl-h">Picking again replaces every night. To change one night, swap it.</p>
    <noscript><p class="pctl-h">The controls need JavaScript. Without it this is still one
    full week, already picked, and every dinner links to its recipe.</p></noscript>
  </div>
</div></form>

<main>
  <div class="wrap">
  <p class="printhead">The 20-Minute Table &mdash; {words[n]} dinners for {words[serves]}</p>
  <div class="statband" id="wkband">{band_html}</div>

  <h2 class="sect d" id="week">The week<span id="wkcount">{words[n].capitalize()} nights</span></h2>
  <ol class="week" id="weeklist">{rows}
  </ol>
  <p class="n-short" id="short" hidden></p>
  <p class="empty" id="plan-empty" hidden>Nothing matches those ticks.
    <button class="clear" id="plan-all" type="button">Allow everything again</button></p>
  <p class="weeknote">Every one of these ends with a note on feeding a toddler. Most lift a
  small portion out of the same pan before the salt and before the chilli; a few say plainly
  that theirs is easier cooked alongside. The note is at the foot of each recipe.</p>

  <h2 class="sect d">What is in this week</h2>
  <div class="spread" id="spread"></div>
  <div class="report" id="report"></div>
  <p class="rdisc">The figures are the estimates printed in each recipe, for a quarter of the
  finished dish. They describe the dinner alone &mdash; not what you put beside it, and not
  the rest of the day &mdash; and they are not dietary advice.</p>

  <h2 class="sect d" id="shop">The shop<span id="shopcount"></span></h2>
  <p class="pnote">One list for the whole week, aisle by aisle, with the amounts added up and
  scaled to the number you are feeding. Ticks last while this page is open. Staples are at the
  foot &mdash; check the <a href="pantry.html">Fast Pantry</a> before you buy them twice.</p>
  <div class="plan-actions">
    <button class="btn btn-p" id="plan-pack" type="button">{DL_ICON}<span>Download the week as a PDF</span></button>
    <button class="btn btn-s" id="plan-pdf" type="button"><span>Shopping list only</span></button>
    <button class="btn btn-s" id="plan-copy" type="button"><span>Copy as text</span></button>
  </div>
  <p class="pctl-h plan-note">The first is the shopping list and then every recipe in full,
  laid out to print &mdash; about {words[n + 2]} sheets of paper, and the week is on the fridge door.
  The second is the list on its own.</p>
  </div>

  <div class="filters gbar" id="gbar"><div class="wrap"><div class="frow ftail">
    <span id="gcount"></span>
    <button class="chip" id="hide-ticked" type="button" aria-pressed="false">Hide what is in the trolley</button>
  </div></div></div>

  <div class="wrap">
  <div class="shelves glist" id="glist"></div>
  <details class="cupboard" id="cupboard" hidden>
    <summary>From the cupboard<span id="cupcount"></span></summary>
    <div id="cuplist"></div>
  </details>
  <noscript><p class="empty">The shopping list is added up in your browser, so it needs
  JavaScript. Every dinner above carries its own ingredients on its recipe page.</p></noscript>
  <p class="vh" id="say" aria-live="polite" role="status"></p>
  </div>
</main>
{contribute(0)}
{footer(0)}
<script>window.PLAN={blob}</script>"""

    (SITE / 'plan.html').write_text(shell(
        'Plan a Week — The 20-Minute Table', body, 0,
        'Pick a week of dinners from the book and get one shopping list, aisle by '
        'aisle, as a PDF you can take to the shop.',
        scripts=('pdf.js', 'plan.js')), encoding='utf-8')


# ---------------------------------------------------------- pantry and about
def build_pantry(shelves, kit, n_recipes):
    cols = ''.join(
        f'<div class="shelf"><h3>{name}</h3><ul>' +
        ''.join(f'<li><label><input type="checkbox"><span>{i}</span></label></li>' for i in items) +
        '</ul></div>' for name, items in shelves)
    kithtml = ''.join(f'<li><label><input type="checkbox"><span>{k}</span></label></li>' for k in kit)
    n = sum(len(i) for _, i in shelves)
    body = f"""{nav(0, 'pantry')}
<section class="phero"><div class="wrap">
  <p class="eyebrow">Before you start · {n} things</p>
  <h1 class="d">The Fast Pantry</h1>
  <p class="lede">Twenty-minute cooking only works when the slow part — the shopping, the searching,
  the standing in front of an open cupboard — has already happened. Tick your way through this once
  and every one of the {n_recipes} recipes becomes a decision rather than a project.</p>
  <p class="pnote">Ticks are kept while this page is open. <button class="mini" id="reset-pantry">Reset</button></p>
</div></section>
<main class="wrap"><div class="shelves">{cols}
  <div class="shelf"><h3>The kit — and nothing else</h3><ul>{kithtml}</ul></div>
</div></main>
{footer(0)}"""
    (SITE / 'pantry.html').write_text(shell('The Fast Pantry — The 20-Minute Table', body, 0,
        'The shopping list that makes twenty-minute cooking possible.'), encoding='utf-8')


def build_toddlers(recipes):
    pts = ''.join(f'<div class="tcard"><h3>{t}</h3><p>{b}</p></div>' for t, b in TOD_POINTS)
    body = f"""{nav(0, 'toddlers')}
<section class="phero"><div class="wrap">
  <p class="eyebrow">One dinner, two eaters</p>
  <h1 class="d">Cooking for a Toddler</h1>
  <p class="lede">{TOD_INTRO}</p>
</div></section>
<main class="wrap">
  <div class="tgrid">{pts}</div>
  <p class="disclaimer">{TOD_DISC}</p>
</main>
{footer(0)}"""
    (SITE / 'toddlers.html').write_text(shell('Cooking for a Toddler — The 20-Minute Table',
        body, 0, "How to get a toddler's portion out of the same pan."), encoding='utf-8')


def build_about(recipes, rules):
    counts = Counter(r['method'] for r in recipes)
    rl = ''.join(f'<li><b>{t}</b> {b}</li>' for t, b in rules)
    n = pdf_pages()
    pages = f' {n}-page' if n else ''
    why_paras = ''.join(
        '<p>' + p.replace(REPO_TEXT, f'<a href="{GH_URL}">{REPO_TEXT}</a>') + '</p>'
        for p in MISSION.paras(REPO_TEXT))
    body = f"""{nav(0, 'about')}
<section class="phero"><div class="wrap">
  <p class="eyebrow">A short note first</p>
  <h1 class="d">Twenty Minutes Is Plenty</h1>
  <div class="prose">
    <p class="lede">This book was written for the stretch of life when dinner has to happen anyway.
    There is a small person who needs feeding at six, an adult who has not eaten properly since
    breakfast, and about twenty minutes between the two.</p>
    <p>Most of what makes cooking slow has nothing to do with cooking. It is the deciding, the shopping,
    the hunting for a jar of something at the back of a cupboard, and the washing up that follows.
    Those are the parts a new parent has least of, so those are the parts this book removes — not the
    cooking. Nothing here is a shortcut version of a longer dish. These are dishes that were always
    fast, drawn from the kitchens where speed is not a compromise but the whole tradition. You are not
    being handed a lesser dinner because you have a baby.</p>
    <p>Everything is built on whole ingredients, which is less an ideology than a practical matter: they
    cook faster than you think, they taste of what they are, and they let you season a dish rather than
    negotiate with something already seasoned for you. Every recipe was written to leave one pan or one
    basket behind, and the washing-up line at the foot of each page is the constraint it was designed
    around. Every one also ends by telling you how to get a toddler&rsquo;s portion out of that same pan.</p>
  </div>
</div></section>
<main class="wrap">
  <div class="statband">
    <div><b class="d">{len(recipes)}</b><span>Recipes</span></div>
    <div><b class="d">{counts['Air fryer']}</b><span>Air fryer</span></div>
    <div><b class="d">{counts['One pan'] + counts['Wok']}</b><span>Pan or wok</span></div>
    <div><b class="d">{counts['No cook']}</b><span>No heat at all</span></div>
    <div><b class="d">{sum(1 for r in recipes if r['veg'])}</b><span>Vegetarian</span></div>
  </div>
  <div class="whyw">
    <p class="eyebrow">{MISSION.KICKER}</p>
    <h2 class="whyw-t d">{' '.join(MISSION.HEADING_LINES)}</h2>
    <div class="whyw-body">{why_paras}</div>
  </div>
  <h2 class="sect d">Ten rules for a twenty-minute dinner</h2>
  <ol class="rules">{rl}</ol>
  <h2 class="sect d">Ways to get it</h2>
  <div class="eds">
    <div class="ed">
      <p class="ed-k">Free, from here</p>
      <a class="ed-a" href="{PDF_NAME}" download>
        <b>PDF</b><span>The{pages} book as it prints, laid out in spreads</span></a>
      <a class="ed-a" href="{EPUB_NAME}" download>
        <b>EPUB</b><span>Reflowable, for a phone or an e-reader</span></a>
    </div>
    <div class="ed">
      <p class="ed-k">In print, on Amazon</p>
      <a class="ed-a" href="{IMP.amazon_url('paperback')}">
        <b>Paperback <i>${IMP.LIST_USD['paperback']:.2f}</i></b>
        <span>Softcover, colour throughout</span></a>
      <a class="ed-a" href="{IMP.amazon_url('hardback')}">
        <b>Hardcover <i>${IMP.LIST_USD['hardback']:.2f}</i></b>
        <span>Printed case, no jacket, premium colour</span></a>
      <a class="ed-a" href="{IMP.amazon_url('kindle')}">
        <b>Kindle <i>${IMP.KINDLE_LIST_USD:.2f}</i></b>
        <span>The same book, on the Kindle app or device</span></a>
    </div>
  </div>
  <p class="dl">The files are free and will stay that way. Buying a copy is for having it
    on the shelf, and it keeps the project going.</p>
</main>
{contribute(0)}
{footer(0)}"""
    (SITE / 'about.html').write_text(shell('About — The 20-Minute Table', body, 0,
        'Why these recipes are fast, and what the book is built on.'), encoding='utf-8')


BYN = {}


def main():
    global BYN
    recipes = load_all()
    BYN = {r['num']: r for r in recipes}

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / 'r').mkdir(parents=True)
    ASSETS.mkdir(parents=True)

    (ASSETS / 'style.css').write_text(
        fonts_css() + '\n' +
        (HERE / 'web' / 'style.css').read_text(encoding='utf-8'),
        encoding='utf-8')
    for js in ('app.js', 'pdf.js', 'plan.js'):
        shutil.copy(HERE / 'web' / js, ASSETS / js)

    # The recipes in full, for the printable pack. It is twice the size of
    # everything else the planner needs, and only somebody who asks for the
    # recipes ever loads it, so it is a script the page fetches on demand
    # rather than another 180 kB in every visit. A script rather than JSON so
    # it works from a file:// copy of the site as well as from a server.
    pack = json.dumps(PLANNER.recipe_pack(recipes), sort_keys=True,
                      separators=(',', ':'), ensure_ascii=False)
    (ASSETS / 'recipes.js').write_text('window.PLAN_RECIPES=' + pack,
                                       encoding='utf-8')

    if PDF_SRC.exists():
        shutil.copy(PDF_SRC, SITE / PDF_NAME)
    if EPUB_SRC.exists():
        shutil.copy(EPUB_SRC, SITE / EPUB_NAME)

    build_index(recipes)
    for i, r in enumerate(recipes):
        build_recipe(r, recipes[i - 1] if i else None,
                     recipes[i + 1] if i + 1 < len(recipes) else None)

    build_plan(recipes)
    build_pantry(SHELVES, KIT, len(recipes))
    build_toddlers(recipes)
    build_about(recipes, RULES)

    files = list(SITE.rglob('*'))
    size = sum(f.stat().st_size for f in files if f.is_file())
    print(f'site: {sum(1 for f in files if f.suffix == ".html")} pages, '
          f'{round(size/1e6, 2)} MB in {SITE}')


if __name__ == '__main__':
    main()
