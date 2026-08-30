import re, html, glob, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REC = ROOT / 'recipes'

METHODS = {
  'Air fryer': dict(key='airfryer', color='#C1502E', tint='#FAEDE7', label='Air Fryer'),
  'One pan':   dict(key='onepan',   color='#5A7A48', tint='#EDF3E8', label='One Pan'),
  'Wok':       dict(key='wok',      color='#A5632A', tint='#F9EFE3', label='Wok'),
  'No cook':   dict(key='nocook',   color='#2C6B7B', tint='#E7F0F2', label='No Cook'),
}
ORDER = ['Air fryer','One pan','Wok','No cook']

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s

def section(text, name):
    m = re.search(r'^## ' + re.escape(name) + r'\s*$(.*?)(?=^## |\Z)', text, re.M | re.S)
    return m.group(1).strip() if m else ''

def parse(path):
    t = Path(path).read_text(encoding='utf-8')
    r = {}
    h1 = re.search(r'^# (\d+) · (.+)$', t, re.M)
    r['num'] = h1.group(1)
    r['title'] = h1.group(2).strip()
    meta = re.search(r'\*\*Cuisine:\*\* (.+?) · \*\*Method:\*\* (.+?) · \*\*Total time:\*\* (.+?) · \*\*Serves:\*\* (\d+)', t)
    r['cuisine'], r['method'], r['time'], r['serves'] = [g.strip() for g in meta.groups()]
    r['minutes'] = int(re.match(r'(\d+)', r['time']).group(1))
    r['veg'] = '**Vegetarian**' in t.split('\n')[2]
    r['time_short'] = f"{r['minutes']} min"
    tm = re.search(r'\((\d+) prep / (\d+) cook\)', r['time'])
    r['prep'], r['cook'] = (tm.group(1), tm.group(2)) if tm else ('', '')
    r['m'] = METHODS[r['method']]
    hook = re.search(r'^> (.+)$', t, re.M)
    r['hook'] = hook.group(1).strip()
    r['why'] = ' '.join(section(t, 'Why it works').split())

    # ingredients
    groups, cur = [], {'name': None, 'items': []}
    for line in section(t, 'Ingredients').split('\n'):
        line = line.strip()
        if not line: continue
        gm = re.match(r'^\*\*(.+?)\*\*$', line)
        if gm:
            if cur['items']: groups.append(cur)
            cur = {'name': gm.group(1), 'items': []}
        elif line.startswith('- '):
            cur['items'].append(line[2:].strip())
    if cur['items']: groups.append(cur)
    r['ing_groups'] = groups
    r['ing_count'] = sum(len(g['items']) for g in groups)

    r['steps'] = [re.sub(r'^\d+\.\s*', '', s).strip()
                  for s in re.findall(r'^\d+\.\s+.+$', section(t, 'Method'), re.M)]

    notes = []
    for line in section(t, "Chef's notes").split('\n'):
        nm = re.match(r'^- \*\*(.+?):\*\*\s*(.+)$', line.strip())
        if nm: notes.append((nm.group(1), nm.group(2)))
    r['notes'] = notes

    nut = re.search(r'\|\s*(\d+) kcal\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|\s*(\d+) g\s*\|',
                    section(t, 'Nutrition (per serving, approx.)'))
    r['macros'] = list(nut.groups())
    r['toddler'] = ' '.join(section(t, 'For the toddler').split())
    r['washing'] = ' '.join(section(t, 'Washing up').split())
    r['chars'] = len(t)
    return r

def load_all():
    return [parse(p) for p in sorted(glob.glob(str(REC / '*.md')))]

if __name__ == '__main__':
    rs = load_all()
    print(len(rs), 'parsed')
    for r in rs[:2] + rs[-1:]:
        print(r['num'], r['title'], '|', r['method'], '|ing', r['ing_count'], '|steps', len(r['steps']),
              '|notes', len(r['notes']), '|macros', r['macros'], '|chars', r['chars'])
    print('max chars:', max(r['chars'] for r in rs), 'min:', min(r['chars'] for r in rs))
    print('max ingredients:', max(r['ing_count'] for r in rs))
