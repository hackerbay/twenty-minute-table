"""Build the covers.

Three separate artefacts, sharing only the artwork:

  paperback  a single full-wrap PDF — back cover, spine, front cover, with bleed
             on all four sides. Rendered as vector through the same Chromium
             pipeline as the interior, so the type stays crisp.
  kindle     a front-cover raster, 2560x1600, RGB JPEG.
  hardback   NOT generated here. KDP publishes no hardcover case formula and
             defers to its own cover calculator; the case is materially larger
             than the paperback wrap in both axes because the sheet wraps a
             board that overhangs the text block, plus two hinge channels. Any
             formula short of the calculator's template is guesswork, so this
             prints the numbers you need to feed it instead of inventing a size.

Spine width comes from the real page count in the built interior, not a constant,
because it changes whenever the book does — and from the interior KDP prints it
on, because standard and premium colour are different thicknesses of paper.
"""
import asyncio, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'art'))

from parse import load_all
import build as B
import imprint as IMP
from flatten import mix

BLEED = 0.125          # inches, all four sides on a cover
TRIM_W, TRIM_H = 8.25, 11.0

# Inches of spine per page. KDP publishes one multiplier per interior stock:
#
#   "Standard Color paper: page count x 0.002252" (0.0572 mm)"
#   "Premium Color paper: page count x 0.002347" (0.0596 mm)"
#
# — Create a Paperback Cover, https://kdp.amazon.com/en_US/help/topic/G201953020,
# read 2026-09-01, and confirmed against the Cover Calculator the same day: at
# 8.25x11, 224 pages, paperback, standard colour, white paper it returns a
# 0.504in spine and a 17.254in wrap, which is what the figures below give.
#
# KDP's older Paperback Submission Guidelines page still lumps every colour book
# together as "Color paper: page count x 0.002347"". That row predates the
# standard/premium split and is wrong for a standard-colour interior — see
# docs/kdp-publishing-spec.md §5.1.
SPINE_PER_PAGE = {
    'standard colour': 0.002252,   # what the paperback is printed on
    'premium colour':  0.002347,   # hardback only today, and that uses HC below
}

SAFE = 0.25            # inches: keep all type this far inside the trim

# Hardcover case, read from KDP's Cover Calculator on 2026-08-31 for
# 8.25x11, 224 pages, premium colour, white paper, left-to-right. KDP publishes
# no formula for this, so these are measured values rather than derived ones —
# regenerate them if the page count changes.
#
# The case is bigger than the text block: the printed sheet wraps a board that
# overhangs the pages and turns in to be glued down. Checks out to a thousandth:
# 2*front + spine + 2*wrap = 18.791, and front height + 2*wrap = 12.418.
HC = {
    'pages': 224,
    'sheet_w': 18.79, 'sheet_h': 12.417,
    'panel_w': 8.447, 'panel_h': 11.236,
    'spine': 0.715,      # far wider than the paperback's 0.504
    'wrap': 0.591,       # turn-in: nothing here survives on the visible face
    'hinge': 0.394,      # channel either side of the spine — type creases in it
    'margin': 0.125,
}

PDF = ROOT / 'dist' / 'The-20-Minute-Table.pdf'
INK = '#1B201D'


SAFE_AREA_JS = '''() => {
  const IN = 96, sheet = document.querySelector('.sheet');
  const s = sheet.getBoundingClientRect(), out = [];
  sheet.querySelectorAll('*').forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    if (e.children.length) return;            // measure leaves, not wrappers
    if (!e.textContent.trim()) return;        // ignore spacers and rules
    out.push({cls: String(e.className).slice(0, 26),
              l: (r.left - s.left) / IN, t: (r.top - s.top) / IN,
              r: (s.right - r.right) / IN, b: (s.bottom - r.bottom) / IN});
  });
  return out;
}'''

def page_count():
    if not PDF.exists():
        sys.exit('cover: build the interior first (make book)')
    return len(re.findall(rb'/Type\s*/Page[^s]', PDF.read_bytes()))


def geometry(pages):
    """The paperback wrap. Its spine depends on the interior KDP will print it on."""
    if IMP.INK_CHOICE not in SPINE_PER_PAGE:
        sys.exit(f'cover: no KDP spine multiplier for a {IMP.INK_CHOICE!r} interior')
    spine = pages * SPINE_PER_PAGE[IMP.INK_CHOICE]
    return {
        'pages': pages,
        'spine': spine,
        'width': 2 * BLEED + 2 * TRIM_W + spine,
        'height': 2 * BLEED + TRIM_H,
    }



def back_panel_html(recipes):
    """The back-cover copy. Shared by the paperback wrap and the hardback case."""
    veg = sum(1 for r in recipes if r['veg'])
    cuisines = len({r['cuisine'] for r in recipes})
    return f"""
    <div class="inner">
      <p class="bk-k">One dinner &nbsp;&middot;&nbsp; the adults, and the toddler</p>
      <h2 class="bk-h d">Dinner has to happen<br><em>anyway.</em></h2>
      <p class="bk-p">{len(recipes)} recipes for the stretch of life when there is a small person
      who needs feeding at six, an adult who has not eaten properly since breakfast, and about
      twenty minutes between the two.</p>
      <p class="bk-p">Nothing takes over twenty minutes from a cold start. Everything is built on
      whole ingredients. Every recipe leaves one pan or one basket behind &mdash; and ends by
      telling you how to lift a toddler&rsquo;s portion out of that same pan, before the salt and
      before the chilli.</p>
      <div class="bk-rule"></div>
      <div class="bk-list">
        <div><b>{len(recipes)}</b> recipes</div><div><b>{cuisines}</b> cuisines</div>
        <div><b>20</b> minutes, maximum</div><div><b>{veg}</b> vegetarian</div>
        <div><b>1</b> pan or basket</div><div><b>4</b> servings throughout</div>
      </div>
      <p class="bk-os"><b>The whole book is open source.</b> Every recipe, and the
      software that typesets them into this book, is published under an open licence at
      {IMP.REPO}. Take it, change it, translate it, print it. We would rather eating well
      did not depend on having time, money, or anybody&rsquo;s permission.</p>
      <div class="bk-foot"><span>{IMP.SITE}</span><span>{IMP.PUBLISHER_SITE}</span></div>
    </div>
    <div class="barcode"></div>"""


def wrap_html(recipes, g):
    front = B.cover_front_html(recipes)
    veg = sum(1 for r in recipes if r['veg'])
    cuisines = len({r['cuisine'] for r in recipes})
    blurb_rule = mix('#FDFAF4', INK, .28)
    faint = mix('#FDFAF4', INK, .55)
    mid = mix('#FDFAF4', INK, .74)

    css = f"""
    @page{{size:{g['width']}in {g['height']}in;margin:0}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    html,body{{background:{INK}}}
    .sheet{{position:relative;width:{g['width']}in;height:{g['height']}in;
      background:{INK};color:#FDFAF4;overflow:hidden}}
    .panel{{position:absolute;top:0;height:{g['height']}in}}
    .back {{left:0;width:{BLEED + TRIM_W}in}}
    .spine{{left:{BLEED + TRIM_W}in;width:{g['spine']}in}}
    .front{{left:{BLEED + TRIM_W + g['spine']}in;width:{TRIM_W + BLEED}in}}
    /* the front panel reuses the book's own cover markup and stylesheet */
    .front .inner{{position:absolute;inset:0;
      padding:{BLEED + 0.55}in {BLEED + 0.62}in {BLEED + 0.5}in 0.62in;
      display:flex;flex-direction:column}}
    .back .inner{{position:absolute;inset:0;
      padding:{BLEED + 0.72}in 0.62in {BLEED + 0.5}in {BLEED + 0.62}in;
      display:flex;flex-direction:column}}
    .bk-k{{font-size:8.2pt;letter-spacing:.24em;text-transform:uppercase;
      font-weight:600;color:#E8A87C}}
    .bk-h{{font-size:27pt;line-height:1.1;font-weight:600;letter-spacing:-.02em;margin-top:5mm}}
    .bk-h em{{font-style:italic;color:#E8A87C}}
    .bk-p{{font-size:11pt;line-height:1.62;color:{mid};margin-top:6mm;max-width:104mm}}
    .bk-rule{{height:1px;background:{blurb_rule};margin:8mm 0}}
    .bk-list{{display:grid;grid-template-columns:1fr 1fr;gap:2.6mm 8mm;font-size:9.6pt;
      color:{mid}}}
    .bk-list b{{color:#E8A87C;font-weight:600}}
    .bk-os{{margin-top:9mm;padding-top:6mm;border-top:1px solid {blurb_rule};
      font-size:9.4pt;line-height:1.6;color:{mid};max-width:104mm}}
    .bk-os b{{color:#E8A87C;font-weight:600}}
    .bk-foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
      font-size:8pt;letter-spacing:.14em;text-transform:uppercase;color:{faint}}}
    /* KDP prints the barcode over the lower right of the back cover: keep it clear */
    .barcode{{position:absolute;right:{BLEED + SAFE}in;bottom:{BLEED + SAFE}in;
      width:2in;height:1.2in}}
    .spine-txt{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(90deg);
      transform-origin:center;white-space:nowrap;display:flex;align-items:baseline;gap:7mm;
      font-size:12pt;letter-spacing:.06em}}
    .spine-txt .t{{font-family:'Fraunces',Georgia,serif;font-weight:600}}
    .spine-txt .a{{font-size:9.4pt;color:{mid};letter-spacing:.16em;text-transform:uppercase}}
    """

    spine_txt = (f'<div class="spine-txt"><span class="t d">{IMP.TITLE}</span>'
                 f'<span class="a">{IMP.AUTHOR}</span></div>') if g['spine'] >= 0.0625 else ''

    back = back_panel_html(recipes)

    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<style>{B.FONTS}{B.CSS}{css}</style></head><body>'
            f'<div class="sheet">'
            f'<div class="panel back cover">{back}</div>'
            f'<div class="panel spine">{spine_txt}</div>'
            f'<div class="panel front cover"><div class="inner">{front}</div></div>'
            f'</div></body></html>')



def hardback_html(recipes):
    """The hardback case: one sheet wrapping board, hinges and all.

    Panels left to right for a left-to-right book: turn-in, back cover, spine,
    front cover, turn-in. Nothing in the turn-in survives on the visible face, and
    type in a hinge channel gets creased, so both are treated as dead space.
    """
    h = HC
    front = B.cover_front_html(recipes)
    back = back_panel_html(recipes)
    blurb_rule = mix('#FDFAF4', INK, .28)
    faint = mix('#FDFAF4', INK, .55)
    mid = mix('#FDFAF4', INK, .74)

    back_x = h['wrap']
    spine_x = back_x + h['panel_w']
    front_x = spine_x + h['spine']
    outer_pad = h['wrap'] + 0.5          # clear of the turn-in
    vert_pad = h['wrap'] + 0.55
    hinge_pad = h['hinge'] + 0.25        # clear of the hinge channel

    css = f"""
    @page{{size:{h['sheet_w']}in {h['sheet_h']}in;margin:0}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    html,body{{background:{INK}}}
    .sheet{{position:relative;width:{h['sheet_w']}in;height:{h['sheet_h']}in;
      background:{INK};color:#FDFAF4;overflow:hidden}}
    .panel{{position:absolute;top:0;height:{h['sheet_h']}in}}
    .back {{left:0;width:{spine_x}in}}
    .spine{{left:{spine_x}in;width:{h['spine']}in}}
    .front{{left:{front_x}in;width:{h['sheet_w'] - front_x}in}}
    .front .inner{{position:absolute;inset:0;
      padding:{vert_pad + 0.05}in {outer_pad}in {vert_pad}in {hinge_pad}in;
      display:flex;flex-direction:column}}
    .back .inner{{position:absolute;inset:0;
      padding:{vert_pad + 0.2}in {hinge_pad}in {vert_pad}in {outer_pad}in;
      display:flex;flex-direction:column}}
    .bk-k{{font-size:8.2pt;letter-spacing:.24em;text-transform:uppercase;
      font-weight:600;color:#E8A87C}}
    .bk-h{{font-size:27pt;line-height:1.1;font-weight:600;letter-spacing:-.02em;margin-top:5mm}}
    .bk-h em{{font-style:italic;color:#E8A87C}}
    .bk-p{{font-size:11pt;line-height:1.62;color:{mid};margin-top:6mm;max-width:104mm}}
    .bk-rule{{height:1px;background:{blurb_rule};margin:8mm 0}}
    .bk-list{{display:grid;grid-template-columns:1fr 1fr;gap:2.6mm 8mm;font-size:9.6pt;
      color:{mid}}}
    .bk-list b{{color:#E8A87C;font-weight:600}}
    .bk-os{{margin-top:9mm;padding-top:6mm;border-top:1px solid {blurb_rule};
      font-size:9.4pt;line-height:1.6;color:{mid};max-width:104mm}}
    .bk-os b{{color:#E8A87C;font-weight:600}}
    .bk-foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
      font-size:8pt;letter-spacing:.14em;text-transform:uppercase;color:{faint}}}
    .barcode{{position:absolute;right:{outer_pad}in;bottom:{vert_pad}in;width:2in;height:1.2in}}
    .spine-txt{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(90deg);
      transform-origin:center;white-space:nowrap;display:flex;align-items:baseline;gap:9mm;
      font-size:15pt;letter-spacing:.06em}}
    .spine-txt .t{{font-family:'Fraunces',Georgia,serif;font-weight:600}}
    .spine-txt .a{{font-size:11pt;color:{mid};letter-spacing:.16em;text-transform:uppercase}}
    """
    spine_txt = (f'<div class="spine-txt"><span class="t d">{IMP.TITLE}</span>'
                 f'<span class="a">{IMP.AUTHOR}</span></div>')
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<style>{B.FONTS}{B.CSS}{css}</style></head><body>'
            f'<div class="sheet">'
            f'<div class="panel back cover">{back}</div>'
            f'<div class="panel spine">{spine_txt}</div>'
            f'<div class="panel front cover"><div class="inner">{front}</div></div>'
            f'</div></body></html>')


async def render(html, out_pdf, g, safe=None, label='cover'):
    """Render a cover sheet to PDF.

    `safe['edges']` is (left, top, right, bottom) in inches: the margin every piece
    of type must stay inside. On the hardback that is the turn-in, which is glued
    down out of sight; on the paperback it is the bleed plus KDP's 0.25in rule.
    `safe['keepout']` is a list of (x0, x1) bands measured from the left of the
    sheet — the hardback's hinge channels, where type would be creased.

    Measured from the live layout rather than the finished PDF, so it needs no
    rasteriser and fails before a bad cover is ever written.
    """
    from playwright.async_api import async_playwright
    src = ROOT / 'build' / (label + '.html')
    src.write_text(html, encoding='utf-8')
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--font-render-hinting=none'])
        pg = await b.new_page(viewport={'width': 1600, 'height': 1100})
        await pg.goto(src.as_uri(), wait_until='networkidle')
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(1200)
        if safe:
            els = await pg.evaluate(SAFE_AREA_JS)
            L, T, R, B = safe['edges']
            viol = [(e, 'outside the safe margin') for e in els
                    if e['l'] < L - 0.01 or e['t'] < T - 0.01
                    or e['r'] < R - 0.01 or e['b'] < B - 0.01]
            sheet_w = g['width']
            for x0, x1 in safe.get('keepout', []):
                for e in els:
                    left, right = e['l'], sheet_w - e['r']
                    if left < x1 - 0.01 and right > x0 + 0.01:
                        viol.append((e, f'in the hinge channel {x0:.3f}-{x1:.3f}in'))
            if viol:
                print(f'  {label}: TYPE OUTSIDE THE SAFE AREA, {len(viol)} element(s):')
                for e, why in viol[:6]:
                    print(f"    .{e['cls']:<26} l {e['l']:.3f} t {e['t']:.3f} "
                          f"r {e['r']:.3f} b {e['b']:.3f} in — {why}")
                await b.close()
                raise SystemExit(1)

        await pg.pdf(path=str(out_pdf), print_background=True,
                     margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
                     prefer_css_page_size=True)
        await b.close()


async def render_kindle(recipes, out_jpg):
    """Front cover only: 2560x1600, RGB, no bleed, no spine."""
    from playwright.async_api import async_playwright
    front = B.cover_front_html(recipes)
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{B.FONTS}{B.CSS}'
            f'*{{margin:0;padding:0;box-sizing:border-box}}'
            f'html,body{{background:{INK}}}'
            f'.kc{{width:1600px;height:2560px;position:relative;background:{INK};color:#FDFAF4}}'
            f'.kc .inner{{position:absolute;inset:0;padding:120px 104px 104px;'
            f'display:flex;flex-direction:column}}'
            # A store cover is read as a thumbnail, so the dozen-recipe menu that
            # works on a printed jacket becomes unreadable noise. Drop it and let
            # the title, the promise and the numbers carry the whole cover.
            f'.kc .menu-k,.kc .menu{{display:none}}'
            f'.kc h1{{font-size:172pt;margin-top:0}}'
            f'.kc .cover-sub{{font-size:30pt;max-width:none;margin-top:52px}}'
            f'.kc .promise p{{font-size:34pt;line-height:1.62}}'
            f'.kc .stats{{margin-top:20px}}'
            f'.kc .stat{{padding:40px 28px 34px}}'
            f'.kc .stat .sv{{font-size:62pt}}.kc .stat .sl{{font-size:15pt}}'
            f'.kc .cover-foot{{font-size:17pt}}'
            f'.kc .cover-rule{{height:2px}}'
            f'</style></head><body>'
            f'<div class="kc cover"><div class="inner">{front}</div></div></body></html>')
    src = ROOT / 'build' / 'cover-kindle.html'
    src.write_text(html, encoding='utf-8')
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--font-render-hinting=none'])
        pg = await b.new_page(viewport={'width': 1600, 'height': 2560})
        await pg.goto(src.as_uri(), wait_until='networkidle')
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(1200)
        await pg.locator('.kc').screenshot(path=str(out_jpg), type='jpeg', quality=92)
        await b.close()


def main():
    recipes = load_all()
    g = geometry(page_count())
    (ROOT / 'build').mkdir(exist_ok=True)
    (ROOT / 'dist').mkdir(exist_ok=True)

    pb = ROOT / 'dist' / 'cover-paperback.pdf'
    asyncio.run(render(wrap_html(recipes, g), pb, g,
                       safe={'edges': (BLEED + SAFE,) * 4}, label='cover-paperback'))

    hb = ROOT / 'dist' / 'cover-hardback.pdf'
    if g['pages'] != HC['pages']:
        sys.exit(f"cover: the hardback case was measured at {HC['pages']} pages but the book is "
                 f"now {g['pages']}. Regenerate it from KDP's Cover Calculator and update HC.")
    spine_l = HC['wrap'] + HC['panel_w']
    spine_r = spine_l + HC['spine']
    asyncio.run(render(hardback_html(recipes), hb,
                       {'width': HC['sheet_w'], 'height': HC['sheet_h']},
                       safe={'edges': (HC['wrap'],) * 4,
                             'keepout': [(spine_l - HC['hinge'], spine_l),
                                         (spine_r, spine_r + HC['hinge'])]},
                       label='cover-hardback'))

    kc = ROOT / 'dist' / 'cover-kindle.jpg'
    asyncio.run(render_kindle(recipes, kc))

    print(f"cover: {g['pages']} pages -> spine {g['spine']:.4f}in ({g['spine']*25.4:.2f}mm)")
    print(f"       paperback wrap {g['width']:.4f} x {g['height']:.4f}in -> {pb.name} "
          f"({pb.stat().st_size/1e6:.2f} MB)")
    print(f"       kindle front 1600x2560 -> {kc.name} ({kc.stat().st_size/1e6:.2f} MB)")
    print(f"       hardback case {HC['sheet_w']} x {HC['sheet_h']}in, spine {HC['spine']}in "
          f"-> {hb.name} ({hb.stat().st_size/1e6:.2f} MB)")
    print()
    print("hardback case dimensions came from KDP's Cover Calculator, measured at")
    print(f"          8.25x11, {HC['pages']} pages, premium colour. Re-measure if the page")
    print("          count changes — the build refuses to guess.")


if __name__ == '__main__':
    main()
