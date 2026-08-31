import asyncio, sys, json
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent

async def main(pdf=True):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--font-render-hinting=none'])
        pg = await b.new_page(viewport={'width':1200,'height':1600})
        await pg.goto((ROOT/'build'/'cookbook.html').as_uri(), wait_until='networkidle')
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(1500)

        # --- vertical justification: fit each page by trading leading, per page type ---
        await pg.evaluate("""()=>{
          const MM=96/25.4, TARGET=4.5*MM;
          const PLATE=[
            {s:'.hero',prop:'height',b:88,hi:14,lo:60},
            {s:'.hero',prop:'marginBottom',b:8,hi:3,lo:4},
            {s:'.ing',prop:'fontSize',b:8.5,hi:1.5,lo:7.9,u:'pt'},
            {s:'.why',prop:'fontSize',b:8.9,hi:1.6,lo:8.2,u:'pt'},
            {s:'.rhead',prop:'marginBottom',b:0,hi:10,lo:0},
            {s:'.ing',prop:'marginBottom',b:1.9,hi:2.4,lo:0.75},
            {s:'.why',prop:'marginBottom',b:6.5,hi:9,lo:3},
            {s:'.rbody',prop:'marginTop',b:7.5,hi:8,lo:3.2},
            {s:'.hook',prop:'marginTop',b:6,hi:6,lo:3},
            {s:'.blab',prop:'marginBottom',b:3,hi:3,lo:1.4},
            {s:'.ing-group:not(:first-child)',prop:'marginTop',b:3.4,hi:2.5,lo:1.5},
            {s:'.ing-panel',prop:'paddingTop',b:5,hi:6,lo:3.2},
            {s:'.ing-panel',prop:'paddingBottom',b:5,hi:6,lo:3.2},
            {s:'.rfoot',prop:'paddingTop',b:7,hi:8,lo:3.4},
            {s:'.notes',prop:'paddingTop',b:4,hi:5,lo:2.2},
            {s:'.goes',prop:'marginTop',b:3.2,hi:2,lo:1.4},
            {s:'.wash',prop:'marginTop',b:3.5,hi:2,lo:2},
            {s:'.strip',prop:'marginTop',b:5.5,hi:3,lo:3},
            {s:'.note',prop:'fontSize',b:8.1,hi:1.1,lo:7.6,u:'pt'}
          ];
          const METHOD=[
            {s:'.mstep',prop:'marginBottom',b:7,hi:26,lo:1.6},
            {s:'.mtext',prop:'paddingTop',b:2.6,hi:4,lo:1.0},
            {s:'.mtext',prop:'fontSize',b:10.4,hi:2.4,lo:9.3,u:'pt'},
            {s:'.sglyph,.sphoto',prop:'width',b:15,hi:10,lo:11.5},
            {s:'.sglyph,.sphoto',prop:'height',b:15,hi:10,lo:11.5},
            {s:'.mhead',prop:'paddingBottom',b:4,hi:8,lo:2.4},
            {s:'.mblab',prop:'marginTop',b:7,hi:14,lo:2.6},
            {s:'.blab',prop:'marginBottom',b:3,hi:3,lo:1.4},
            {s:'.rfoot',prop:'paddingTop',b:7,hi:3,lo:3.2}
          ];
          const FRONT=[
            {s:'.rbody',prop:'marginTop',b:7.5,hi:8,lo:3.5}
          ];
          document.querySelectorAll('.page').forEach(pgEl=>{
            const body=pgEl.querySelector('.rbody'),foot=pgEl.querySelector('.rfoot');
            if(!body||!foot)return;
            const L = pgEl.querySelector('.ing-panel') ? PLATE
                    : pgEl.querySelector('.msteps') ? METHOD : FRONT;
            const gap=()=>foot.getBoundingClientRect().top-body.getBoundingClientRect().bottom;
            const apply=t=>L.forEach(l=>pgEl.querySelectorAll(l.s).forEach(e=>{
              e.style[l.prop]=(t>=0? l.b+l.hi*t : l.b-(l.b-l.lo)*(-t))+(l.u||'mm');}));
            const g0=gap();
            if(Math.abs(g0-TARGET)<2)return;
            let lo,hi;
            if(g0>TARGET){ apply(1); if(gap()>=TARGET)return; lo=0; hi=1; }
            else { apply(-1); if(gap()<0)return; lo=-1; hi=0; }
            for(let k=0;k<24;k++){const m=(lo+hi)/2;apply(m);if(gap()>=TARGET)lo=m;else hi=m;}
            apply(lo);
          });
        }""")
        await pg.wait_for_timeout(400)
        over = await pg.evaluate("""() => {
          const out=[];
          document.querySelectorAll('.page').forEach((pgEl,i)=>{
            const inner=pgEl.querySelector('.inner');
            const kids=[...inner.children];
            let last=kids.length?kids[kids.length-1]:null;
            const ib=inner.getBoundingClientRect();
            let deepest=ib.top;
            inner.querySelectorAll('*').forEach(e=>{
              const r=e.getBoundingClientRect();
              if(r.height>0&&r.bottom>deepest) deepest=r.bottom;
            });
            const cs=getComputedStyle(inner);
            const limit=ib.bottom-parseFloat(cs.paddingBottom);
            const spill=deepest-limit;
            const f=pgEl.parentElement.querySelector(':scope > .folio');
            const fo=pgEl.querySelector('.folio')||pgEl.nextElementSibling;
            let label=(pgEl.querySelector('.rtitle,.ptitle,.mh-title,h1')||{}).textContent||'';
            const kind=pgEl.querySelector('.ing-panel')?'PLATE':pgEl.querySelector('.msteps')?'METHOD':'FRONT';
            label=kind+' '+label;
            out.push({i:i+1,label:label.trim().slice(0,46),spill:Math.round(spill*100)/100,
                      scroll:inner.scrollHeight-inner.clientHeight});
          });
          return out;
        }""")
        bad=[o for o in over if o['spill']>0.5 or o['scroll']>1]
        print(f"pages: {len(over)} | overflowing: {len(bad)}")
        for o in bad: print(f"  p{o['i']:>3} spill {o['spill']:>7}px  scroll {o['scroll']:>4}  {o['label']}")
        worst=sorted(over,key=lambda o:-o['spill'])[:5]
        print("closest to the edge:")
        for o in worst: print(f"  p{o['i']:>3} spill {o['spill']:>8}px  {o['label']}")
        # --- KDP safe-area check ------------------------------------------------
        # Measured from the TRIM edge. The gutter carries no bleed, so the page box
        # edge is the trim edge there; the outer, top and bottom edges each sit
        # 3.175mm of bleed outside trim. .mnum deliberately hangs outside the content
        # box, so this measures real ink rather than trusting the padding.
        safe = await pg.evaluate("""()=>{
          const MM=96/25.4, BLEED=3.175, out=[];
          document.querySelectorAll('.page').forEach((p,i)=>{
            const pb=p.getBoundingClientRect();
            const inner=p.querySelector('.inner'); if(!inner)return;
            let minL=1e9,maxR=-1e9;
            inner.querySelectorAll('*').forEach(e=>{const q=e.getBoundingClientRect();
              if(q.width>0&&q.height>0){ if(q.left<minL)minL=q.left; if(q.right>maxR)maxR=q.right; }});
            if(minL>1e8)return;                       // a blank page has no ink
            const recto = p.dataset.side==='recto';
            const fromPageL=(minL-pb.left)/MM, fromPageR=(pb.right-maxR)/MM;
            // gutter side has no bleed; outer side must lose the bleed to reach trim
            const gutter = recto ? fromPageL : fromPageR;
            const outer  = (recto ? fromPageR : fromPageL) - BLEED;
            out.push({i:i+1, gutter:+gutter.toFixed(2), outer:+outer.toFixed(2)});
          });
          return out;}""")
        GUTTER_MIN, OUTER_MIN = 12.7, 6.35     # KDP, 151-300pp, measured from trim
        tight = [s for s in safe if s['gutter'] < GUTTER_MIN or s['outer'] < OUTER_MIN]
        g = min(s['gutter'] for s in safe); o = min(s['outer'] for s in safe)
        print(f"safe area mm from trim | tightest gutter {g} (min {GUTTER_MIN})"
              f" | tightest outer {o} (min {OUTER_MIN})")
        if tight:
            print(f"  KDP SAFE AREA VIOLATED on {len(tight)} page(s):")
            for s in tight[:10]:
                print(f"    p{s['i']:>3} gutter {s['gutter']}mm outer {s['outer']}mm")
            raise SystemExit(1)

        gaps = await pg.evaluate("""()=>{const o=[];document.querySelectorAll('.page').forEach((p,i)=>{
          const b=p.querySelector('.rbody'),f=p.querySelector('.rfoot');if(!b||!f)return;
          o.push(Math.round((f.getBoundingClientRect().top-b.getBoundingClientRect().bottom)*25.4/96*10)/10);});return o;}""")
        gaps.sort()
        print("body-to-footer slack mm | min", gaps[0], "| median", gaps[len(gaps)//2], "| max", gaps[-1])
        if pdf:
            await pg.pdf(path=str(ROOT/'dist'/'The-20-Minute-Table.pdf'), width='8.375in', height='11.25in',
                         print_background=True, margin={'top':'0','right':'0','bottom':'0','left':'0'},
                         prefer_css_page_size=True)
        await b.close()

asyncio.run(main('--nopdf' not in sys.argv))
