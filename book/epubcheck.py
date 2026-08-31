"""Structural validation of the built EPUB.

Not a substitute for Adobe's epubcheck or Kindle Previewer — run those before
publishing — but it catches the things that actually break a Kindle conversion
and it runs in the build with no Java dependency.
"""
import re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath, Path

ROOT = Path(__file__).resolve().parent.parent
EPUB = ROOT / 'dist' / 'The-20-Minute-Table.epub'
OPF_NS = {'o': 'http://www.idpf.org/2007/opf'}


def resolve(base, href):
    parts = []
    for seg in str((PurePosixPath(base).parent / href).as_posix()).split('/'):
        if seg == '..':
            parts and parts.pop()
        elif seg not in ('.', ''):
            parts.append(seg)
    return '/'.join(parts)


def main():
    if not EPUB.exists():
        sys.exit('epubcheck: build the epub first (make epub)')
    # A build that fails before writing leaves the previous archive in place, and
    # validating that would report success for a file nobody just built. Compare
    # against the newest input instead of trusting whatever is on disk.
    built = EPUB.stat().st_mtime
    sources = list((ROOT / 'recipes').glob('*.md')) + list((ROOT / 'book').rglob('*.py'))
    cover = ROOT / 'dist' / 'cover-kindle.jpg'
    if cover.exists():
        sources.append(cover)
    newer = [p for p in sources if p.stat().st_mtime > built]
    if newer:
        rel = [str(p.relative_to(ROOT)) for p in sorted(newer)[:4]]
        sys.exit(f'epubcheck: {EPUB.name} is older than {len(newer)} of its sources '
                 f'({", ".join(rel)}). Rebuild it — the epub build probably failed.')

    z = zipfile.ZipFile(EPUB)
    names = z.namelist()
    problems = []

    if names[0] != 'mimetype':
        problems.append(f'first archive entry is {names[0]!r}; it must be "mimetype"')
    if z.getinfo('mimetype').compress_type != zipfile.ZIP_STORED:
        problems.append('mimetype must be stored uncompressed')
    if z.read('mimetype') != b'application/epub+zip':
        problems.append('mimetype content is wrong')

    for n in names:
        if n.endswith(('.xhtml', '.opf', '.ncx', '.xml')):
            try:
                ET.fromstring(z.read(n))
            except ET.ParseError as e:
                problems.append(f'{n} is not well-formed XML: {e}')

    if 'OEBPS/content.opf' in names:
        root = ET.fromstring(z.read('OEBPS/content.opf'))
        items = root.findall('.//o:manifest/o:item', OPF_NS)
        missing = [i.get('href') for i in items if f"OEBPS/{i.get('href')}" not in names]
        if missing:
            problems.append(f'{len(missing)} manifest items are not in the archive: {missing[:4]}')
        ids = {i.get('id') for i in items}
        dangling = [r.get('idref') for r in root.findall('.//o:spine/o:itemref', OPF_NS)
                    if r.get('idref') not in ids]
        if dangling:
            problems.append(f'spine points at unknown ids: {dangling[:4]}')
        navs = [i for i in items if 'nav' in (i.get('properties') or '')]
        if len(navs) != 1:
            problems.append(f'{len(navs)} items declare properties="nav"; EPUB3 needs exactly one')
        covers = [i for i in items if 'cover-image' in (i.get('properties') or '')]
        if len(covers) != 1:
            problems.append(f'{len(covers)} items declare cover-image; need exactly one')

    dead = []
    for n in names:
        if n.endswith('.xhtml'):
            for href in re.findall(rb'(?:href|src)="([^"#:]+)"', z.read(n)):
                t = resolve(n, href.decode())
                if t not in names:
                    dead.append(f'{n} -> {href.decode()}')
    if dead:
        problems.append(f'{len(dead)} dead internal links, e.g. {dead[:3]}')

    # KDP forbids transparency in EPUB images
    pngs = [n for n in names if n.lower().endswith('.png')]
    if pngs:
        problems.append(f'{len(pngs)} PNGs present; KDP wants no alpha — prefer JPEG: {pngs[:3]}')

    mb = EPUB.stat().st_size / 1e6
    if problems:
        print('epubcheck: FAILED')
        for p in problems:
            print('  -', p)
        sys.exit(1)
    print(f'epubcheck: OK — {len(names)} entries, {sum(n.endswith(".xhtml") for n in names)} documents, '
          f'{mb:.2f} MB')
    print('           still run Adobe epubcheck and Kindle Previewer 3 before publishing')


if __name__ == '__main__':
    main()
