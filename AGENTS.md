# AGENTS.md

Working notes for coding agents on **The 20-Minute Table**. Read this before editing anything.

## What this repo is

A cookbook that is compiled, not laid out by hand. 100 markdown recipe files in `recipes/` are
the single source of truth; a Python toolchain in `book/` turns them into two artefacts:

- `dist/The-20-Minute-Table.pdf` — a 224-page print book, 8.25x11 trim with bleed
- `site/` — a static website with no build step and no external requests

Every number that appears in either output — page numbers, contents pages, cuisine indexes,
cover statistics, vegetarian counts, website filters — is derived from the recipe files. There
are no hand-maintained totals anywhere. If you change a recipe, rerun the build and the rest
follows.

## The one rule that matters

**Never hand-edit `dist/`, `site/` or `build/`.** They are generated. Change `recipes/` or
`book/`, then rerun `make`. A diff that edits generated HTML directly will be overwritten by
the next build and is always the wrong fix.

`build/` is gitignored. `dist/` and `site/` are committed, so regenerate and commit them
whenever the sources change — otherwise the repo ships stale output.

## Build

```bash
npm install     # Fraunces + Inter, embedded into both outputs
make verify     # structure — must be clean
make audit      # content — must be clean
make book       # markdown -> HTML -> PDF
make site       # markdown -> static site
make            # verify, audit, book, site
```

Requires Python 3 with `playwright` and a Chromium build available to it. `make clean` removes
`build/` and `site/`.

`make verify` and `make audit` are the gate. Both must report zero problems before you commit.
Current baseline: `verify` reports "No problems found", `audit` reports "100 recipes audited — 0
findings". Do not commit a regression from that.

## Pipeline

```
recipes/*.md
   |
   parse.py        markdown -> structured recipe data
   |
   +-- build.py    -> build/cookbook.html   -- render.py -> dist/*.pdf
   |
   +-- site.py     -> site/
```

Shared data modules feed **both** outputs, so edit them once and the book and site stay in
agreement:

| File | Owns |
|---|---|
| `book/pairings.py` | which three sides go with each main |
| `book/pantry_data.py` | the pantry checklist, the kit, the ten rules |
| `book/toddler_data.py` | the general toddler guidance page |
| `book/icons.py` | method icons, the time dial, the page-anatomy diagram |
| `book/art/` | 72 food icons, 20 action pictograms, colours, composition |
| `book/style.css` | print stylesheet |
| `book/web/` | site stylesheet and script |

## Recipe file contract

`recipes/NN-slug.md`, numbered contiguously from `01`. `verify.py` enforces all of the
following and fails the build otherwise:

- Exactly one H1: `# NN · Title`. Titles must be unique across the book.
- A meta line matching exactly, `·`-separated:
  `**Cuisine:** X · **Method:** Y · **Total time:** N min (P prep / C cook) · **Serves:** 4`
  plus a trailing ` · **Vegetarian**` where it applies.
- `Serves:` is always `4`.
- Total time is **never above 20 minutes**.
- H2 sections, exactly these and in this order:
  `Why it works`, `Ingredients`, `Method`, `Chef's notes`, `For the toddler`,
  `Nutrition (per serving, approx.)`, `Washing up`.
- 3–7 numbered method steps.
- `Chef's notes` contains all four labels: `**Swap:**`, `**Make it faster:**`,
  `**On the side:**`, `**Leftovers:**`.
- `For the toddler` is 28–120 words.
- If `honey` appears in the ingredients it **must** be addressed in the toddler note.
- Nutrition table macros must be arithmetically consistent: `4·protein + 4·carbs + 9·fat`
  within 12% of the stated kcal.

## House style

These are enforced mechanically — a build failure, not a preference:

- **No exclamation marks.** Anywhere in a recipe file.
- **Banned words:** delicious, flavorful/flavourful, elevate, game-changer/game changer,
  whip up, burst of flavour/flavor.

And these are conventions to match, enforced by `audit.py` or by eye:

- **Metric first, imperial in brackets:** `200 g (1 cup) couscous`, `200°C (400°F)`. Keep the
  two consistent — `audit.py` catches conversions that have drifted.
- Every ingredient listed must be used in the method, and every ingredient the method calls for
  must be listed.
- Meat needs a doneness cue, not just a timer.
- Portions stay in a sensible kcal range for their section (mains 600–780).
- No sentence copy-pasted between recipes; `audit.py` flags repeated prose.
- Plain, declarative voice. Describe what happens in the pan and why, not how good it tastes.

## Print geometry — the rules the book is now built to

The book is typeset for Amazon KDP at **8.25in x 11in trim**, the only size in KDP's
catalogue that is both a standard hardcover trim and reachable as a paperback. One interior
serves the premium colour hardback and the standard colour paperback. `docs/kdp-publishing-spec.md`
is the full specification; these are the parts that will break if you edit carelessly.

**The page box carries bleed.** `.page` is `8.375in x 11.25in` — trim plus 0.125in on the top,
bottom and outer edge. The gutter never carries bleed. Anything that should reach the printed
edge must run to the page box edge, not the trim line.

**Margins are mirrored, and the side comes from the page index.** `build.py` stamps
`data-side="recto|verso"` when it numbers the pages; the CSS keys the mirrored `.inner` padding,
the folio centring and the page-number side off that attribute. Never derive the side from
`:nth-of-type()` — divider and blank insertions make the DOM index wrong.

**Pagination invariants, asserted in `build.py`.** A facing pair in a bound book is
(even verso, odd recto), so every recipe's plate page must be even and its method page the next
one, or the two-page spread the whole design rests on is split across a page turn. The build
asserts this for all 100 recipes, that each recipe's contents entry matches where its plate
actually lands, and that the total page count is even — KDP appends an uncontrolled blank
otherwise. Blank versos close sections one to three so the next divider opens on a recto; front
matter runs to 16 pages for the same reason. Change `FRONT`, add a page, or reorder a section
and the assertion will tell you what you broke.

**The cover is not an interior page.** KDP prints it from a separate wrap file. The artwork
lives in `build.cover_front_html()` and is rendered by the cover build, not appended to `pages`.

**Never write `rgba()`, `opacity`, or an eight-digit hex.** KDP requires a flattened interior.
Every alpha in this book is one known colour over one known backdrop, so it is pre-composited at
build time with `flatten.mix(fg, bg, alpha)`. Flattening downstream with Ghostscript instead
would rasterise those regions and turn an all-vector book into a mixed one, reintroducing a
resolution problem the book does not otherwise have. `make kdp` fails the build on any
transparency group, soft mask, sub-1 alpha operator, wrong page box or odd page count.

**ISBNs live in `book/imprint.py`**, allocated from HackerBay's own Bowker block so the
publisher of record is not Amazon. The copyright page omits any empty field rather than printing
a placeholder, so the book is always correct to print even while something there is unset.

## The Amazon editions

```bash
make amazon     # verify, audit, interior, covers, Kindle edition
```

Three artefacts land in `dist/`:

| File | What it is |
|---|---|
| `The-20-Minute-Table.pdf` | the interior, 8.25x11 trim with bleed, for both print editions |
| `cover-paperback.pdf` | the full wrap: back cover, spine, front cover, bleed on all four sides |
| `cover-hardback.pdf` | the hardback case: turn-in, back, hinge, spine, hinge, front, turn-in |
| `cover-kindle.jpg` | 2560x1600 front cover for the eBook |
| `The-20-Minute-Table.epub` | reflowable EPUB3 for Kindle |

**The spine width is derived, not configured.** `cover.py` reads the real page count out
of the built interior and multiplies by KDP's premium colour figure. Rebuild the interior
before the cover or the spine will be wrong for the book it wraps.

**The hardback case dimensions are measured, not derived.** KDP publishes no hardcover
formula, so the numbers in `HC` at the top of `cover.py` were read from its Cover Calculator
for 8.25x11 at 224 pages in premium colour. They are only correct at that page count, and the
build refuses to guess: change the page count and `make covers` stops and tells you to
re-measure. Do not compute the case from the paperback wrap — it is larger in both axes,
because the sheet wraps a board that overhangs the text block and turns in to be glued down.

**Both wraps are checked before the PDF is written.** Type in the turn-in would be glued out of
sight; type in a hinge channel gets creased. `cover.py` measures every piece of text against the
safe area in the live layout and fails the build rather than producing a cover that looks fine
on screen and wrong in the hand.

**The Kindle edition is reflowable, and the print design does not survive.** Full-bleed
panels, the two-page spread and the vertical justification are print production, not content;
`epub.py` rebuilds the book from `parse.py` as semantic XHTML the reader restyles. It is
generated from `recipes/`, never from `build/cookbook.html`, which is print geometry. Keep
body text at `1em` and set fonts on `body` only — an absolute size takes the reader's font
control away. `make epub` runs a structural check, but run Adobe epubcheck and Kindle
Previewer 3 before publishing.

**Watch the EPUB's size.** KDP charges $0.15/MB of the converted file against the 70%
royalty option, so illustration weight comes straight off the margin. `epub.py` reports the
total and the implied fee; it is around 4 MB today, and the knobs are `IMG_W` and `JPEG_Q`.

**Margins are gated, not assumed.** `make pricing` computes the lowest list price each
edition needs to clear its target margin (25%, in `imprint.py`) and fails if a configured
price misses it; `make amazon` runs it, so a submission bundle cannot be prepared with
economics that do not work. CI deliberately does not run it — an unmade business decision
should not turn the build red. On a colour book the page count sets the floor under the
price: at 224 pages premium colour needs roughly a $54 list to clear 25%, standard colour
about $29, and every 10 pages cut takes about $2.29 off the minimum in premium colour,
$1.15 in standard.

**The pricing figures in `imprint.py` are verified.** Every one was read from KDP's own
printing-cost calculator on 2026-08-31 for 8.25x11 at 224 pages, and KDP confirmed the
print costs and minimum list prices again at submission. They are correct at that page
count and trim and nowhere else: change either and re-read them from the calculator rather
than scaling them. The numbers at the end of `docs/kdp-publishing-spec.md` were not
rechecked and still describe a 218-page premium colour book.

**The ISBNs are allocated but not registered.** They come from HackerBay's own Bowker block
so the publisher of record is not Amazon. Assigning them against the title at Bowker means
entering real publication metadata, and is left as a deliberate human step.

## Typesetting

Each recipe occupies exactly two A4 pages. `render.py` runs a vertical-justification pass in
headless Chromium: per page it binary-searches one parameter that expands or tightens leading,
panel padding and — on the densest pages — body size, until content sits 4.5 mm above the
footer. Long ingredient lists switch to a two-column panel automatically.

If you add a recipe with an unusually long ingredient list or method, **check the PDF**, not
just that the build exited zero. The justifier will do something to make it fit; confirm the
something is reasonable.

## Adding or changing a recipe

1. Copy an existing file in `recipes/` as the template — the contract above is unforgiving.
2. Number it next in sequence; keep numbering contiguous.
3. If it is a main, add its side pairings to `book/pairings.py`.
4. `make verify && make audit` — both clean.
5. `make` to regenerate, then eyeball the affected spread in `dist/The-20-Minute-Table.pdf`.
6. Commit the sources **and** the regenerated `dist/` and `site/`.

Renumbering existing recipes is expensive: it changes filenames, the pairings map and every
cross-reference. Prefer appending.

## Photographs

There are none by design. The slots exist: drop `NN-hero.jpg` or `NN-step-K.jpg` into `images/`
and the build picks them up. See `images/README.md`.

## Versioning and releases

`package.json` holds the version and nothing else does. `book/version.py` reads it, and it
surfaces in three places: the book cover foot, the book colophon, and the website footer. Never
hardcode a version anywhere else.

To cut a release: bump `version` in `package.json`, add a `CHANGELOG.md` entry, run `make`,
commit the regenerated `dist/` and `site/`, then merge to the `release` branch. The release
workflow builds, deploys to Firebase, tags `v<version>` and publishes a GitHub release with the
PDF attached. It refuses to run if the tag already exists — bump the version rather than trying
to move a tag people may already have.

## Continuous integration

`.github/workflows/ci.yml` runs on every push to `main` and every pull request: `make verify`,
`make audit`, then a full book and site build. It also fails if the committed `site/` does not
match what the sources generate — that check is what stops a recipe change landing without its
regenerated output. The PDF is excluded from that comparison because Chromium stamps a creation
date into it, so it is not byte-reproducible.

## Deployment

The site is a plain static directory — fonts are embedded in the stylesheet, so `site/` works on
any static host with no configuration.

```bash
make site
firebase deploy --only hosting
```

`firebase.json` serves `site/` as the public root. Rebuild before deploying; do not deploy a
`site/` that is out of date with `recipes/`.
