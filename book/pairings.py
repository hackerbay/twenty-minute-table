"""Which side goes with which main.

Keyed by main-course number, valued by side numbers in the order they are
suggested. Sides are 86-100. Edit freely; the book and the website both read
this file, and an unknown number is simply ignored.

  98  cucumber, mint and yoghurt raita — the cooling side for anything spiced
  99  blistered padron peppers — Spanish and Mediterranean plates
 100  charred broccolini with miso butter — the East Asian and Japanese mains
"""

PAIRINGS = {
    '01': ['88', '98', '94'], '02': ['100', '93', '97'], '03': ['92', '89', '95'],
    '04': ['98', '91', '94'], '05': ['100', '87', '93'], '06': ['94', '90', '88'],
    '07': ['95', '97', '94'], '08': ['99', '86', '92'], '09': ['95', '97', '92'],
    '10': ['90', '94', '88'], '11': ['96', '98', '89'], '12': ['92', '95', '96'],
    '13': ['87', '100', '93'], '14': ['88', '98', '94'], '15': ['100', '87', '97'],
    '16': ['87', '91', '100'], '17': ['91', '98', '87'], '18': ['100', '87', '93'],
    '19': ['87', '100', '93'], '20': ['93', '100', '87'], '21': ['87', '95', '100'],
    '22': ['93', '100', '87'], '23': ['91', '98', '94'], '24': ['98', '91', '90'],
    '25': ['98', '91', '94'], '26': ['94', '90', '89'], '27': ['90', '94', '88'],
    '28': ['89', '86', '94'], '29': ['99', '89', '86'], '30': ['86', '89', '92'],
    '31': ['86', '89', '92'], '32': ['86', '94', '89'], '33': ['99', '92', '89'],
    '34': ['99', '92', '95'], '35': ['95', '97', '94'], '36': ['95', '92', '94'],
    '37': ['95', '91', '89'], '38': ['87', '95', '100'], '39': ['87', '100', '91'],
    '40': ['87', '91', '100'], '41': ['87', '91', '98'], '42': ['96', '89', '88'],
    '43': ['88', '98', '90'], '44': ['96', '89', '91'], '45': ['94', '90', '96'],
    '46': ['87', '95', '97'], '47': ['90', '94', '88'], '48': ['93', '87', '100'],
    '49': ['95', '94', '92'], '50': ['94', '90', '89'],
}


def sides_for(num, byn, limit=3):
    """Resolve a main's suggested sides to recipe records that actually exist."""
    return [byn[s] for s in PAIRINGS.get(num, [])[:limit] if s in byn]


def mains_for(side_num, byn, limit=6):
    """The reverse lookup: which mains name this side."""
    out = [m for m, ss in sorted(PAIRINGS.items()) if side_num in ss]
    return [byn[m] for m in out[:limit] if m in byn]
