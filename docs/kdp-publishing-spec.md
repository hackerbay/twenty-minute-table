# KDP publishing specification

How to take the book from its current A4 web/PDF form to three Amazon editions:
premium colour hardback, premium colour paperback, and a reflowable Kindle edition.

Researched against Amazon's own KDP help pages and adversarially verified; every
number that could not be confirmed against a primary source is called out as such
in the final section. Confirm those in KDP before submitting.

---


---

## 0. Verified state of the current artefact

Probed directly against `/Users/nawazdhandala/Projects/HackerBay/twenty-minute-table/recipie/dist/The-20-Minute-Table.pdf`:

| Property | Measured value | Verdict |
|---|---|---|
| Page count | 217 `/Type /Page` objects | Must become an even number (218) — KDP rounds up and inserts its own blank otherwise |
| MediaBox | `[0 0 595.91998 841.91998]` pt = 210.23 × 297.04 mm | Wrong size, wrong shape, and **no bleed** despite a full-bleed design |
| PDF version | 1.4 | Acceptable (KDP specifies no version) |
| Transparency groups | 56 `/S /Transparency` | **FAIL** — flattening is mandatory |
| Alpha operators | 29 `/ca`, 7 `/CA` | **FAIL** — same cause |
| Raster images | 0 `/Subtype /Image` | Pass — the 300 dpi rule is moot; the book is 100% vector + text |
| Embedded fonts | 28 `/FontFile2` (TrueType subsets) | Pass |
| Encryption / annotations | none | Pass |
| Interior page 1 | a `.cover` page (`book/build.py:92`) | **FAIL** — the interior must not contain the cover |

Note the MediaBox is 210.23 mm, not 210.00 mm. Chromium converts the `width='210mm'` argument to CSS pixels at 96 dpi (793.70 px), rounds, and converts back. This rounding drift is eliminated in §2 by specifying the page in inches that land on integer pixels.

---

## 1. Recommended trim size

**One layout serves both formats: 8.25″ × 11″ (209.55 × 279.4 mm).**

| | A4 (current) | 8.25″ × 11″ | 8.5″ × 11″ |
|---|---|---|---|
| Paperback | Standard trim | Custom trim (within 4″–8.5″ × 6″–11.69″) | Standard trim |
| **Hardcover** | **Not offered** | **Standard trim (the largest of the five)** | **Not offered** |
| Premium colour | Yes | Yes | Yes |

KDP hardcover offers exactly five trim sizes — 5.5×8.5, 6×9, 6.14×9.21, 7×10, 8.25×11 — and no custom option. A4 hardcover does not exist. 8.5×11 hardcover does not exist either. **8.25″ × 11″ is the only size in the entire KDP catalogue that is simultaneously a standard hardcover trim and reachable as a paperback trim.** A single interior PDF therefore serves both editions, which is worth real money: one layout, one proof cycle, one set of corrections.

At 218 pages both editions clear their page-count bands (hardcover premium colour 75–550; paperback premium colour 24–590 at large trims).

### How much the A4 layout must reflow

| Axis | A4 | 8.25″ × 11″ | Δ |
|---|---|---|---|
| Trim width | 210.00 mm | 209.55 mm | **−0.45 mm (−0.21%)** |
| Trim height | 297.00 mm | 279.40 mm | **−17.60 mm (−5.93%)** |
| Live content width (current `.inner` padding 16 mm) | 178.00 mm | 179.55 mm (spec below) | **+1.55 mm** |
| Live content height | 269.00 mm | 253.40 mm (spec below) | **−15.60 mm (−5.80%)** |

**Horizontally, nothing reflows.** The recipe grid in `book/style.css:139` is `grid-template-columns:62mm 1fr; gap:9mm` — the fixed 62 mm ingredient column is untouched and the extra 1.55 mm is absorbed silently by the `1fr` method column. No column, panel, or measure needs editing.

**Vertically, every page loses 15.6 mm (5.8%) of live height.** This is the entire body of work. The good news is that `book/render.py` already contains a per-page binary-search vertical justifier that trades leading, panel padding, and font size against a 4.5 mm body-to-footer target, with per-property floors (`lo` values). The 5.8% squeeze should be absorbed by that mechanism on most pages; where it bottoms out against the floors, `render.py`'s overflow report will name the page. Expect to hand-correct a minority of METHOD pages (the `.mtext` floor is 9.3 pt, only 1.1 pt of headroom below the 10.4 pt base) and to move one or two long recipes' optional content (`.notes`, `.goes`, `.wash`) rather than compress further.

**Trade-off to state plainly:** 8.25×11 paperback is not eligible for Expanded Distribution, and hardcover is never eligible for it in any size. If Expanded Distribution matters more than a hardback edition, ship the paperback at A4 or 8.5×11 and drop the hardback. It cannot be had both ways.

---

## 2. Page box dimensions

Bleed is **0.125″ (3.175 mm) on the top, bottom, and OUTER edge only** — never the gutter. So the page box is trim + 0.125″ wide and trim + 0.25″ tall, and the trim rectangle sits at a different offset on recto and verso.

| | Inches | Millimetres | PostScript points | CSS pixels @96 dpi |
|---|---|---|---|---|
| **Trim (finished book)** | 8.25 × 11 | 209.55 × 279.400 | 594 × 792 | 792 × 1056 |
| **Page box WITH bleed (submit this)** | **8.375 × 11.25** | **212.725 × 285.750** | **603 × 810** | **804 × 1080** |
| Page box WITHOUT bleed | 8.25 × 11 | 209.55 × 279.400 | 594 × 792 | 792 × 1056 |

**Submit the with-bleed size.** The design has full-bleed coloured top bars (`.topbar`, `style.css:11`) and section dividers; a no-bleed submission would print them with a white sliver of paper-shift at the edge.

**Engineering note that prevents the rounding drift seen in §0:** 8.375″ × 96 = 804.0 px exactly and 11.25″ × 96 = 1080.0 px exactly. Both land on integer CSS pixels, so Chromium will emit a MediaBox of exactly `603 × 810` pt with no drift. Specify the page in **inches**, never millimetres:

```python
await pg.pdf(path=..., width='8.375in', height='11.25in',
             print_background=True,
             margin={'top':'0','right':'0','bottom':'0','left':'0'},
             prefer_css_page_size=True)
```

and in `book/style.css`:

```css
@page { size: 8.375in 11.25in; margin: 0; }
.page { width: 8.375in; height: 11.25in; overflow: hidden; }
```

KDP's own bleed table rounds 8.375 × 11.25 to "21.26 × 28.54 cm". The exact conversion is 212.725 × 285.75 mm. Use the inch figures as authoritative; they are what the formula is defined in.

---

## 3. Margins — mirrored, recto vs verso

At 218 pages (the 151–300 band):

| Margin | KDP requirement | Measured from |
|---|---|---|
| Inside / gutter | **0.5″ (12.7 mm) exactly** | Trim edge at the spine. Bleed is never added here. |
| Outside, top, bottom | **0.375″ (9.525 mm) minimum with bleed** | See ambiguity note below |
| Outside, top, bottom | 0.25″ (6.35 mm) minimum without bleed | Trim edge |

**⚠ Unverified interpretation — confirm before submitting.** KDP does not state whether the with-bleed 0.375″ is measured from the trim line or from the edge of the enlarged bleed page. The two readings differ by 3.175 mm. Reading (A): 0.375″ from the *bleed page* edge, leaving a 0.25″ safe zone inside trim — identical to the no-bleed rule. Reading (B): 0.375″ from the *trim* line. **This specification adopts reading (B), the strictly safer one.** It costs nothing horizontally (the design already has 16 mm side padding) and only ~7 mm of vertical headroom. Confirm against a physical KDP proof copy or the KDP online previewer's safe-zone overlay before the first commercial print run; if reading (A) turns out to be correct you may recover 6.35 mm of live height, which would meaningfully relieve the tightest METHOD pages.

### Recommended design values

Distances **from the trim edge**:

| Edge | KDP floor | **Spec value** | Rationale |
|---|---|---|---|
| Inside (spine) | 12.7 mm | **14.0 mm** | 1.3 mm over the floor. A 218-page premium-colour perfect-bound block on 88–105 GSM stock has a stiff gutter; the extra 1.3 mm keeps ingredient-panel text off the curve. |
| Outside | 9.525 mm | **16.0 mm** | Inner-smaller-than-outer is the correct classical proportion — the two inner margins pair across the gutter to read as one 28 mm channel. Also gives thumbs somewhere to go in a kitchen. |
| Top | 9.525 mm | **14.0 mm** | Clears the 5 mm `.topbar` plus breathing room. |
| Bottom | 9.525 mm | **12.0 mm** | Must still contain the folio and page number — see §3.2. |

Live content box: **179.55 × 253.40 mm**, identical on both sides.

### 3.1 Mirrored `.inner` padding, expressed against the 212.725 × 285.75 mm page box

The bleed strip sits on the outer edge, which flips side. **Left and right pages therefore need different padding — this is not optional.** The current `book/style.css:10` uses a single symmetric `padding:16mm 16mm 12mm` for every page, which is a hard blocker.

| Padding | **Recto** (odd folio, right-hand) | **Verso** (even folio, left-hand) |
|---|---|---|
| `padding-top` | 3.175 + 14.0 = **17.175 mm** | **17.175 mm** |
| `padding-bottom` | 3.175 + 12.0 = **15.175 mm** | **15.175 mm** |
| `padding-left` | 0 + 14.0 = **14.000 mm** *(inside/spine)* | 3.175 + 16.0 = **19.175 mm** *(outside)* |
| `padding-right` | 3.175 + 16.0 = **19.175 mm** *(outside)* | 0 + 14.0 = **14.000 mm** *(inside/spine)* |

Implementation: stamp `data-side="recto"` / `data-side="verso"` onto each `<section class="page">` in `book/build.py:41` from the page index (after the cover is removed — page 1 is a recto), then:

```css
.page[data-side="recto"] .inner { padding: 17.175mm 19.175mm 15.175mm 14mm; }
.page[data-side="verso"] .inner { padding: 17.175mm 14mm     15.175mm 19.175mm; }
```

Do not derive side from `:nth-of-type()`; the section-divider and blank-page insertions in `build.py` make the DOM index unreliable.

### 3.2 Absolutely-positioned furniture must be re-measured

Three rules in `style.css` are positioned against the page box and will land in the bleed or the unsafe zone at the new size:

| Rule | Current | Required |
|---|---|---|
| `.topbar` (`:11`) | `top:0; left:0; right:0; height:5mm` | `height: 8.175mm` — it must extend 3.175 mm *into* the top bleed so exactly 5 mm survives above the trim line. `left:0;right:0` already covers the outer bleed correctly. |
| `.folio` (`:12`) | `bottom:6.5mm`, centred on the page box | `bottom: 12.7mm` minimum (6.5 mm from the bleed edge is inside the unsafe zone). Centring must be on the **trim** rectangle, not the page box: add `margin-left:3.175mm` on verso and `margin-right:3.175mm` on recto, or the folio sits 1.59 mm off-centre on every printed page. |
| `.pageno` (`:14`) | `right:16mm` on every page | Must flip to the outer edge: `right:16mm` on recto, `left:16mm` on verso. The value is the same on both because the outer edge is the bleed edge in both cases (16 mm from the page box = 12.825 mm from trim). |

### 3.3 Spread parity

The design gives each recipe exactly one two-page spread. A facing pair in a bound book is (even verso, odd recto). **Every recipe's plate page must therefore fall on an even page number and its method page on the following odd number.** Front matter must be padded to an even page count so the first recipe opens on a verso. Add a `verify.py` assertion that fails the build if any recipe's plate page is odd — this is the single easiest way to ship a book where every recipe is split across a page turn.

---

## 4. Interior PDF file requirements

| Requirement | Specification | Status / action |
|---|---|---|
| **PDF version** | KDP specifies **none**, and never mentions PDF/X anywhere in its documentation. It is neither required nor recommended. **Do not chase PDF/X-1a.** Chromium's native PDF 1.4 output is acceptable. | Already compliant |
| **Colour space** | KDP publishes **no interior colour-mode requirement at all** — not for premium colour, not for anything. Its only explicit CMYK instruction is for *cover* images. Advice that "KDP requires CMYK interiors" is wrong; so is "KDP officially requires sRGB". KDP is silent. Leave Chromium's native sRGB-ish device RGB alone. | No action |
| **Colour profile** | **Do not embed one.** KDP strips ICC profiles before publishing and explicitly advises against including them. No profile is named for premium colour anywhere. | Verify none is emitted |
| **Font embedding** | Mandatory. 28 `/FontFile2` subsets present (Inter static weights + Fraunces variable, both inlined as base64 `@font-face` in `book/build.py:32–35`). | Already compliant |
| **Transparency** | **Mandatory flattening. Currently failing.** See §4.1. | **Blocker** |
| **Resolution** | 300 dpi minimum (stated as spec on the guidelines pages, softened to "we recommend" on the troubleshooting page), 600 dpi recommended maximum. **Moot** — the interior contains zero raster images. | No action |
| **Page structure** | Single pages only. No 2-up spreads, despite the design being conceived in spreads. | Already compliant |
| **Cleanliness** | No crop marks, trim marks, bookmarks, comments, annotations, invisible objects, placeholder text, or metadata. Not encrypted. | Already compliant (0 `/Annots`, no `/Encrypt`) — add a build-time assertion |
| **Page count** | Must be even. 217 → 218. Control this yourself; do not let KDP insert an uncontrolled blank. | **Action** |
| **Format** | Bleed interiors **must** be PDF. DOCX/RTF/HTML uploads are accepted only for no-bleed interiors. | Already compliant |

### 4.1 Transparency flattening — the concrete recipe

The 56 transparency groups come from exactly two sources, and both are trivially pre-compositable because every alpha in the book is a single known foreground over a single known backdrop:

1. **`book/style.css`** — 14 distinct `rgba()` values, all of them `rgba(253,250,244,α)` (the cream, over the coloured cover/divider panels) plus one `rgba(255,255,255,.6)` divider rule in `.mac`; and one `opacity:.45` at `style.css:228`.
2. **`book/art/*`** — 19 SVG `opacity="…"` attributes across the illustration set. No gradients, no `mix-blend-mode`, no `filter`, no `box-shadow` anywhere in the project.

Flatten **at the source, not with a post-processor.** Add a build-time helper and pre-composite:

```python
def mix(fg, bg, a):   # returns an opaque #rrggbb
    return '#%02X%02X%02X' % tuple(round(a*f + (1-a)*b) for f, b in zip(fg, bg))
```

Call it with the backdrop that each element actually sits on — every `rgba()` in `style.css` is inside a container whose background colour is a known constant (`--cream`, `--panel`, or the per-page `topcolor` passed to `page()` at `build.py:41`). For the SVG art, resolve `opacity` against the art's own background fill in `book/art/compose.py`.

Do **not** reach for `gs -dCompatibilityLevel=1.3` as the primary route. It flattens by rasterising the affected regions, which would convert this book's entirely-vector interior into a mix of vector and raster and reintroduce the 300 dpi question you currently do not have. Keep it as a fallback only.

Add a hard gate to the build:

```bash
python3 - <<'EOF'
import re, sys
d = open('dist/The-20-Minute-Table.pdf','rb').read()
bad = {
 'transparency groups': len(re.findall(rb'/S\s*/Transparency', d)),
 'ca operators':        len(re.findall(rb'/ca\s+[0-9.]+', d)),
 'CA operators':        len(re.findall(rb'/CA\s+[0-9.]+', d)),
 'annotations':         len(re.findall(rb'/Annots', d)),
}
mb = set(re.findall(rb'/MediaBox\s*\[[^\]]*\]', d))
pages = len(re.findall(rb'/Type\s*/Page[^s]', d))
assert mb == {b'/MediaBox [0 0 603 810]'}, mb
assert pages % 2 == 0 and pages == 218, pages
assert not any(bad.values()), bad
print('interior OK:', pages, 'pages', mb)
EOF
```

---

## 5. Cover specifications

The three covers — paperback, hardback, Kindle — are **three separate artefacts**. Nothing is shared but the artwork source.

### 5.1 Spine width formula

**Premium colour: spine width = page count × 0.002347″ (0.0596 mm).** Premium colour is offered on white paper only; there is no white/cream split and therefore exactly one multiplier.

| Paper / ink | Multiplier (inches per page) |
|---|---|
| **Premium colour (white only)** | **0.002347** |
| Standard colour (white) | 0.002252 |
| B&W on white | 0.002252 |
| B&W on cream | 0.0025 |
| Groundwood | 0.00235 |

**⚠ Genuine contradiction in KDP's own documentation.** The Paperback Submission Guidelines page gives a single figure — "Color paper: page count × 0.002347″" — for all colour, while the Create a Paperback Cover page splits premium (0.002347″) from standard (0.002252″). For this book both pages agree, because we are on premium colour. No action needed here, but do not be surprised by the discrepancy.

**Worked example at 217 pages:** KDP rounds the page count up to an even number, so **compute on 218, not 217**.

```
218 × 0.002347″ = 0.5116460″ = 12.996 mm ≈ 13.0 mm
```

Do not use 217 (0.5093″). The 0.6 mm difference is inside KDP's tolerance but the printed spine will be built on 218.

### 5.2 Paperback cover — full-wrap single PDF

KDP's published formula, verbatim in structure:

```
Cover Width  = Bleed + Back Cover Width + Spine Width + Front Cover Width + Bleed
Cover Height = Bleed + Trim Height + Bleed
```

Bleed is 0.125″ (3.175 mm) on **all four sides** — unlike the interior, the cover is one continuous sheet with no bound edge, so the height gets bleed top *and* bottom.

| Component | Inches | Millimetres |
|---|---|---|
| Bleed (left) | 0.1250 | 3.175 |
| Back cover | 8.2500 | 209.550 |
| Spine (218 pp premium colour) | 0.5116 | 12.996 |
| Front cover | 8.2500 | 209.550 |
| Bleed (right) | 0.1250 | 3.175 |
| **Total width** | **17.2616″** | **438.446 mm** |
| Bleed + trim height + bleed | 0.125 + 11 + 0.125 | 3.175 + 279.400 + 3.175 |
| **Total height** | **11.2500″** | **285.750 mm** |

In points: **1242.84 × 810 pt**. If rasterised at 300 dpi: 5179 × 3375 px (round the width up; 17.2616 × 300 = 5178.5). **Prefer a vector PDF** — the artwork should be authored in the same HTML/SVG pipeline and printed by Chromium at `width='17.2616in' height='11.25in'`, which keeps the type crisp and sidesteps the dpi question entirely.

Additional cover rules:
- One continuous, **flattened** image. Same transparency rule as the interior.
- All text and critical imagery at least 0.25″ (6.35 mm) clear of the outside edge.
- Borders and frames are discouraged — KDP documents a **0.125″ spine-shift tolerance**, so a symmetrical border will visibly drift on the printed copy. Design the spine so that a 3 mm shift is invisible: no hairline rules parallel to the spine folds, no type that runs right to the hinge.
- Spine text is permitted (79-page minimum, 80 if using Cover Creator). At 218 pages this is comfortably clear.
- CMYK is the one place KDP explicitly asks for it — **cover images only**.

### 5.3 Hardback cover — do not hand-derive

**KDP publishes no hardcover cover formula.** The Create a Hardcover Cover page documents only the components and explicitly defers to the cover calculator. Any formula you find in a blog post is reverse-engineered guesswork.

The three geometry constants KDP does publish:

| Constant | Value |
|---|---|
| Wrap past the front cover edge | 0.51″ (15 mm) |
| Spine hinge, each side | 0.4″ (10 mm) |
| Safe distance for all text/images from the book edge | 0.635″ (16 mm) |

The case is larger than the trim size because the printed sheet wraps a ~2 mm solid case board that overhangs the text block and turns in to be glued to the endpaper, plus two hinge channels flanking the spine.

**Process:**
1. Go to the KDP cover calculator. Enter: hardcover, trim 8.25″ × 11″, page count **218**, premium colour, white paper.
2. Download the generated PNG/PDF template. It carries the exact case dimensions, hinge channels, wrap allowance, and barcode box for *this* book.
3. Author the cover art in the pipeline as a **resolution-independent HTML/SVG source with no fixed outer dimension** — a background that tiles or scales, with the title block positioned relative to the front panel rather than the sheet. Then render it to whatever size the template specifies and composite.
4. Keep all type ≥ 0.635″ (16 mm) from every book edge, and off the two 0.4″ hinge channels — type that lands in a hinge is creased.

Do not size the hardback artwork from the paperback numbers. The hardcover case will be materially larger than 17.2616 × 11.25 in both axes, and the exact figure is not something this specification can supply without inventing precision.

### 5.4 Kindle cover — a third, unrelated artefact

| Property | Requirement |
|---|---|
| Format | JPEG or TIFF (not PDF) |
| Ideal size | 2560 × 1600 px |
| Minimum | 1000 × 625 px |
| Maximum | 10,000 px per side |
| Aspect ratio | height:width at least 1.6:1 |
| Colour | RGB |
| File size | under 50 MB |

Front cover only. No spine, no back, no bleed.

### 5.5 Business-critical number to confirm before pricing

**⚠ Unverified — confirm in the KDP printing-cost calculator before setting a list price.** Research reports premium colour at large trim on Amazon.com as a $1.00 fixed cost plus **$0.080 per page**. At 218 pages that is **$18.44 of print cost per paperback copy**. KDP paperback royalty is 60% of list minus print cost, so break-even list price would be roughly **$30.73**, before any margin at all. The hardback will be higher still.

This is the number most likely to change the shape of the project. At $0.08/page, every page you can remove is worth $0.08 per copy sold. Run the real figures in KDP's calculator for both editions and all target marketplaces **before** committing to a 218-page premium-colour build. If the economics do not work, the levers in order of impact are: reduce page count, switch to standard colour (reported $0.0402/page at large trim — roughly half), or drop to a smaller trim. Note that **ink and paper type are locked permanently after publication** — you can never switch a published title between premium colour, standard colour, and black-and-white, and paper-type switching is unavailable for any colour title. Get this right the first time.

---

## 6. Required front matter for print

The interior currently opens with a cover page (`build.py:92`). **Remove it.** KDP prints the cover from the separate cover file; a duplicate cover as interior page 1 wastes two pages of premium-colour printing, breaks recto/verso parity for the entire book, and looks amateurish in the Look Inside preview.

Suggested sequence. Page 1 is always a recto (right-hand page); versos are even.

| Page | Side | Content | Status |
|---|---|---|---|
| 1 | recto | **Half title** — book title alone, set large | New |
| 2 | verso | Blank, or frontispiece illustration | New |
| 3 | recto | **Title page** — title, subtitle, author, imprint/publisher name | New |
| 4 | verso | **Copyright page** — see below | New |
| 5 | recto | **Dedication** (optional but conventional) | New |
| 6 | verso | Blank | New |
| 7–8 | recto/verso | **Contents** | Exists (`build.py:262`, `:301`, `:308`) |
| 9+ | recto | Introduction / "How to use this book" / the pantry and method pages | Exists (`build.py:124`–`:359`) |
| … | verso | First recipe plate begins — **must be even** | Pagination assertion |

Back matter (existing, keep): recipe index (`build.py:536`), category index, allergen and conversion tables, about the author, colophon.

### Copyright page — required contents

- Full title and subtitle
- `Copyright © 2026 [Author name]`
- `All rights reserved.` plus the standard no-reproduction-without-permission sentence
- Moral rights / right-to-be-identified assertion (relevant if selling into the UK/EU)
- **Edition and printing statement** — `First edition, 2026`
- **ISBN.** Each format needs its own. Paperback and hardback each require a distinct ISBN — either KDP-assigned free ISBNs or your own from the national agency. The Kindle edition uses an Amazon ASIN and needs no ISBN. Note that KDP-assigned ISBNs list Amazon as the publisher of record and cannot be moved to another printer; buy your own if you may ever print elsewhere.
- **Disclaimer** — for a cookbook, a short notice covering allergens, dietary suitability, and food-safety responsibility. Nutrition figures, if printed, should be flagged as approximate.
- Design and typesetting credit; typeface credits (Fraunces and Inter, both SIL Open Font License — the OFL does not require attribution in the book, but state it if you wish)
- Website / contact

**Do not** print internal page-number cross-references generated at build time into the copyright or contents pages without regenerating them after the reflow to 8.25×11 — the vertical squeeze will move content across page boundaries.

---

## 7. Kindle edition

### Recommended format: **reflowable EPUB3**. Not fixed-layout. Not Print Replica.

**Why reflowable.** KDP's operative test is verbatim: a book converts as reflowable "when the body text can be easily separated from the images without losing any context or important layout design." A recipe decomposes cleanly into title, ingredient list, numbered method, and an accompanying illustration. The two-page spread is a print-production convention, not semantic content. KDP's Comparing Formats page reserves fixed-layout for children's picture books, coffee-table books, comics, and "image-heavy books with large text" — this is a text-driven book with supporting illustration.

**Why not fixed-layout.** The decisive argument is the phone. KDP requires capital letters at least 2 mm high measured on a 7″ device for non-children's fixed-layout books. An 8.25″ × 11″ page scaled to a ~6″ phone is roughly a 4× linear reduction; body text set at 8.5–10.4 pt lands well under 1 mm cap height. It would be functionally unreadable on the device where most Kindle-app reading happens. Beyond that, every fixed-layout variant loses **user font settings** (no reader-controlled size, font, colour, margins, spacing, or alignment) and **screen-reader / refreshable-braille support** — a real accessibility loss for a book read hands-free in a kitchen.

**Correction to a claim you may have seen:** Enhanced Typesetting is **not** lost in fixed-layout — KDP's chart reads "Yes" for reflowable and for all three fixed-layout variants and Print Replica alike. Drop it from the argument. Likewise, "Fixed Layout without Pop-Ups" retains dictionary look-up, highlighting, word search **and** X-Ray. The honest loss list for fixed-layout is exactly two items: user font settings and screen-reader support. And the reflowable feature list should be quoted with its qualifiers — "dictionary, X-Ray (when available), text-to-speech (when available), Word Wise (when available), Kindle Real Page Numbers (when available)."

**Why not Print Replica.** Unavailable on iOS and on standard Kindle e-readers. Feeding the existing PDF to Kindle Create is the wrong route.

**MOBI is dead.** Reflowable support ended 1 August 2021; fixed-layout support ended March 2025. Do not generate it.

**Kindle Create is not worth using here.** It imports only DOC/DOCX for reflowable output, cannot edit inline images or tables in-app, and would discard the structured markdown pipeline entirely.

### What to generate from the markdown sources

Author EPUB3 directly from `/Users/nawazdhandala/Projects/HackerBay/twenty-minute-table/recipie/recipes/*.md` via a new `book/epub.py`, reusing `book/parse.py`. Do **not** derive it from `build/cookbook.html` — that file is print geometry.

| Element | Specification |
|---|---|
| Structure | One XHTML file per recipe (100 files) plus front/back matter. Single-column, one recipe flowing continuously. |
| Navigation | **EPUB3 nav document** as the logical TOC (NCX only as an EPUB2 fallback), plus an HTML TOC near the front. **Maximum two levels of nesting.** This is the highest-leverage thing to get right. |
| Headings | Semantic `<h1>`/`<h2>`/`<h3>` from the markdown. Give headings **explicit `text-align`** — Kindle's defaults differ from browsers'. |
| Body text | Must stay at **`1em`**. Never set an absolute body size. Set fonts on `<body>`, not on individual paragraphs. |
| Ingredients | `<ul>`; method steps `<ol>`. Not tables. |
| Images | **JPEG or PNG only.** No TIFF, no multi-frame GIF, **no transparency**, sRGB. Pictorial images should fill ≥60% of screen width; images containing text ≥80%. The SVG hero art in `book/art/` must be rasterised to JPEG at a target width of ~1200 px. |
| Full-bleed panels and dividers | **Cannot survive the conversion.** The coloured `.topbar`, the bleeding section dividers, and the panel-behind-ingredients treatment must be redesigned as typographic devices (rules, small caps, spacing) or dropped. Do not attempt to fake bleed with negative margins. |
| Hard limits | 650 MB maximum upload, 8,000 pages maximum. Not a constraint here. |

### File size is directly load-bearing on margin

Delivery cost under the 70% royalty option is **US $0.15/MB on the converted file size**, deducted *after* the 70% is computed.

| Converted size | Delivery cost | Royalty at $12.99 list |
|---|---|---|
| 15 MB | $2.25 | $9.09 − $2.25 = **$6.84** |
| 25 MB | $3.75 | $9.09 − $3.75 = **$5.34** |
| 60 MB | $9.00 | $9.09 − $9.00 = **$0.09** |

**Target 15–25 MB.** At 100 recipes that is a budget of roughly 150–250 KB per illustration. Compress aggressively, and check the converted size KDP reports in the preview step *before* setting the price. The US 70% band is now $2.99–$12.99, expanded from $9.99 effective 7 July 2026.

### KDP Select

**A freely downloadable PDF of this book on the author's own site is a direct breach of KDP Select exclusivity.** KDP states plainly that during exclusivity "you cannot distribute your book digitally anywhere else, including on your website, blogs, etc." A PDF is a digital format; the print-format exception does not rescue it. This repository ships a Firebase-hosted site (`firebase.json`, `book/site.py`, `.firebaserc`) — if that site serves the PDF, either take it down before enrolling or skip Select.

**Skipping Select is cheaper than it looks.** The 70% royalty in the US, UK, and EU is **not** conditional on enrolment. Only Brazil, Japan, Mexico, and India require Select for 70%. What you forfeit is Kindle Unlimited page reads and Countdown Deals. For a book with a free companion website driving traffic, keeping the site is likely the better trade.

### Validation chain

`epubcheck` → **Kindle Previewer 3** (opens `.epub` natively; check phone, 6″ e-reader, and tablet profiles) → upload and read the converted file size KDP reports → *then* set the price.

---

## 8. Ordered implementation plan

**Phase 0 — Decide, before writing code**
1. Run the real print costs for 8.25″ × 11″ premium colour at 218 pages in the KDP printing-cost calculator, for paperback *and* hardcover, in every target marketplace. Confirm or refute the $0.080/page figure in §5.5. If the economics fail, resolve trim/ink now — ink and paper are locked forever at publication.
2. Confirm the with-bleed margin datum (§3, reading A vs B) using the KDP previewer's safe-zone overlay.
3. Decide Expanded Distribution vs hardback edition (§1).
4. Decide KDP Select vs the public website (§7).

**Phase 1 — Interior geometry**
5. `book/render.py`: change the `pg.pdf()` call to `width='8.375in', height='11.25in'`. Add `@page { size: 8.375in 11.25in; margin: 0 }` to `book/style.css` and change `.page` to `width:8.375in; height:11.25in`.
6. `book/build.py:41` (`page()`): stamp `data-side="recto"|"verso"` from the page index. Remove the cover page at `build.py:92`.
7. `book/style.css:10`: replace the symmetric `.inner` padding with the two mirrored rules in §3.1.
8. Fix `.topbar` height to 8.175 mm, `.folio` to `bottom:12.7mm` with trim-centred offset, `.pageno` to flip left/right by side (§3.2).
9. Run `python3 book/render.py --nopdf`. Read the overflow report. Expect a batch of failures — this is the 5.8% vertical squeeze landing.

**Phase 2 — Absorb the vertical reflow**
10. For each overflowing page, in order of preference: let the existing justifier in `render.py` do its work; lower a `lo` floor only where the typography can bear it (`.mtext` has the least headroom); move optional content (`.notes`, `.goes`, `.wash`) to the facing page; only then re-edit the recipe copy.
11. Re-run until `overflowing: 0` and the reported minimum body-to-footer slack is ≥ 2 mm.

**Phase 3 — Front matter and pagination**
12. Author half title, title page, copyright page, dedication (§6). Pad front matter to an even count.
13. Land the interior on exactly **218** pages.
14. Add a `book/verify.py` assertion: every recipe plate page number is even, and its method page is the next odd number.
15. Regenerate the contents and indexes against the new pagination.

**Phase 4 — Flattening and file gate**
16. Add the `mix()` helper; pre-composite all 14 `rgba()` values and the `opacity:.45` in `style.css` against their known backdrops.
17. Pre-composite the 19 SVG `opacity` attributes in `book/art/`.
18. Add the assertion script from §4.1 to the `book` target in the `Makefile`. It must fail the build on any transparency group, alpha operator, wrong MediaBox, or odd page count.
19. Confirm no ICC profile is embedded.

**Phase 5 — Covers**
20. Build the paperback wrap at **17.2616″ × 11.25″** with a **0.5116″** spine, rendered through the same Chromium pipeline. Keep all type 0.25″ clear of the outer edge and design the spine to tolerate a 0.125″ shift.
21. Generate the hardcover template from the KDP cover calculator (8.25×11, 218 pp, premium colour). Composite the artwork onto it. Do not hand-derive the size.
22. Export the Kindle front cover at 2560 × 1600 px RGB JPEG.

**Phase 6 — Proof**
23. Upload the interior and paperback cover. Work through every KDP previewer warning.
24. **Order a physical proof of both editions.** Verify with a ruler: the gutter, the bleed on all three edges, the folio position, and that no ingredient panel text falls into the spine curve. This is the only way to settle the §3 margin ambiguity for certain.
25. Repeat for the hardcover.

**Phase 7 — Kindle**
26. Write `book/epub.py` generating EPUB3 from `recipes/*.md` via `book/parse.py`, per §7.
27. Rasterise the illustration set to sRGB JPEG, no transparency, ~1200 px wide, budget 150–250 KB each.
28. `epubcheck` → Kindle Previewer 3 (phone, 6″ e-reader, tablet) → upload → **read KDP's reported converted file size** → set the price.

---

## Numbers this specification could not verify against a primary source

Confirm each of these in KDP before submitting:

| Item | Where it appears | Why it is uncertain |
|---|---|---|
| With-bleed margin datum: 0.375″ from trim, or from the bleed page edge | §3 | KDP does not state which. Adopted the safer reading. Worth 6.35 mm of live height. |
| Premium colour print cost: $1.00 + $0.080/page at large trim | §5.5 | Not verified against a primary source, and it determines whether the project is viable at all. |
| Hardcover case dimensions | §5.3 | KDP publishes no formula. Must come from the cover calculator. |
| Colour spine multiplier for standard vs premium | §5.1 | KDP's two help pages contradict each other. Immaterial here (premium is unambiguous at 0.002347″), but do not generalise. |
| Expanded Distribution ineligibility for 8.25×11 paperback | §1 | Reported, not independently confirmed. Check in the KDP dashboard if ED matters. |
| Paperback premium colour page ceiling at custom 8.25×11 (reported 24–590 for 8.5×11-class trims) | §1 | 218 is far inside any reported band, so this is not a live risk — but confirm if the page count ever grows past ~580. |


---

## Corrections the verify pass made

- **Wrong:** Fixed-layout gives up text resizing AND screen-reader support; reflowable retains X-Ray, Word Wise, dictionary, text-to-speech and full Enhanced Typesetting
  **Correction:** Accurate version: Per KDP's current "Comparing Formats" page, every fixed-layout variant loses user font settings (no reader-controlled size, font, color, margins, spacing, alignment) and screen-reader/refreshable-braille support, while reflowable supports both. That much is correct and is a genuine functional loss for a cookbook read hands-free in a kitchen.

But Enhanced Typesetting is NOT lost: the chart's "Supports Enhanced Typesetting" column reads "Yes" for reflowable and for all three fixed-layout formats (and Print Replica). Drop it from the loss list.

And if the cookbook is built as "Fixed Layout without Pop-Ups" — the variant KDP scopes to "image-heavy books with large text" — it retains dictionary look-up, highlighting, word search AND X-Ray. The only documented losses on that path are user font settings and screen-reader support, plus KDP's own constraint that it is "only for use on books with type large enough to be read on all devices without magnification" (on a 7" tablet, capitals in body text at least 2mm high in non-children's books).

Finally, the reflowable feature list should be quoted with its qualifiers: "dictionary, X-Ray (when available), text-to-speech (when available), Word Wise (when available), Kindle Real Page Numbers (when available)."
