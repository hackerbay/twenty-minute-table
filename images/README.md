# Photographs

Drop photographs in here and the build uses them in place of the generated
illustrations. Nothing is required — with this folder empty, every recipe gets
a composed line-art flat lay instead.

| File | Where it appears |
|---|---|
| `07-hero.jpg` | full-width picture at the top of recipe 07's plate page |
| `07-step-3.jpg` | replaces the action glyph beside step 3 of recipe 07 |

Use the two-digit recipe number, zero-padded, exactly as it appears in
`recipes/`. `.jpg`, `.jpeg`, `.png` and `.webp` all work.

Heroes are cropped to fill a box roughly 178 × 88 mm, so landscape shots at
2000 px wide or more are ideal. Step photographs are cropped to a circle, so
keep the subject centred. Images are embedded in the PDF as base64, so large
files make a large book — 200–400 KB each is plenty.
