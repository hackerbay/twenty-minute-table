import math
from flatten import mix

ICONS = {
 'airfryer': '<rect x="3.5" y="6.5" width="14" height="13" rx="2.6"/><path d="M17.5 10h3.2v6h-3.2"/>'
             '<path d="M7 3c0 1.3 1.6 1.3 1.6 2.6M12 3c0 1.3 1.6 1.3 1.6 2.6"/><path d="M7 16.2h7"/>',
 'onepan':   '<path d="M2.4 9.6h13.2v4.2a4.2 4.2 0 0 1-4.2 4.2h-4.8a4.2 4.2 0 0 1-4.2-4.2z"/>'
             '<path d="M15.6 11.3h6.2"/><path d="M6 6.6c0-1.2 1.4-1.2 1.4-2.4M10.4 6.6c0-1.2 1.4-1.2 1.4-2.4"/>',
 'wok':      '<path d="M2.6 9.4h18.8l-3.2 6.8a4.8 4.8 0 0 1-4.3 2.7h-3.8a4.8 4.8 0 0 1-4.3-2.7z"/>'
             '<path d="M1 9.4h3M20 9.4h3"/><path d="M9.6 6.2c0-1.3 1.5-1.3 1.5-2.6M13.4 6.2c0-1.3 1.5-1.3 1.5-2.6"/>',
 'nocook':   '<path d="M12 21V8.6"/><path d="M12 13.4c0-3.4 2.8-6.2 6.2-6.2 0 3.4-2.8 6.2-6.2 6.2z"/>'
             '<path d="M12 17.6c0-2.9-2.3-5.2-5.2-5.2 0 2.9 2.3 5.2 5.2 5.2z"/>',
}

def icon(key, size='4.6mm', sw=1.45):
    return (f'<svg class="ico" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
            f'stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[key]}</svg>')

def dial(minutes, color, size='100%', cap=20, bg='#FDFAF4'):
    """A ring showing a recipe's total time against a twenty-minute dial.

    The arc is inset by half a stroke at each end so its round caps sit inside
    the sweep rather than overshooting the twelve o'clock start, and the SVG
    fills its wrapper so the ring and the label centre on the same box.
    """
    r, sw = 10.4, 1.7
    circ = 2 * math.pi * r
    frac = max(0.05, min(minutes / cap, 1.0))
    arc = max(circ * frac - sw, 0.01)
    return (f'<svg viewBox="0 0 26 26" width="{size}" height="{size}" '
            f'style="display:block" aria-hidden="true">'
            f'<circle cx="13" cy="13" r="{r}" fill="none" stroke="{mix(color, bg, .15)}" '
            f'stroke-width="{sw}"/>'
            f'<circle cx="13" cy="13" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-dasharray="{arc:.2f} {circ:.2f}" '
            f'stroke-dashoffset="{-sw / 2:.2f}" transform="rotate(-90 13 13)"/></svg>')


def anatomy(c='#C1502E', tint='#FAEDE7', w='64mm', bg='#FDFAF4'):
    def bars(x, y, widths, gap=6.2, h=2.6, fill='#828C84', op=.42, rx=1.3, on=None):
        out = ''
        for i, ww in enumerate(widths):
            out += (f'<rect x="{x}" y="{y+i*gap}" width="{ww}" height="{h}" rx="{rx}" '
                    f'fill="{mix(fill, on or bg, op)}"/>')
        return out
    r = 14; C = 2 * math.pi * r
    mk = lambda x, y, n: (f'<circle cx="{x}" cy="{y}" r="7.6" fill="{c}"/>'
                          f'<text x="{x}" y="{y+3.4}" font-size="9.4" font-weight="700" fill="#fff" '
                          f'text-anchor="middle" font-family="Inter">{n}</text>')
    steps = ''
    for i in range(4):
        yy = 138 + i * 21
        steps += (f'<text x="93" y="{yy+3}" font-size="8" fill="{c}" font-family="Georgia">{i+1}</text>'
                  + bars(101, yy - 3, [92, 78, 54][:2 + (i % 2)], 6.4))
    macs = ''.join(f'<line x1="{17+35.2*(i+1)}" y1="258" x2="{17+35.2*(i+1)}" y2="278" '
                   f'stroke="#fff" stroke-width="1"/>' for i in range(4))
    macv = ''.join(f'<rect x="{24+35.2*i}" y="263" width="21" height="5" rx="2" fill="{mix(c, tint, .55)}"/>'
                   f'<rect x="{27+35.2*i}" y="271" width="15" height="2.6" rx="1.3" fill="{mix('#828C84', tint, .45)}"/>'
                   for i in range(5))
    return f'''<svg viewBox="0 0 210 297" width="{w}" style="height:auto;display:block">
<rect x=".5" y=".5" width="209" height="296" fill="#FDFAF4" stroke="#E2DACA"/>
<rect width="210" height="7" fill="{c}"/>
<text x="17" y="45" font-size="24" font-weight="700" fill="{c}" font-family="Georgia">01</text>
<rect x="52" y="26" width="100" height="9" rx="3" fill="{mix('#1B201D', bg, .85)}"/>
<rect x="52" y="41" width="27" height="7" rx="3.5" fill="{c}"/>{bars(84, 42.5, [30, 22, 20], 0)}
<rect x="84" y="42.5" width="30" height="3" rx="1.5" fill="{mix('#828C84', bg, .42)}"/>
<rect x="119" y="42.5" width="22" height="3" rx="1.5" fill="{mix('#828C84', bg, .42)}"/>
<circle cx="180" cy="38" r="{r}" fill="none" stroke="{mix(c, bg, .18)}" stroke-width="3"/>
<circle cx="180" cy="38" r="{r}" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round"
  stroke-dasharray="{C*0.9:.1f} {C:.1f}" transform="rotate(-90 180 38)"/>
<rect x="17" y="70" width="2.2" height="18" fill="{c}"/>
<rect x="26" y="72" width="150" height="4" rx="2" fill="{mix(c, bg, .5)}"/>
<rect x="26" y="81" width="96" height="4" rx="2" fill="{mix(c, bg, .5)}"/>
<rect x="17" y="94" width="24" height="3.2" rx="1.6" fill="{mix(c, bg, .75)}"/>
<line x1="17" y1="102" x2="81" y2="102" stroke="#E2DACA" stroke-width="1"/>
<rect x="17" y="108" width="64" height="112" rx="4" fill="#F6F1E6"/>
{bars(23, 116, [40, 50, 44, 52, 36, 48, 42, 51, 38, 46, 44, 39, 47, 35], 7.1, 2.7, '#4B554E', .38)}
<rect x="93" y="94" width="24" height="3.2" rx="1.6" fill="{mix(c, bg, .75)}"/>
<line x1="93" y1="102" x2="193" y2="102" stroke="#E2DACA" stroke-width="1"/>
{bars(93, 108, [100, 96, 62], 6.6)}
<rect x="93" y="128" width="20" height="3.2" rx="1.6" fill="{mix(c, bg, .75)}"/>
<line x1="93" y1="133.5" x2="193" y2="133.5" stroke="#E2DACA" stroke-width="1"/>
{steps}
<line x1="17" y1="230" x2="193" y2="230" stroke="#E2DACA" stroke-width="1"/>
<rect x="17" y="236" width="18" height="3" rx="1.5" fill="{mix(c, bg, .7)}"/>
<rect x="110" y="236" width="24" height="3" rx="1.5" fill="{mix(c, bg, .7)}"/>
{bars(17, 243, [76, 62], 6.2)}{bars(110, 243, [80, 58], 6.2)}
<rect x="17" y="258" width="176" height="20" rx="3" fill="{tint}"/>{macs}{macv}
<rect x="17" y="286" width="22" height="3" rx="1.5" fill="{mix(c, bg, .7)}"/>
<rect x="45" y="286" width="96" height="3" rx="1.5" fill="{mix('#828C84', bg, .42)}"/>
{mk(180,38,1)}{mk(26,57,2)}{mk(49,164,3)}{mk(160,110,4)}{mk(105,268,5)}{mk(37,286,6)}
</svg>'''
