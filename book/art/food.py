"""Merged line-art food icon library. 48x48 viewBox, stroke-based, fill:none.

Elements carrying class="s" are rendered as solid fills (seeds, pips, grains).
"""
from food_a import PART as A
from food_b import PART as B
from food_c import PART as C
from food_d import PART as D
from food_e import PART as E
from food_f import PART as F

PART = {}
for _p in (A, B, C, D, E, F):
    PART.update(_p)

# Redraws for a handful that did not read clearly at small size.
PART.update({
    'kale':
        '<path d="M24 43v-4"/>'
        '<path d="M24 39.5c-3.4-6.4-3.4-13 0-19.6 3.4 6.6 3.4 13.2 0 19.6z"/>'
        '<path d="M24 39.5c-6.6-3.2-9.6-9-8.6-17 5.9 2.8 8.9 8.4 8.6 17z"/>'
        '<path d="M24 39.5c6.6-3.2 9.6-9 8.6-17-5.9 2.8-8.9 8.4-8.6 17z"/>',
    'sweet-potato':
        '<path d="M11.5 32.5c-3.4-4 .2-11.2 7.5-15.2 7.4-4 15.6-3.2 18.4 1.2 2.6 4.1-.4 9.6-6.6 13.2'
        '-6.6 3.8-15.7 4.3-19.3.8z"/>'
        '<path d="M16.8 25.8c2.4-1.5 5-2.6 7.5-3.2M22.5 31.4c2.9-.7 5.7-2 8-3.5"/>'
        '<path d="M10.6 30.4 6.5 31.8M38.3 19.6l4.2-1.6"/>',
    'turkey-breast':
        '<path d="M12 28.6c0-7.4 5.6-13.4 13-13.4 6.4 0 10.9 3.6 10.9 8.4 0 6.4-6.4 11.6-14.2 11.6'
        '-6 0-9.7-2.6-9.7-6.6z"/>'
        '<path d="M18.4 21.6c3 .7 5.6 2.3 7.4 4.6M23.6 18.6c2.6.6 4.9 1.9 6.6 3.8"/>',
})
