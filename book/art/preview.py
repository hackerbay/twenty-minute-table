"""Render an icon dict to a labelled PNG grid so it can be reviewed by eye.
Usage: python3 preview.py <module_name> [out.png]
The module must define PART = {'key': '<svg elements>'}"""
import sys, asyncio, importlib, math
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def build_html(part, cols=6, cell=190):
    rows = math.ceil(len(part) / cols)
    cells = ''
    for k, body in part.items():
        cells += (f'<div class="c"><svg viewBox="0 0 48 48" width="118" height="118" fill="none" '
                  f'stroke="#1B201D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                  f'{body}</svg><div class="l">{k}</div></div>')
    return f'''<!doctype html><meta charset="utf-8"><style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{background:#FDFAF4;font:500 12px/1.3 system-ui,sans-serif;color:#4B554E;padding:16px}}
    .g{{display:grid;grid-template-columns:repeat({cols},1fr);gap:8px;width:{cols*cell}px}}
    .c{{background:#fff;border:1px solid #E2DACA;border-radius:8px;padding:12px 6px 8px;
        display:flex;flex-direction:column;align-items:center;gap:8px}}
    .l{{font-size:11px;color:#828C84;text-align:center;word-break:break-word}}
    .s{{fill:#1B201D;stroke:none}}
    </style><div class="g">{cells}</div>'''

async def main():
    mod = importlib.import_module(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else f'{sys.argv[1]}.png'
    html = build_html(mod.PART)
    tmp = HERE / f'_prev_{sys.argv[1]}.html'
    tmp.write_text(html, encoding='utf-8')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1200, 'height': 900}, device_scale_factor=2)
        await pg.goto(tmp.as_uri()); await pg.wait_for_timeout(400)
        el = await pg.query_selector('.g')
        await el.screenshot(path=out)
        await b.close()
    tmp.unlink()
    print(f'{len(mod.PART)} icons -> {out}')

asyncio.run(main())
