"""Colour for every icon in the food library.

Each entry is (base, accent). `base` fills the first closed shape — the body of
the thing. `accent` fills every closed shape after it, which is where yolks,
stones, pips and flesh live. Where an ingredient is one colour throughout, the
two are the same. Outlines are derived by darkening the base, so the line work
belongs to the same hue rather than sitting on top in black.
"""

COLORS = {
    # proteins and dairy
    'chicken-thigh': ('#E8B57A', '#E8B57A'), 'prawn': ('#F4A088', '#F4A088'),
    'salmon-fillet': ('#F09372', '#F09372'), 'white-fish': ('#B4CBD8', '#B4CBD8'),
    'beef-strips': ('#C4614F', '#C4614F'),   'pork-loin': ('#EFAC91', '#EFAC91'),
    'turkey-breast': ('#E3B183', '#E3B183'), 'egg': ('#F3E7CB', '#F2B441'),
    'tofu': ('#E8DBB6', '#E8DBB6'),          'paneer': ('#EADCB9', '#EADCB9'),
    'feta': ('#EBDFC2', '#EBDFC2'),          'yoghurt': ('#EDE4C9', '#DBCBA6'),
    'tuna-tin': ('#D6DCE0', '#D08C6A'),      'anchovy': ('#C08258', '#C08258'),
    # vegetables
    'cauliflower': ('#E9DCB8', '#B9CC93'),   'broccoli': ('#6D9A55', '#6D9A55'),
    'tomato': ('#D9483B', '#6D9A55'),        'cherry-tomatoes': ('#DE5546', '#6D9A55'),
    'onion': ('#E7C7A8', '#E7C7A8'),         'spring-onion': ('#8FB86B', '#F1EADA'),
    'garlic': ('#E2CFA4', '#E2CFA4'),        'ginger': ('#DDBB86', '#DDBB86'),
    'chilli': ('#CE3B32', '#6D9A55'),        'bell-pepper': ('#E0562F', '#E0562F'),
    'courgette': ('#6E9C51', '#6E9C51'),     'aubergine': ('#7B5A8F', '#6D9A55'),
    'mushroom': ('#C8A987', '#EFE6D4'),      'spinach': ('#4E8244', '#4E8244'),
    'kale': ('#43703C', '#43703C'),          'cabbage': ('#BCD09A', '#BCD09A'),
    'pak-choi': ('#86AE5C', '#F1EADA'),      'green-beans': ('#6FA24E', '#6FA24E'),
    'peas': ('#B7CE8E', '#6FA24E'),          'sweetcorn': ('#F0C04E', '#8FB86B'),
    'sweet-potato': ('#E08B4E', '#E08B4E'),  'carrot': ('#E58A3C', '#6D9A55'),
    'cucumber': ('#86B26A', '#86B26A'),      'avocado': ('#A8C264', '#8A6A42'),
    'radish': ('#DA5B6A', '#8FB86B'),        'fennel': ('#D8E3B4', '#8FB86B'),
    # fruit and nuts
    'lemon': ('#F2C93F', '#8FB86B'),         'lime-wedge': ('#B4CF4A', '#DCE9AF'),
    'orange': ('#F0913A', '#F7C489'),        'pineapple': ('#E7B93F', '#8FB86B'),
    'banana': ('#F2CE55', '#F2CE55'),        'date': ('#A9713F', '#A9713F'),
    'fig': ('#9B5A85', '#D9899E'),           'walnut': ('#C79A62', '#E0BE8E'),
    'almond': ('#D8A878', '#D8A878'),        'coconut': ('#DCC9A6', '#EDE2CA'),
    # pulses, grains, bread
    'chickpeas': ('#DCB870', '#DCB870'),     'black-beans': ('#5A4A52', '#5A4A52'),
    'white-beans': ('#E2CFA6', '#E2CFA6'),   'lentils': ('#C97A4E', '#C97A4E'),
    'rice-bowl': ('#E9D9B0', '#E9D9B0'),     'noodles': ('#E9CE90', '#E9CE90'),
    'oats': ('#DFCAA0', '#DFCAA0'),          'couscous': ('#E3C88E', '#E3C88E'),
    'bread': ('#D9A968', '#D9A968'),         'flatbread': ('#E9C68C', '#C48B4E'),
    'nori': ('#3C6157', '#3C6157'),          'sesame': ('#E2CCA0', '#E2CCA0'),
    # store cupboard
    'olive-oil': ('#CBAE45', '#CBAE45'),     'soy-bottle': ('#7A5540', '#7A5540'),
    'paste-jar': ('#C1502E', '#E0BE8E'),     'tinned-tomatoes': ('#D24B3C', '#EFE6D4'),
    'coconut-milk': ('#E9DDC6', '#D9C9A8'),  'olives': ('#7A8F45', '#7A8F45'),
    'honey': ('#E0A32E', '#E0A32E'),         'tahini': ('#DCC694', '#DCC694'),
    'herbs': ('#5C8A48', '#5C8A48'),         'spice-jar': ('#C77A33', '#EFE6D4'),
}

DEFAULT = ('#E0BE8E', '#E0BE8E')


def _hex(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def shade(color, k=0.52):
    """A darker, slightly desaturated version of a colour, for outlines."""
    r, g, b = _hex(color)
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def tone(color, k):
    """Lighten (k>1) or darken (k<1) towards white/black."""
    r, g, b = _hex(color)
    if k >= 1:
        f = min(k - 1, 1)
        return '#%02X%02X%02X' % tuple(int(v + (255 - v) * f) for v in (r, g, b))
    return shade(color, k)


def of(key):
    return COLORS.get(key, DEFAULT)
