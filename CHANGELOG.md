# Changelog

The version in `package.json` is the single source of truth. It is printed on the book's
cover and colophon, shown in the website footer, and used as the git tag when a release is
cut. Bump it there and everything else follows.

This project uses [semantic versioning](https://semver.org) loosely, read for a cookbook:

- **Patch** — a correction. A conversion that was wrong, a timing that was optimistic, a
  typo, a broken link.
- **Minor** — new recipes, a new section, a new feature on the website.
- **Major** — a change that reorganises the book: renumbering recipes, changing the recipe
  file contract, dropping a section.

## Unreleased

- Open source: MIT for the toolchain, CC BY 4.0 for the recipes and the book text.
- The website is published at https://twentyminutetable.hackerbay.io.
- A PDF download in the site header, on every page.
- Version stamped on the cover, in the colophon and in the site footer.
- CI on every push and pull request; releases cut automatically from the `release` branch.
- Typeset for Amazon KDP: 8.25x11 trim with bleed, mirrored margins, flattened
  transparency, print front matter, and an even page count.
- Fixed a pagination bug that split fifty recipes' spreads across a page turn.
- Paperback cover wrap, Kindle cover, and a reflowable EPUB3 edition.
- `RELEASING.md`: how to change the book and publish the result.
- Releases now attach all four Amazon artefacts, not just the print PDF.
- A margin gate: `make pricing` refuses a submission bundle whose economics miss
  the 25% target, and says what list price each edition would need.
- ISBNs allocated from HackerBay's own Bowker block, so the publisher of record
  is not Amazon.

## 1.0.0

- 100 recipes across 49 cuisines, typeset into a 217-page book and a static website.
- Every recipe serves four, is on the table inside twenty minutes, and carries a toddler note.
