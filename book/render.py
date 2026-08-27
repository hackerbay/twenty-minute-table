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

        # --- vertical justification pass: shrink or grow leading to fit the page ---
        await pg.evaluate("""()=>{
          const MM=96/25.4, TARGET=4.5*MM;
          const L=[
            {s:'.step',prop:'marginBottom',b:3.4,hi:4.5,lo:1.5},
            {s:'.ing',prop:'marginBottom',b:1.9,hi:2.4,lo:0.85},
            {s:'.why',prop:'marginBottom',b:6.5,hi:9,lo:3.2},
            {s:'.rbody',prop:'marginTop',b:7.5,hi:8,lo:3.5},
            {s:'.hook',prop:'marginTop',b:6,hi:6,lo:3},
            {s:'.blab',prop:'marginBottom',b:3,hi:3,lo:1.4},
            {s:'.ing-group:not(:first-child)',prop:'marginTop',b:3.4,hi:2.5,lo:1.6},
            {s:'.ing-panel',prop:'paddingTop',b:5,hi:6,lo:3.4},
            {s:'.ing-panel',prop:'paddingBottom',b:5,hi:6,lo:3.4},
            {s:'.rfoot',prop:'paddingTop',b:7,hi:0,lo:3.5}
          ];
          document.querySelectorAll('.page').forEach(pgEl=>{
            const body=pgEl.querySelector('.rbody'),foot=pgEl.querySelector('.rfoot');
            if(!body||!foot)return;
            const gap=()=>foot.getBoundingClientRect().top-body.getBoundingClientRect().bottom;
            const apply=t=>L.forEach(l=>pgEl.querySelectorAll(l.s).forEach(e=>{
              e.style[l.prop]=(t>=0? l.b+l.hi*t : l.b-(l.b-l.lo)*(-t))+'mm';}));
            const g0=gap();
            if(Math.abs(g0-TARGET)<2)return;
            let lo,hi;
            if(g0>TARGET){ apply(1); if(gap()>=TARGET)return; lo=0; hi=1; }
            else { apply(-1); if(gap()<0){return;} lo=-1; hi=0; }
            for(let k=0;k<24;k++){const m=(lo+hi)/2;apply(m);if(gap()>=TARGET)lo=m;else hi=m;}
            apply(lo);
          });
        }""")
        await pg.wait_for_timeout(300)
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
            const label=(pgEl.querySelector('.rtitle,.ptitle,h1')||{}).textContent||('page '+(i+1));
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
        gaps = await pg.evaluate("""()=>{const o=[];document.querySelectorAll('.page').forEach((p,i)=>{
          const b=p.querySelector('.rbody'),f=p.querySelector('.rfoot');if(!b||!f)return;
          o.push(Math.round((f.getBoundingClientRect().top-b.getBoundingClientRect().bottom)*25.4/96*10)/10);});return o;}""")
        gaps.sort()
        print("body-to-footer slack mm | min", gaps[0], "| median", gaps[len(gaps)//2], "| max", gaps[-1])
        if pdf:
            await pg.pdf(path=str(ROOT/'dist'/'The-20-Minute-Table.pdf'), width='210mm', height='297mm',
                         print_background=True, margin={'top':'0','right':'0','bottom':'0','left':'0'},
                         prefer_css_page_size=True)
        await b.close()

asyncio.run(main('--nopdf' not in sys.argv))
