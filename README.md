# The 20-Minute Table

**Seventy fast, whole-food recipes**, typeset into a printable 151-page A4 cookbook.

Nothing takes over twenty minutes from a cold start. Everything is built on unprocessed
ingredients. Every recipe is designed to leave one pan or one basket behind — the
washing-up line at the foot of each spread is the constraint the recipe was written around.

📕 **[dist/The-20-Minute-Table.pdf](dist/The-20-Minute-Table.pdf)**

| | |
|---|---|
| Recipes | 70 — 50 lunch & dinner, 20 breakfast |
| Cuisines | 45 |
| Air fryer | 20 |
| One pan | 35 |
| Wok | 7 |
| No cook | 8 |
| Fastest | 8 minutes |
| Slowest | 20 minutes |
| Serves | 4 throughout |
| Pages | 151 |

Metric quantities first, US cups and ounces alongside.

## Every recipe is a spread

**The plate page** carries an illustration, the title block with a twenty-minute time dial,
the hook, the full ingredient list and the one piece of technique that makes the dish work,
then the nutrition strip and the washing-up line.

**The method page** carries the numbered steps, each with an action pictogram matched to what
the step actually asks you to do, and the swap / faster / bulk / leftovers notes.

## Illustrations, and how to replace them with photographs

There are no stock photographs in this book. Each plate page gets a flat-lay illustration
composed at build time from the recipe's own ingredient list: `book/art/compose.py` matches
each ingredient line against a rule table, picks up to nine icons from a library of 72
hand-drawn line-art foods, sorts them so the star ingredient is largest, and scatters them
with a seed derived from the recipe number — so a given recipe always draws the same picture.
Method steps are matched the same way against 20 action pictograms.

To use real photographs instead, drop them into `images/` as `NN-hero.jpg` and
`NN-step-K.jpg`. The build picks them up automatically and falls back to the illustration
for anything you have not shot. See [images/README.md](images/README.md).

## Layout

```
recipes/     70 markdown recipe cards, numbered 01-70 — the source of truth
images/      optional photographs; empty by default
book/        the typesetter
  parse.py     markdown -> structured recipe data
  build.py     recipe data -> a single self-contained cookbook.html
  render.py    html -> PDF via headless Chromium, with a vertical-justification pass
  style.css    the print stylesheet
  icons.py     method icons, the time dial, the page-anatomy diagram
  verify.py    consistency checks across all 70 recipe files
  art/
    food_a-f.py  the 72-icon ingredient library, drawn on a 48x48 grid
    food.py      merged library plus a few redraws
    actions.py   20 cooking-action pictograms
    compose.py   ingredient -> icon rules, flat-lay layout, step -> glyph rules
    preview.py   renders any icon module to a labelled PNG grid for review
dist/        the built PDF
build/       intermediate HTML (gitignored)
```

## Building

```bash
npm install        # fonts (Fraunces + Inter, embedded as base64 in the HTML)
make verify        # check every recipe file against the template
make build         # markdown -> HTML -> PDF
```

Requires Python 3 with `playwright` and a Chromium build available to it.

Edit any file in `recipes/` and rerun `make` — the contents pages, both cuisine indexes,
the page numbers and the cover statistics all regenerate from the recipe files themselves.

To review the icon library after editing it:

```bash
cd book/art && python3 preview.py food /tmp/food.png
```

## How a recipe file is structured

Every file follows the same template, and `verify.py` enforces it: heading with number and
title, a meta line (cuisine, method, total time, serves), a one-line hook, *Why it works*,
*Ingredients*, *Method*, *Chef's notes* (swap / make it faster / bulk it out / leftovers),
a nutrition table, and a *Washing up* line. `verify.py` also checks the macro arithmetic,
that no recipe exceeds twenty minutes, and that no two recipes share a title.

## The typesetting

Each recipe occupies exactly two A4 pages, and recipes vary a lot in length. Before printing,
`render.py` runs a vertical-justification pass in the browser: for each page it binary-searches
a single parameter that expands or tightens a set of levers — the height of the hero image, the
leading between steps and ingredients, panel padding, and on the densest method pages the body
size itself — until the content sits a consistent 4.5 mm above the footer block. Long ingredient
lists switch to a two-column panel automatically. The result is that the nutrition strip lands in
the same place on all 70 plate pages, with no page overflowing and none conspicuously empty.

---

## Lunch & Dinner

| # | Recipe | Cuisine | Method | Time | Page |
|---|---|---|---|---|---|
| 01 | [Harissa Chickpea & Cauliflower Crunch](recipes/01-harissa-chickpea-cauliflower-crunch.md) | Tunisian / North African | Air Fryer | 18 min | 10 |
| 02 | [Miso-Glazed Salmon with Charred Tenderstem](recipes/02-miso-glazed-salmon-charred-tenderstem.md) | Japanese | Air Fryer | 12 min | 12 |
| 03 | [Peri-Peri Chicken Thighs with Blistered Peppers](recipes/03-peri-peri-chicken-blistered-peppers.md) | Portuguese-Mozambican | Air Fryer | 18 min | 14 |
| 04 | [Tandoori Paneer Tikka Skewers](recipes/04-tandoori-paneer-tikka-skewers.md) | Indian | Air Fryer | 15 min | 16 |
| 05 | [Gochujang Tofu with Smashed Sesame Cucumber](recipes/05-gochujang-tofu-smashed-cucumber.md) | Korean | Air Fryer | 18 min | 18 |
| 06 | [Za'atar Chicken with Lemon Courgette](recipes/06-zaatar-chicken-lemon-courgette.md) | Levantine | Air Fryer | 18 min | 20 |
| 07 | [Chilli-Lime Prawns with Avocado & Coriander](recipes/07-chilli-lime-prawns-avocado.md) | Mexican | Air Fryer | 10 min | 22 |
| 08 | [Sicilian Sea Bass with Fennel, Olive & Orange](recipes/08-sicilian-sea-bass-fennel-orange.md) | Italian (Sicilian) | Air Fryer | 14 min | 24 |
| 09 | [Jerk Chicken with Charred Pineapple](recipes/09-jerk-chicken-charred-pineapple.md) | Jamaican | Air Fryer | 18 min | 26 |
| 10 | [Shawarma-Spiced Turkey with Sumac Onions](recipes/10-shawarma-turkey-sumac-onions.md) | Middle Eastern | Air Fryer | 15 min | 28 |
| 11 | [Berbere Sweet Potato & Lentil Bowl](recipes/11-berbere-sweet-potato-lentil-bowl.md) | Ethiopian | Air Fryer | 20 min | 30 |
| 12 | [Cajun Blackened Cod with Charred Corn Salsa](recipes/12-cajun-blackened-cod-corn-salsa.md) | American (Louisiana) | Air Fryer | 12 min | 32 |
| 13 | [Furikake Salmon Rice Bowl](recipes/13-furikake-salmon-rice-bowl.md) | Hawaiian-Japanese | Air Fryer | 15 min | 34 |
| 14 | [Chermoula Prawns with Courgette Ribbons](recipes/14-chermoula-prawns-courgette-ribbons.md) | Moroccan | Air Fryer | 12 min | 36 |
| 15 | [Salt & Pepper Tofu with Pak Choi](recipes/15-salt-pepper-tofu-pak-choi.md) | Chinese (Cantonese) | Air Fryer | 18 min | 38 |
| 16 | [Pad Krapow — Thai Basil Chicken](recipes/16-pad-krapow-thai-basil-chicken.md) | Thai | One Pan | 12 min | 40 |
| 17 | [Quick Thai Green Curry Prawns](recipes/17-thai-green-curry-prawns.md) | Thai | One Pan | 15 min | 42 |
| 18 | [Ginger-Garlic Prawn & Broccoli Stir-Fry](recipes/18-ginger-garlic-prawn-broccoli-stirfry.md) | Chinese | Wok | 10 min | 44 |
| 19 | [Sichuan Cumin Beef with Peppers](recipes/19-sichuan-cumin-beef-peppers.md) | Chinese (Sichuan) | Wok | 12 min | 46 |
| 20 | [Korean Bulgogi Beef Bowl](recipes/20-korean-bulgogi-beef-bowl.md) | Korean | One Pan | 15 min | 48 |
| 21 | [Vietnamese Lemongrass Chicken Bowl](recipes/21-vietnamese-lemongrass-chicken-bowl.md) | Vietnamese | One Pan | 15 min | 50 |
| 22 | [Shogayaki — Japanese Ginger Pork with Cabbage](recipes/22-shogayaki-ginger-pork-cabbage.md) | Japanese | One Pan | 12 min | 52 |
| 23 | [Kerala Coconut Prawn Fry](recipes/23-kerala-coconut-prawn-fry.md) | Indian (South) | One Pan | 15 min | 54 |
| 24 | [Egg & Spinach Bhurji](recipes/24-egg-spinach-bhurji.md) | Indian | One Pan | 10 min | 56 |
| 25 | [Fifteen-Minute Chana Masala](recipes/25-fifteen-minute-chana-masala.md) | Indian | One Pan | 15 min | 58 |
| 26 | [Turkish Menemen](recipes/26-turkish-menemen.md) | Turkish | One Pan | 12 min | 60 |
| 27 | [Green Shakshuka](recipes/27-green-shakshuka.md) | Israeli / Levantine | One Pan | 15 min | 62 |
| 28 | [Greek Lemon Chicken & Orzo](recipes/28-greek-lemon-chicken-orzo.md) | Greek | One Pan | 20 min | 64 |
| 29 | [Prawn Saganaki with Feta](recipes/29-prawn-saganaki-feta.md) | Greek | One Pan | 15 min | 66 |
| 30 | [Broccoli Aglio e Olio with Anchovy](recipes/30-broccoli-aglio-e-olio-anchovy.md) | Italian | One Pan | 15 min | 68 |
| 31 | [Tuscan White Bean, Kale & Lemon Skillet](recipes/31-tuscan-white-bean-kale-skillet.md) | Italian (Tuscan) | One Pan | 12 min | 70 |
| 32 | [Tuna Puttanesca Beans](recipes/32-tuna-puttanesca-beans.md) | Italian | One Pan | 12 min | 72 |
| 33 | [Gambas al Ajillo with Chickpeas](recipes/33-gambas-al-ajillo-chickpeas.md) | Spanish | One Pan | 12 min | 74 |
| 34 | [Smoky Paprika Chicken with Piquillo Peppers](recipes/34-smoky-paprika-chicken-piquillo.md) | Spanish | One Pan | 18 min | 76 |
| 35 | [Chipotle Black Bean & Charred Corn Skillet](recipes/35-chipotle-black-bean-charred-corn.md) | Mexican | One Pan | 15 min | 78 |
| 36 | [Lomo Saltado](recipes/36-lomo-saltado.md) | Peruvian | Wok | 15 min | 80 |
| 37 | [Moqueca Express — Brazilian Coconut Fish Stew](recipes/37-moqueca-express-brazilian-fish.md) | Brazilian | One Pan | 18 min | 82 |
| 38 | [Filipino Adobo Flash Chicken](recipes/38-filipino-adobo-flash-chicken.md) | Filipino | One Pan | 18 min | 84 |
| 39 | [Nasi Goreng Cauliflower Rice with Fried Egg](recipes/39-nasi-goreng-cauliflower-rice.md) | Indonesian | Wok | 15 min | 86 |
| 40 | [Sambal Green Beans with Egg](recipes/40-sambal-green-beans-egg.md) | Malaysian | Wok | 12 min | 88 |
| 41 | [Burmese Golden Turmeric Chicken](recipes/41-burmese-golden-turmeric-chicken.md) | Burmese | One Pan | 15 min | 90 |
| 42 | [Ethiopian Gomen with Spiced Eggs](recipes/42-ethiopian-gomen-spiced-eggs.md) | Ethiopian | One Pan | 15 min | 92 |
| 43 | [Ras el Hanout Turkey with Herbs & Almonds](recipes/43-ras-el-hanout-turkey-almonds.md) | Moroccan | One Pan | 15 min | 94 |
| 44 | [West African Peanut Stew Express](recipes/44-west-african-peanut-stew.md) | Ghanaian / Senegalese | One Pan | 20 min | 96 |
| 45 | [Georgian Walnut-Garlic Green Beans with Eggs](recipes/45-georgian-walnut-garlic-green-beans.md) | Georgian | One Pan | 15 min | 98 |
| 46 | [Deconstructed Vietnamese Summer Roll Bowl](recipes/46-vietnamese-summer-roll-bowl.md) | Vietnamese | No Cook | 15 min | 100 |
| 47 | [Fattoush with Crisped Chickpeas](recipes/47-fattoush-crisped-chickpeas.md) | Lebanese | No Cook | 15 min | 102 |
| 48 | [Salmon Poke Bowl](recipes/48-salmon-poke-bowl.md) | Hawaiian-Japanese | No Cook | 12 min | 104 |
| 49 | [Prawn Ceviche Tostada Salad](recipes/49-prawn-ceviche-tostada-salad.md) | Peruvian-Mexican | No Cook | 15 min | 106 |
| 50 | [Turkish Çoban Salad with Tuna & Sumac](recipes/50-turkish-coban-salad-tuna-sumac.md) | Turkish | No Cook | 10 min | 108 |

## Breakfast

| # | Recipe | Cuisine | Method | Time | Page |
|---|---|---|---|---|---|
| 51 | [Sweet Potato, Egg & Chilli Hash](recipes/51-sweet-potato-egg-chilli-hash.md) | American | Air Fryer | 18 min | 111 |
| 52 | [Halloumi, Tomato & Za'atar Plate](recipes/52-halloumi-tomato-zaatar-plate.md) | Cypriot | Air Fryer | 12 min | 113 |
| 53 | [Masala Omelette Muffins](recipes/53-masala-omelette-muffins.md) | Indian | Air Fryer | 15 min | 115 |
| 54 | [Banana, Oat & Almond Butter Bake](recipes/54-banana-oat-almond-butter-bake.md) | British | Air Fryer | 18 min | 117 |
| 55 | [Crispy Chickpea, Avocado & Lemon Toast](recipes/55-crispy-chickpea-avocado-lemon-toast.md) | Modern Levantine | Air Fryer | 12 min | 119 |
| 56 | [Tamagoyaki with Rice & Nori](recipes/56-tamagoyaki-rice-nori.md) | Japanese | One Pan | 12 min | 121 |
| 57 | [Gyeran Bap — Korean Egg Rice](recipes/57-gyeran-bap-korean-egg-rice.md) | Korean | One Pan | 10 min | 123 |
| 58 | [Ten-Minute Ginger Congee](recipes/58-ten-minute-ginger-congee.md) | Chinese | One Pan | 15 min | 125 |
| 59 | [Rava Uttapam with Coconut Chutney](recipes/59-rava-uttapam-coconut-chutney.md) | Indian (South) | One Pan | 18 min | 127 |
| 60 | [Persian Herb & Feta Omelette](recipes/60-persian-herb-feta-omelette.md) | Iranian | One Pan | 15 min | 129 |
| 61 | [Huevos Rancheros Rápidos](recipes/61-huevos-rancheros-rapidos.md) | Mexican | One Pan | 15 min | 131 |
| 62 | [Pan con Tomate with Soft Eggs](recipes/62-pan-con-tomate-soft-eggs.md) | Spanish | One Pan | 10 min | 133 |
| 63 | [Ful Medames](recipes/63-ful-medames.md) | Egyptian | One Pan | 12 min | 135 |
| 64 | [Buckwheat Galette with Egg & Greens](recipes/64-buckwheat-galette-egg-greens.md) | French (Breton) | One Pan | 18 min | 137 |
| 65 | [Khao Tom — Thai Rice Soup with Prawns](recipes/65-khao-tom-thai-rice-soup-prawns.md) | Thai | One Pan | 15 min | 139 |
| 66 | [Egg & Tomato Stir-Fry](recipes/66-egg-tomato-stir-fry.md) | Chinese | Wok | 10 min | 141 |
| 67 | [Sinangag — Filipino Garlic Rice & Egg](recipes/67-sinangag-filipino-garlic-rice-egg.md) | Filipino | Wok | 12 min | 143 |
| 68 | [Ten-Minute Bircher Muesli](recipes/68-ten-minute-bircher-muesli.md) | Swiss | No Cook | 10 min | 145 |
| 69 | [Danish Rye with Cottage Cheese, Cucumber & Dill](recipes/69-danish-rye-cottage-cheese-dill.md) | Danish | No Cook | 8 min | 147 |
| 70 | [Orange, Date & Almond Yoghurt Bowl](recipes/70-orange-date-almond-yoghurt-bowl.md) | Moroccan | No Cook | 8 min | 149 |

## By cuisine

- **American** — 51
- **American (Louisiana)** — 12
- **Brazilian** — 37
- **British** — 54
- **Burmese** — 41
- **Chinese** — 18, 58, 66
- **Chinese (Cantonese)** — 15
- **Chinese (Sichuan)** — 19
- **Cypriot** — 52
- **Danish** — 69
- **Egyptian** — 63
- **Ethiopian** — 11, 42
- **Filipino** — 38, 67
- **French (Breton)** — 64
- **Georgian** — 45
- **Ghanaian / Senegalese** — 44
- **Greek** — 28, 29
- **Hawaiian-Japanese** — 13, 48
- **Indian** — 04, 24, 25, 53
- **Indian (South)** — 23, 59
- **Indonesian** — 39
- **Iranian** — 60
- **Israeli / Levantine** — 27
- **Italian** — 30, 32
- **Italian (Sicilian)** — 08
- **Italian (Tuscan)** — 31
- **Jamaican** — 09
- **Japanese** — 02, 22, 56
- **Korean** — 05, 20, 57
- **Lebanese** — 47
- **Levantine** — 06
- **Malaysian** — 40
- **Mexican** — 07, 35, 61
- **Middle Eastern** — 10
- **Modern Levantine** — 55
- **Moroccan** — 14, 43, 70
- **Peruvian** — 36
- **Peruvian-Mexican** — 49
- **Portuguese-Mozambican** — 03
- **Spanish** — 33, 34, 62
- **Swiss** — 68
- **Thai** — 16, 17, 65
- **Tunisian / North African** — 01
- **Turkish** — 26, 50
- **Vietnamese** — 21, 46
