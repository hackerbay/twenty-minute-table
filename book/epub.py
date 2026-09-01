"""Build the Kindle edition: a reflowable EPUB3, generated from recipes/*.md.

Reflowable rather than fixed-layout, because most Kindle reading happens on a
phone. An 8.25x11 page scaled to a ~6in screen puts this book's body text well
under the 2mm cap height KDP requires of fixed-layout, and fixed-layout also
gives up user font settings and screen-reader support — a real loss for a book
read hands-free in a kitchen.

That means the print design does not survive, and should not be faked: the
full-bleed colour bars, the two-page spread and the vertical justification are
print production, not content. What carries over is the structure — title,
meta, why it works, ingredients, method, notes, the toddler portion — as
semantic XHTML the reader restyles at will.

Built from parse.py, never from build/cookbook.html, which is print geometry.
"""
import asyncio, html, io, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'art'))

from parse import load_all, inline
from compose import hero_svg
from version import VERSION
import imprint as IMP

OUT = ROOT / 'dist' / 'The-20-Minute-Table.epub'
IMG_W = 1200          # px; KDP wants pictorial images to fill >=60% of screen width
JPEG_Q = 78           # flat vector art compresses hard; watch the total in the report

XHTML = ('<?xml version="1.0" encoding="utf-8"?>\n'
         '<!DOCTYPE html>\n'
         '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
         'lang="en" xml:lang="en">\n<head><meta charset="utf-8"/><title>{title}</title>'
         '<link rel="stylesheet" type="text/css" href="{up}style.css"/></head>\n'
         '<body>\n{body}\n</body>\n</html>\n')


def esc(s):
    # resolve any named entity to its character before escaping: XHTML served as
    # XML defines only &amp; &lt; &gt; &quot; &apos;
    return html.escape(html.unescape(str(s)), quote=False)


def rich(s):
    """inline() already escapes &, < and > and emits only <strong>/<em>, so it must
    not be given pre-escaped text. XML has no named entities beyond the big five,
    so anything arriving as one is resolved to its character first."""
    out = inline(html.unescape(str(s)))
    return out.replace('<br>', '<br/>')


CSS = """/* Reflowable: never set an absolute body size, and set the family on body only.
   Kindle's defaults differ from a browser's, so headings state their alignment. */
body { font-family: serif; font-size: 1em; line-height: 1.5; margin: 0 5%; }
h1, h2, h3 { font-family: sans-serif; text-align: left; page-break-after: avoid; }
h1 { font-size: 1.5em; line-height: 1.25; margin: 1em 0 0.2em; }
h2 { font-size: 1.1em; margin: 1.6em 0 0.4em; text-transform: uppercase;
     letter-spacing: 0.08em; }
h3 { font-size: 1em; margin: 1.2em 0 0.3em; }
p { margin: 0 0 0.8em; text-indent: 0; }
.meta { font-family: sans-serif; font-size: 0.85em; margin: 0 0 1em; }
.hook { font-style: italic; margin: 0 0 1.2em; }
.hero { text-align: center; margin: 0 0 1.2em; }
.hero img { width: 100%; max-width: 100%; height: auto; }
ul, ol { margin: 0 0 1em 1.2em; padding: 0; }
li { margin: 0 0 0.45em; }
.group { font-family: sans-serif; font-size: 0.85em; text-transform: uppercase;
         letter-spacing: 0.08em; margin: 0.9em 0 0.3em; }
.toddler { border-top: 1px solid #999; border-bottom: 1px solid #999;
           padding: 0.8em 0; margin: 1.4em 0; }
.nutrition { font-family: sans-serif; font-size: 0.85em; }
.washing { font-size: 0.9em; font-style: italic; }
.note b { font-family: sans-serif; }
.toc-sec { font-family: sans-serif; text-transform: uppercase; letter-spacing: 0.08em;
           margin: 1.4em 0 0.4em; }
nav ol { list-style: none; margin-left: 0; }
.front { margin-top: 2em; }
.small { font-size: 0.82em; }
"""


def recipe_xhtml(r, img_name):
    veg = ' &#183; Vegetarian' if r['veg'] else ''
    ings = ''
    for g in r['ing_groups']:
        if g['name']:
            ings += f'<p class="group">{esc(g["name"])}</p>\n'
        ings += '<ul>\n' + ''.join(f'<li>{rich(x)}</li>\n' for x in g['items']) + '</ul>\n'
    steps = '<ol>\n' + ''.join(f'<li>{rich(s)}</li>\n' for s in r['steps']) + '</ol>\n'
    notes = ''.join(f'<p class="note"><b>{esc(t)}:</b> {rich(b)}</p>\n' for t, b in r['notes'])
    k, pr, ca, fa, fb = r['macros']
    body = f"""<h1>{esc(r['title'])}</h1>
<p class="meta">{esc(r['cuisine'])} &#183; {esc(r['method'])} &#183; {esc(r['time'])}
 &#183; Serves {esc(r['serves'])}{veg}</p>
<div class="hero"><img src="../img/{img_name}" alt="An illustration of {esc(r['title'])}"/></div>
<p class="hook">{rich(r['hook'])}</p>
<h2>Why it works</h2>
<p>{rich(r['why'])}</p>
<h2>Ingredients</h2>
{ings}<h2>Method</h2>
{steps}<h2>Chef&#8217;s notes</h2>
{notes}<div class="toddler">
<h3>For the toddler</h3>
<p>{rich(r['toddler'])}</p>
</div>
<h2>Nutrition</h2>
<p class="nutrition">Per serving, approximate: {esc(k)} kcal &#183; protein {esc(pr)} g
 &#183; carbs {esc(ca)} g &#183; fat {esc(fa)} g &#183; fibre {esc(fb)} g</p>
<p class="washing">Washing up: {rich(r['washing'])}</p>"""
    return XHTML.format(title=esc(r['title']), up='../', body=body)


SECTIONS = [('Lunch &#38; Dinner', 1, 50), ('Breakfast', 51, 70),
            ('Something Afterwards', 71, 85), ('On the Side', 86, 100)]


def section_of(num):
    n = int(num)
    for name, lo, hi in SECTIONS:
        if lo <= n <= hi:
            return name
    return 'Recipes'


async def render_images(recipes, dest):
    """Rasterise each hero illustration. Kindle's converter does not handle SVG
    reliably, and KDP forbids transparency in EPUB images."""
    from playwright.async_api import async_playwright
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': IMG_W, 'height': int(IMG_W * 0.62)})
        for r in recipes:
            svg = hero_svg(r, r['m']['color'], r['m']['tint'])
            await pg.set_content(
                f'<style>html,body{{margin:0;background:#FFF}}'
                f'#h{{width:{IMG_W}px;height:{int(IMG_W*0.62)}px;overflow:hidden}}'
                f'#h svg{{width:100%;height:100%;display:block}}</style>'
                f'<div id="h">{svg}</div>')
            name = f"{r['num']}.jpg"
            await pg.locator('#h').screenshot(path=str(dest / name), type='jpeg', quality=JPEG_Q)
            out[r['num']] = name
        await b.close()
    return out


def build():
    recipes = load_all()
    tmp = ROOT / 'build' / 'epub'
    img_dir = tmp / 'img'
    imgs = asyncio.run(render_images(recipes, img_dir))

    cover_jpg = ROOT / 'dist' / 'cover-kindle.jpg'
    if not cover_jpg.exists():
        sys.exit('epub: build the covers first (make covers)')

    files = {}   # archive path -> bytes

    # ---- front matter -------------------------------------------------------
    files['OEBPS/cover.xhtml'] = XHTML.format(
        title='Cover', up='', body='<div class="hero"><img src="img/cover.jpg" '
        f'alt="{esc(IMP.TITLE)}"/></div>').encode()

    files['OEBPS/titlepage.xhtml'] = XHTML.format(
        title=esc(IMP.TITLE), up='',
        body=(f'<div class="front"><h1>{esc(IMP.TITLE)}</h1>'
              f'<p>{esc(IMP.SUBTITLE)}</p><p>{esc(IMP.AUTHOR)}</p>'
              f'<p class="small">{esc(IMP.PUBLISHER)} &#183; {esc(IMP.PUBLISHER_SITE)}</p>'
              f'<p class="small">{esc(IMP.SITE)}</p></div>')).encode()

    files['OEBPS/copyright.xhtml'] = XHTML.format(
        title='Copyright', up='',
        body=('<div class="front small">'
              f'<p>Copyright &#169; {IMP.YEAR} {esc(IMP.AUTHOR)}</p>'
              f'<p>Published by {esc(IMP.PUBLISHER)}, {esc(IMP.PUBLISHER_SITE)}</p>'
              f'<p>{esc(IMP.LICENCE)}</p><p>{esc(IMP.MORAL_RIGHTS)}</p>'
              f'<p>{esc(IMP.EDITION)}, {IMP.YEAR}. Version {VERSION}.</p>'
              f'<p>{IMP.DISCLAIMER}</p><p>{esc(IMP.SITE)}</p></div>')).encode()

    # ---- recipes ------------------------------------------------------------
    for r in recipes:
        files[f"OEBPS/r/{r['num']}.xhtml"] = recipe_xhtml(r, imgs[r['num']]).encode()
    for num, name in imgs.items():
        files[f'OEBPS/img/{name}'] = (img_dir / name).read_bytes()
    files['OEBPS/img/cover.jpg'] = cover_jpg.read_bytes()
    files['OEBPS/style.css'] = CSS.encode()

    # ---- navigation ---------------------------------------------------------
    # Two levels at most: section, then recipe. Deeper nesting is the single most
    # common reason a Kindle TOC renders badly.
    nav_items = ''
    for name, lo, hi in SECTIONS:
        rs = [r for r in recipes if lo <= int(r['num']) <= hi]
        if not rs:
            continue
        kids = ''.join(f'<li><a href="r/{r["num"]}.xhtml">{esc(r["title"])}</a></li>\n' for r in rs)
        nav_items += (f'<li><a href="r/{rs[0]["num"]}.xhtml">{name}</a>\n'
                      f'<ol>\n{kids}</ol>\n</li>\n')
    nav_body = (f'<nav epub:type="toc" id="toc"><h1>Contents</h1>\n<ol>\n'
                f'<li><a href="titlepage.xhtml">Title page</a></li>\n'
                f'{nav_items}</ol>\n</nav>')
    files['OEBPS/nav.xhtml'] = XHTML.format(title='Contents', up='', body=nav_body).encode()

    ncx_points = ''.join(
        f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{esc(r["title"])}</text></navLabel>'
        f'<content src="r/{r["num"]}.xhtml"/></navPoint>\n'
        for i, r in enumerate(recipes, 1))
    # Stable for the life of the work, and deliberately not derived from VERSION:
    # see EPUB_ID in imprint.py. The version belongs on the copyright page and in
    # dcterms:modified below, not in the identity of the publication.
    uid = IMP.EPUB_ID
    files['OEBPS/toc.ncx'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        f'<head><meta name="dtb:uid" content="{uid}"/></head>\n'
        f'<docTitle><text>{esc(IMP.TITLE)}</text></docTitle>\n'
        f'<navMap>\n{ncx_points}</navMap>\n</ncx>\n').encode()

    # ---- package ------------------------------------------------------------
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="style.css" media-type="text/css"/>',
        '<item id="cover-img" href="img/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="title" href="titlepage.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="copy" href="copyright.xhtml" media-type="application/xhtml+xml"/>',
    ]
    spine = ['<itemref idref="cover"/>', '<itemref idref="title"/>',
             '<itemref idref="copy"/>', '<itemref idref="nav"/>']
    for r in recipes:
        manifest.append(f'<item id="r{r["num"]}" href="r/{r["num"]}.xhtml" '
                        f'media-type="application/xhtml+xml"/>')
        manifest.append(f'<item id="i{r["num"]}" href="img/{imgs[r["num"]]}" media-type="image/jpeg"/>')
        spine.append(f'<itemref idref="r{r["num"]}"/>')

    modified = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    files['OEBPS/content.opf'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'<dc:identifier id="pub-id">{uid}</dc:identifier>\n'
        f'<dc:title>{esc(IMP.TITLE)}</dc:title>\n'
        f'<dc:creator>{esc(IMP.AUTHOR)}</dc:creator>\n'
        '<dc:language>en</dc:language>\n'
        f'<dc:description>{esc(IMP.SUBTITLE)}</dc:description>\n'
        f'<dc:date>{IMP.YEAR}-01-01</dc:date>\n'
        f'<meta property="dcterms:modified">{modified}</meta>\n'
        '</metadata>\n'
        f'<manifest>\n{chr(10).join(manifest)}\n</manifest>\n'
        f'<spine toc="ncx">\n{chr(10).join(spine)}\n</spine>\n'
        '</package>\n').encode()

    files['META-INF/container.xml'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles>\n</container>\n').encode()

    OUT.parent.mkdir(exist_ok=True)
    # Written to one side and moved into place, so a crash mid-build leaves the
    # previous archive intact rather than a truncated one that still opens.
    tmp = OUT.with_name(OUT.name + '.tmp')
    with zipfile.ZipFile(tmp, 'w') as z:
        # mimetype must be first and stored uncompressed
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip',
                   compress_type=zipfile.ZIP_STORED)
        for name in sorted(files):
            z.writestr(name, files[name], compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(OUT)

    mb = OUT.stat().st_size / 1e6
    img_mb = sum(len(v) for k, v in files.items() if k.startswith('OEBPS/img/')) / 1e6
    print(f'epub: {len(recipes)} recipes, {len(files) + 1} files -> {OUT.name} ({mb:.2f} MB)')
    print(f'      illustrations {img_mb:.2f} MB '
          f'({img_mb * 1000 / max(len(imgs), 1):.0f} KB each)')
    print(f'      KDP delivery fee at $0.15/MB on the converted size: '
          f'about ${mb * 0.15:.2f} a sale under the 70% option')
    if mb > 25:
        print('      WARNING: over the 25 MB the delivery fee starts to bite; '
              'lower JPEG_Q or IMG_W')


if __name__ == '__main__':
    build()
