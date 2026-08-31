"""Pre-composite translucent colours against their known backdrop.

KDP requires a flattened interior: no transparency groups, no alpha operators.
Every alpha in this book is a single known foreground over a single known
backdrop, so it can be resolved to an opaque colour at build time. That keeps
the PDF entirely vector — flattening downstream with Ghostscript would rasterise
the affected regions and reintroduce a resolution question this book does not
otherwise have.
"""


def _rgb(c):
    c = c.lstrip('#')
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(fg, bg, alpha):
    """`fg` at `alpha` over opaque `bg`, as an opaque #RRGGBB."""
    f, b = _rgb(fg), _rgb(bg)
    return '#%02X%02X%02X' % tuple(round(alpha * x + (1 - alpha) * y) for x, y in zip(f, b))
