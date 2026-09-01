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

- **The Kindle edition declares a real, stable identifier.** `dc:identifier` was
  `urn:uuid:twenty-minute-table-1.0.1`: not a UUID at all, which Adobe epubcheck rejects,
  and carrying the version, so v1.0.1 and v1.0.2 presented as two different publications
  rather than two versions of one. It is now a version 4 UUID, minted once and held as
  `EPUB_ID` in `book/imprint.py` next to the ISBNs, and used verbatim in both `content.opf`
  and `toc.ncx`. The version still appears where it belongs — the colophon prints it, and
  `dcterms:modified` carries the build time. `book/epubcheck.py` now asserts the
  identifier's form and that the two files agree, so it cannot drift back.
- Three places still said the ISBNs were not registered at Bowker, which 1.0.2 had already
  made untrue: the comment above the ISBN dict in `book/imprint.py`, the "Before you start"
  prerequisite in `PUBLISHING.md` — which contradicted its own "Registering the ISBNs at
  Bowker" section further down the same file — and `AGENTS.md`. All three now say what
  happened: registered on 1 September 2026 under the HackerBay, Inc. account, and Pending
  at Bowker while the records process into Books In Print. `README.md` and `RELEASING.md`
  never carried the claim.

No page of the book changed in this release. Nothing here is a reason to re-upload to
Amazon: Kindle keys on the ASIN and never reads the EPUB's identifier, so the edition in
review there is unaffected. The identifier fix matters for future builds, and for any
channel other than Amazon.

## 1.0.2

- Both ISBNs are registered at Bowker against the title, so the numbers printed in the
  book resolve to a real record rather than to nothing. `PUBLISHING.md` carries what was
  filed, including the three subject schemes that do not map onto each other.
- **The content gates actually fail now.** `book/audit.py` ended `sys.exit(0 if main() == 0
  else 0)` — both branches zero — and `book/verify.py` never called `sys.exit` at all, so
  neither could ever turn CI red. The recipe contract and house style in `AGENTS.md` were
  conventions rather than gates for as long as they have existed.
- The paperback spine is measured on the paper it is printed on. `cover.py` multiplied the
  page count by the premium colour figure while the paperback interior is standard colour,
  making the wrap 0.54mm too wide; the multiplier is now chosen from `INK_CHOICE`, and an
  unrecognised ink stops the build rather than guessing. Covers rebuilt to match.
- Corrected stale facts that had drifted since the book was retypeset for Amazon: the
  README called it a 217-page book, `AGENTS.md` described the paperback as premium colour,
  put the standard colour pricing floor $10 too low, and said every figure in `imprint.py`
  was unverified when KDP has since confirmed them, and `RELEASING.md` listed four release
  artefacts when there are five — omitting the one file the hardcover needs.

No page of the book changed in this release. Nothing here is a reason to re-upload to
Amazon: the editions on sale carry v1.0.0, which is the version that was published.

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
- Releases now attach all five Amazon artefacts, not just the print PDF.
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
