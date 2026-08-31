"""Gate the built PDF against Amazon KDP's interior requirements.

Fails the build rather than letting a non-compliant file reach an upload, because
KDP's own rejection messages are slow and vague. Everything checked here is
something KDP either states outright or silently rounds/rejects.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / 'dist' / 'The-20-Minute-Table.pdf'

# 8.375in x 11.25in = trim 8.25x11 plus 0.125in bleed on the outer edge and both
# ends. Chromium emits a width a hundredth of a point wide; that is 0.04mm against
# KDP's own 3.175mm paper-shift tolerance, so a tolerance is honest here where
# demanding an exact integer would only invite a pointless workaround.
WANT_W, WANT_H, TOL = 603.0, 810.0, 0.5


def main():
    if not PDF.exists():
        sys.exit(f'kdp: {PDF} not built')
    d = PDF.read_bytes()
    problems = []

    boxes = set(re.findall(rb'/MediaBox\s*\[([^\]]*)\]', d))
    if len(boxes) != 1:
        problems.append(f'{len(boxes)} different MediaBox values; every page must be one size')
    for box in boxes:
        try:
            x0, y0, x1, y1 = (float(v) for v in box.split())
        except ValueError:
            problems.append(f'unparseable MediaBox: {box!r}')
            continue
        w, h = x1 - x0, y1 - y0
        if abs(w - WANT_W) > TOL or abs(h - WANT_H) > TOL:
            problems.append(f'page box {w:.2f} x {h:.2f}pt, want {WANT_W} x {WANT_H} (+/-{TOL})')

    pages = len(re.findall(rb'/Type\s*/Page[^s]', d))
    if pages % 2:
        problems.append(f'{pages} pages: odd, so KDP will append a blank of its own')

    # KDP requires a flattened interior. Ghostscript would flatten by rasterising,
    # so these are pre-composited at source instead — see book/flatten.py.
    for label, pat in [('transparency groups', rb'/S\s*/Transparency'),
                       ('soft masks', rb'/SMask(?!\s*/None)'),
                       ('annotations', rb'/Annots'),
                       ('encryption', rb'/Encrypt')]:
        n = len(re.findall(pat, d))
        if n:
            problems.append(f'{n} {label}')

    # /ca and /CA at 1 are the opaque default graphics state, not transparency.
    # Only a value below 1 is an actual alpha blend.
    for label, pat in [('fill-alpha', rb'/ca\s+([0-9.]+)'),
                       ('stroke-alpha', rb'/CA\s+([0-9.]+)')]:
        soft = [v for v in re.findall(pat, d) if float(v) < 1]
        if soft:
            problems.append(f'{len(soft)} {label} operators below 1: {sorted(set(v.decode() for v in soft))}')

    if not re.search(rb'/FontFile', d):
        problems.append('no embedded font programs')

    if problems:
        print('kdp: interior does NOT meet the requirements')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print(f'kdp: interior OK — {pages} pages, '
          f'{sorted(boxes)[0].decode()}, flattened, fonts embedded')


if __name__ == '__main__':
    main()
