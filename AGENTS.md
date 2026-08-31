# AGENTS.md

Working notes for coding agents on **The 20-Minute Table**. Read this before editing anything.

## What this repo is

A cookbook that is compiled, not laid out by hand. 100 markdown recipe files in `recipes/` are
the single source of truth; a Python toolchain in `book/` turns them into two artefacts:

- `dist/The-20-Minute-Table.pdf` — a 217-page A4 print book
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
