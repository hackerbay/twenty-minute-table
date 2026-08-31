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

## 1.0.1

- `PUBLISHING.md` records what actually went to Amazon — the prices, the royalties, and
  the DRM, KDP Select and AI declarations, two of which cannot be changed later.
- Kindle economics corrected to KDP's measured converted file size: 4.56 MB, so $0.68
  of delivery and a $6.52 royalty rather than the estimated $6.36.
- `make pricing` no longer claims the converted Kindle file is smaller than the EPUB.
  It is larger — 4.23 MB became 4.56 MB — so the estimate runs optimistic, not
  conservative, and now says so.

## 1.0.0

- 100 recipes across 49 cuisines, typeset into a 224-page book and a static website.
- Every recipe serves four, is on the table inside twenty minutes, and carries a toddler note.
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
- The book says where it came from: HackerBay.io on the title page, the copyright
  page, the colophon and both covers.
- A "Why this book exists" page facing the title page, and an open-source note on
  the back cover.
- The same "why" on the website's about page, from a shared `mission.py` so the
  book and the site cannot drift apart.
- List prices set from KDP's own calculator: paperback $28.99 (standard colour),
  hardback $69.99 (premium colour, the only option), Kindle $9.99.
- The hardback case is now built like the other covers, to dimensions measured
  from KDP's Cover Calculator; both wraps are checked against their safe areas
  before the PDF is written.
