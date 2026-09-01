# Publishing to Amazon

How to get the three editions onto KDP. [RELEASING.md](RELEASING.md) covers changing the book
and publishing the website; this is the separate, manual step of listing it for sale.

Do it once carefully. Two of the choices below — trim size and ink — **cannot be changed after
publication**. Everything else can.

---

## Before you start

Three things must be true first.

**1. The release exists.** Publish a release so the files you upload are a version you can name
later. `RELEASING.md` covers it. The release attaches all four:

| File | Used for |
|---|---|
| `The-20-Minute-Table-vX.Y.Z.pdf` | interior of **both** print editions |
| `cover-paperback-vX.Y.Z.pdf` | paperback cover wrap |
| `cover-hardback-vX.Y.Z.pdf` | hardback case |
| `The-20-Minute-Table-vX.Y.Z.epub` | Kindle edition |
| `cover-kindle-vX.Y.Z.jpg` | Kindle cover |

You can also upload straight from `dist/` after `make amazon`.

**2. The ISBNs are registered at Bowker.** Both were assigned to the title at
[myidentifiers.com](https://www.myidentifiers.com/isbn_dashboard), with format and publication
details, on 1 September 2026, and both sit at Bowker's **Pending** status while the records
process into Books In Print. They are held in [book/imprint.py](book/imprint.py), and
[Registering the ISBNs at Bowker](#registering-the-isbns-at-bowker) below records what was filed:

- Paperback `978-1-950600-01-4`
- Hardback `978-1-950600-02-1`
- Kindle needs none; Amazon issues an ASIN.

Using your own ISBNs means **HackerBay** is the publisher of record rather than Amazon, and the
book could be printed elsewhere later without new numbers.

**3. Nothing else.** The hardback cover used to be the missing piece; it is now built like the
others. KDP publishes no hardcover case formula, so the dimensions were read from its
[Cover Calculator](https://kdp.amazon.com/en_US/cover-calculator) for 8.25 × 11 at 224 pages in
premium colour and recorded in `HC` at the top of [book/cover.py](book/cover.py):

| | |
|---|---|
| Full case | 18.79 × 12.417 in |
| Front and back panels | 8.447 × 11.236 in each |
| Spine | 0.715 in |
| Turn-in (wrap) | 0.591 in — glued down, nothing here is visible |
| Hinge channel | 0.394 in either side of the spine — type here gets creased |

**Those numbers are measured, not derived, so they are only right for 224 pages.** If the page
count changes, the build refuses to guess: it stops and tells you to re-measure. Both wraps are
also checked against their safe areas before the PDF is written — type in the turn-in or a hinge
fails the build rather than reaching a printer.

---

## Settings, verified

These came from KDP's own calculator. Enter them exactly; the two marked permanent are the ones
you cannot revise.

| | Paperback | Hardcover | Kindle |
|---|---|---|---|
| Interior type | Standard colour, white paper **(permanent)** | Premium colour, white paper **(permanent — the only option)** | — |
| Trim | **Custom**, 8.25 × 11 in **(permanent)** | 8.25 × 11 in (a standard size) **(permanent)** | — |
| Bleed | **Bleed (PDF only)** | **Bleed (PDF only)** | — |
| Pages | 224 | 224 | — |
| ISBN | 978-1-950600-01-4 | 978-1-950600-02-1 | none (ASIN) |
| Printing cost | $10.00 | $23.57 | $0.68 delivery (4.56 MB converted) |
| KDP minimum | $16.67 | $39.28 | — |
| **List price** | **$28.99** | **$69.99** | **$9.99** |
| Royalty | 60% → $7.39 | 60% → $18.42 | 70% → $6.52 |

The interior is built **with bleed** — 8.375 × 11.25 in page box against an 8.25 × 11 trim. If
you tell KDP "no bleed" it will reject or rescale it.

---

## What was submitted

All three editions went to KDP on 31 August 2026 from version 1.0.0, and each came back
**In review**. KDP takes up to 72 hours to finish that review, and the Amazon product pages —
and therefore the links this repo wants to put on the website — do not exist until it does.

| | Paperback | Hardcover | Kindle |
|---|---|---|---|
| Status | In review | In review | In review |
| List price | $28.99 | $69.99 | $9.99 |
| Royalty | 60% → $7.39 | 60% → $18.42 | 70% → $6.52 |
| Margin | 25.5% | 26.3% | 65.3% |

Confirmed by KDP at submission, against what this repo predicted:

- **Print cost.** $10.00 paperback, $23.57 hardcover — both exactly the figures in
  [book/imprint.py](book/imprint.py).
- **Minimum list price.** $16.67 and $39.28, again matching. Every edition clears the 25%
  margin gate that `make pricing` enforces.
- **Kindle file size.** 4.56 MB after conversion, so $0.68 of delivery comes off the 70%
  royalty. The 70% band now runs to $12.99, as `KDP_70_BAND` already assumed.
- **Trim and pages.** 8.25 × 11 in, 224 pages, bleed, on both print editions. The hardcover
  previewer reported no issues.

Three decisions worth knowing about, because they are not obvious and two are permanent:

- **DRM is off** on the Kindle edition. The book carries a CC BY 4.0 notice that grants the
  right to share and adapt it; shipping it under DRM would contradict the copyright page.
  **This cannot be changed after publication.**
- **KDP Select is not enrolled.** It demands exclusivity, and the PDF is a free download from
  our own site. That costs the 70% rate in Japan, Brazil and Mexico, which drop to 35%.
- **The AI declaration** is *Yes* on all three: texts *some sections, with minimal or no
  editing*, tool *OpenCode*, images *None*, translations *None*. The same answer on every
  edition, because it is the same content.

---

## Registering the ISBNs at Bowker

Both ISBNs were registered against the title at
[myidentifiers.com](https://www.myidentifiers.com) on 1 September 2026, under the
HackerBay, Inc. account, and both sit at Bowker's **Pending** status while the records
are processed into Books In Print. Until a number is registered it resolves to nothing,
which is why this step matters even though Amazon never asks for it.

This is what was filed. Keep it here: the two records have to agree with each other and
with the book, and re-deriving any of it is how they drift apart.

**Shared by both editions**

| Field | Value |
|---|---|
| Title | The 20-Minute Table |
| Subtitle | A hundred fast, whole-food recipes for the years when dinner has to happen anyway |
| Contributor | Nawaz Dhandala — Author (A01) |
| Publisher | HackerBay, Inc. |
| Imprint | HackerBay |
| Edition | First edition |
| Page count | 224 |
| Trim | 8.25 x 11 in (209.55 x 279.4 mm) |
| Cover finish | Matte |
| Language | English |
| Copyright | 2026, Nawaz Dhandala |
| Country of publication | United States |
| Publication date | 3 September 2026 |
| Title status | Forthcoming, moved to Active once the Amazon pages exist |
| Audience | Trade / general adult |
| Sales rights | World |
| Availability | Print on demand (Amazon KDP), not returnable, carton quantity 1 |
| Front cover image | `dist/cover-kindle.jpg` — the only front-only asset; both print files are full wraps |

**Per edition**

| | Paperback | Hardback |
|---|---|---|
| ISBN | 978-1-950600-01-4 | 978-1-950600-02-1 |
| Binding | Trade paperback, perfect bound | Hardcover, case laminate, no jacket |
| Interior | Standard colour, white paper, bleed | Premium colour, white paper, bleed |
| List price | $28.99 USD | $69.99 USD |
| Related edition | 978-1-950600-02-1 | 978-1-950600-01-4 |

**Subjects.** Bowker's short form does not take BISAC codes at all. It offers its own
much broader list and exactly two slots, so the filed values are **First Genre: COOKING**
and **Second Genre: PARENTING**. The BISAC headings this book would otherwise carry
(*Cooking / Methods / Quick & Easy*, *Cooking / Courses & Dishes / General*,
*Family & Relationships / Parenting / General*) are reachable only through Bowker's
Advanced form. The KDP categories are a third scheme again — do not try to reconcile them.

Four things the form asks for that this repo cannot answer, and how each was handled:

- **Leave thickness and weight blank.** `cover.py` derives the paperback spine with the
  premium colour constant while that interior is standard colour, so the figure it reports is
  not the right one to file. Measure a proof copy instead.
- **No Kindle ISBN.** Amazon issues an ASIN. Register a third number only if the EPUB is ever
  distributed outside Amazon.
- **No illustrator credit.** The food icons and action pictograms are generated by code in
  this repository, not drawn by a second person.
- **The contributor biography is blank.** Bowker allows 350 words and does not require any.
  Nothing in the repo supplies a biography and inventing one is not the job of a build script,
  so the field was left empty; it can be added later by editing either record.

The account itself is **HackerBay, Inc.**, and that is what Bowker records as the publisher.
The short form has no imprint field — the imprint selector lives on the Advanced form and the
account has none defined — so "HackerBay" as a separate imprint was not filed. Nothing is
missing from the record; it just means publisher and imprint are the same name.

---

## Paperback

1. KDP Bookshelf → **Create** → **Paperback**.
2. **Details.** Title *The 20-Minute Table*, subtitle from
   [book/imprint.py](book/imprint.py), author **Nawaz Dhandala**, publisher **HackerBay**.
   Description: adapt the back cover copy in `book/cover.py`. Not a large-print or low-content
   book.
3. **ISBN.** Choose *Use my own ISBN* and enter `978-1-950600-01-4`. Imprint: HackerBay.
4. **Content.** Print options exactly as the table above. Upload
   `The-20-Minute-Table.pdf` as the manuscript and `cover-paperback.pdf` as the cover.
5. **Previewer.** Work through every warning. It will confirm 224 pages and the trim.
6. **Rights & Pricing.** Worldwide rights. Primary marketplace Amazon.com, **$28.99**, 60%.
   Let other marketplaces convert automatically unless you have a reason not to.
7. **Order a proof** before publishing, and check the gutter, the bleed on all three outer
   edges, and the folio position with a ruler. It is the only way to be sure.

### The trade you made by choosing 8.25 × 11

Expanded Distribution is the bookstore, library and academic channel. Two things about it,
both from KDP's own eligibility page:

- **Hardcover is never eligible.** KDP states it outright.
- **Eligibility is a fixed chart of standard trim sizes.** A custom trim — which 8.25 × 11 is,
  for a paperback — is not on that chart, so it does not qualify. But **8.5 × 11 with standard
  colour on white paper does.**

So there was a genuine fork, and it is worth being clear which side we are on. 8.25 × 11 is the
only trim that is *both* a hardcover size and reachable as a paperback, so one interior serves
both editions. 8.5 × 11 would have opened Expanded Distribution for the paperback — at 40%
royalty rather than 60% — but there is no 8.5 × 11 hardcover, so the hardback would have to go.

**Hardback plus one interior, or Expanded Distribution.** Not both. We chose the hardback. If
that turns out to be the wrong call, it means a new paperback at 8.5 × 11 with its own ISBN —
trim cannot be changed on a published title.

## Hardcover

Same flow, **Create → Hardcover**, with `978-1-950600-02-1`, the premium colour interior, the
same `The-20-Minute-Table.pdf`, and `cover-hardback.pdf`. List at **$69.99**.

The hardback is expensive because it has to be: KDP does not offer standard colour for
hardcover, so 224 colour pages cost $23.57 to print and 25% margin needs $67.34. If you would
rather sell it cheaper, $55 still works at about 17%.

## Kindle

1. **Create** → **Kindle eBook**.
2. Same details. **No ISBN needed.**
3. **KDP Select: do not enrol.** The full PDF is free at
   [twentyminutetable.hackerbay.io](https://twentyminutetable.hackerbay.io), and Select requires
   the digital edition be exclusive to Amazon. You keep the 70% royalty in the US, UK and EU
   without it; what you give up is Kindle Unlimited.
4. **DRM: no.** The content is CC BY 4.0. Locking it would contradict the licence the book
   itself prints on its copyright page.
5. Upload `The-20-Minute-Table.epub` and `cover-kindle.jpg`.
6. Check the converted file size KDP reports **before** setting the price — the delivery fee is
   charged on that, not on the EPUB. It should be at or under 4.2 MB.
7. Price **$9.99**, 70% royalty.

Run the EPUB through Adobe epubcheck and Kindle Previewer 3 first. `make epub` runs a structural
check with no Java dependency, but it is not a substitute.

---

## After publishing

- **Link the editions** so paperback, hardcover and Kindle share one detail page. KDP usually
  does this automatically for matching title and author; if not, ask KDP support.
- **Categories** — two, plus up to seven keywords. Quick & easy cooking, baby and toddler
  feeding, and whole-food or family cooking all fit this book.
- **Author Central** for the author page and A+ content.

## Updating a published book

Interior and cover files, description, categories, keywords and price can all be changed after
publication: upload a new file and republish, and Amazon relists within a couple of days.

**Trim size and ink cannot.** Changing either means publishing a new title with a new ISBN.

When you do update, cut a release first so the file you upload is a version you can point at.
