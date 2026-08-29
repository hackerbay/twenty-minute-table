import sys, asyncio, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from food import PART
from playwright.async_api import async_playwright

def variant_all(body, fill, line):
    return f'<g fill="{fill}" fill-rule="evenodd" stroke="{line}">{body}</g>'

def variant_first(body, fill, line):
    els = re.findall(r'<[^>]+/>', body)
    if not els: return variant_all(body, fill, line)
    head = els[0].replace('/>', f' fill="{fill}"/>')
    return f'<g stroke="{line}" fill="none">{head}{"".join(els[1:])}</g>'

def variant_closed(body, fill, line):
    els = re.findall(r'<[^>]+/>', body)
    out = ''
    for e in els:
        d = re.search(r'd="([^"]*)"', e)
        closed = (d and ('z' in d.group(1).lower())) or e.startswith('<circle') or e.startswith('<ellipse') or e.startswith('<rect') or e.startswith('<polygon')
        out += e.replace('/>', f' fill="{fill}"/>') if closed else e
    return f'<g stroke="{line}" fill="none">{out}</g>'

VARIANTS = {'all': variant_all, 'first': variant_first, 'closed': variant_closed}

async def main():
    which = sys.argv[1]; out = sys.argv[2]
    fn = VARIANTS[which]
    cells = ''
    for k, body in PART.items():
        cells += (f'<div class="c"><svg viewBox="0 0 48 48" width="96" height="96" fill="none" '
                  f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
                  f'{fn(body, "#E8A87C", "#1B201D")}</svg><div class="l">{k}</div></div>')
    html = f'''<!doctype html><meta charset=utf-8><style>*{{margin:0;padding:0;box-sizing:border-box}}
    body{{background:#FDFAF4;padding:12px;font:500 10px/1.2 system-ui;color:#828C84}}
    .g{{display:grid;grid-template-columns:repeat(9,1fr);gap:6px;width:1260px}}
    .c{{background:#fff;border:1px solid #E2DACA;border-radius:6px;padding:8px 4px 5px;
       display:flex;flex-direction:column;align-items:center;gap:5px}}
    .l{{text-align:center;word-break:break-word}} .s{{fill:#1B201D;stroke:none}}</style>
    <div class="g">{cells}</div>'''
    p = Path(f'/tmp/ft_{which}.html'); p.write_text(html)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={'width':1300,'height':900}, device_scale_factor=1.6)
        await pg.goto(p.as_uri()); await pg.wait_for_timeout(400)
        await (await pg.query_selector('.g')).screenshot(path=out); await b.close()
    print(which, '->', out)

asyncio.run(main())
