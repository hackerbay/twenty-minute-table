# Contributing

The whole point of this repo being open is that you can take it apart. Fork it,
change it, cook from it, translate it, print it, put your own recipes in it. You
do not need permission and you do not need to ask first.

If you want your change to come back here, read on.

## The quickest possible start

```bash
git clone https://github.com/hackerbay/twenty-minute-table.git
cd twenty-minute-table
npm install
make verify   # structure
make audit    # content
make          # build the book and the site
```

You need Python 3 with `playwright` and a Chromium build available to it. If you
only want to change recipes and see the website, `python3 book/site.py` skips the
PDF render and is much faster.

## What this project will happily take

- **New recipes.** Anything that lands on the table in twenty minutes from a cold
  start, serves four, is built on whole ingredients, and leaves one pan behind.
  Cuisines not already in the book are especially welcome — there are 49 so far.
- **Corrections.** A conversion that is wrong, a step that does not work, a timing
  that is optimistic. These are the most valuable contributions there are; if you
  cooked it and it failed, that is worth an issue on its own.
- **Translations.** The build is content-agnostic. A translated `recipes/` is a
  legitimate fork and a good one.
- **Accessibility and typesetting fixes.** Especially on the website.

## What to know before you write a recipe

`make verify` is strict, and it is strict on purpose — it is what keeps 100
recipes consistent enough to typeset automatically. It will reject your recipe if
the shape is wrong, and the error message tells you what it wants.

The full contract is in [AGENTS.md](AGENTS.md), but the short version:

- Copy an existing file in `recipes/` rather than starting from blank.
- Twenty minutes maximum. Serves four. No exceptions — both are enforced.
- Metric first, imperial in brackets, and the two must actually agree.
- Every recipe needs a `## For the toddler` section. If it contains honey, the
  toddler note must say so.
- No exclamation marks, and no cookbook filler — "delicious", "elevate",
  "game-changer" and friends are a build failure, not a style note.
- The nutrition table has to be arithmetically consistent with itself.

Then:

```bash
make verify && make audit
```

Both must come back clean. `make` regenerates the book and the site; commit the
regenerated `dist/` and `site/` along with your recipe.

## Pull requests

Small and single-purpose is easier to review than large and sweeping. Say what you
changed and, for a recipe, say that you cooked it — that is the only real test
this project has.

## What CI will check

Opening a pull request runs `make verify`, `make audit` and a full build. It also checks that
the committed `site/` matches what your recipe files generate, so run `make` and commit the
regenerated `dist/` and `site/` along with your change.

## Licensing your contribution

By contributing you agree that your contribution is licensed on the same terms as
the rest of the project: MIT for code, CC BY 4.0 for recipes and written content.
See [LICENSE](LICENSE) and [LICENSE-CONTENT](LICENSE-CONTENT).

## A note on the toddler guidance

The toddler notes are about cooking, not nutrition or medicine. Please keep them
that way. Anything that reads as clinical advice will be edited or declined — the
guidance page points readers at their own health service, and that is deliberate.
