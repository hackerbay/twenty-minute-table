# The 20-Minute Table

**100 fast, whole-food recipes for new parents**, published two ways: a printable 217-page
A4 cookbook and a static website you can host anywhere.

Written for the stretch of life when dinner has to happen anyway: a small person who needs
feeding at six, an adult who has not eaten properly since breakfast, and about twenty minutes
between the two. Nothing takes over twenty minutes from a cold start. Everything is built on
unprocessed ingredients. The lunches and dinners are proper main courses — the starch is in
the recipe, not in a footnote — every one leaves a single pan or basket behind, and every one
ends by telling you how to lift a toddler's portion out of that same pan.

📕 **[dist/The-20-Minute-Table.pdf](dist/The-20-Minute-Table.pdf)** &nbsp;·&nbsp; 🌐 **[site/](site/)** — open `site/index.html`

| | |
|---|---|
| Recipes | 100 |
| Lunch & dinner | 50, all 600–780 kcal a serving |
| Sides | 15, all under 15 minutes |
| Breakfast | 20 |
| Something afterwards | 15, all under 320 kcal |
| Cuisines | 49 |
| Vegetarian | 54, marked throughout |
| Air fryer / one pan / wok / no cook | 30 / 44 / 7 / 19 |
| Serves | 4 throughout |
| Pages | 217 |

Metric quantities first, US cups and ounces alongside.

## The two outputs

**The book.** Every recipe is a spread. The left page is what you need — title, a twenty-minute
time dial, the full ingredient list, the one piece of technique that makes it work, the notes,
the nutrition strip and the washing-up line. The right page is how you cook it: the numbered
steps, each with a pictogram matched to what the step actually asks you to do, and the toddler
note at the foot.

**The site.** The same recipe files, generated as plain HTML. Filter by section, method, time
or vegetarian; search by dish, cuisine or ingredient; tick ingredients off as you shop and
strike out steps as you cook. Dark mode follows the system. No build step, no external
requests, no tracking — the fonts are embedded in the stylesheet, so you can drop `site/`
on any static host and it works.

## Sides are paired to mains

`book/pairings.py` maps every lunch and dinner to three of the 15 sides. The book prints them
at the foot of each recipe's page; the site renders them as cards, and each side lists the
mains that call for it. Edit that one file and both outputs follow.

## Cooking for a toddler

Every recipe carries a `## For the toddler` section: when to lift a small portion out of the
same pan, what to hold back from it, and how to cut it. The general rules behind those notes
— salt, heat, honey before one year, shapes that catch, textures that work — live in
`book/toddler_data.py` and are printed as a page of their own in the book and at
`site/toddlers.html`.

`verify.py` enforces the section on every recipe and fails the build if a recipe containing
honey does not mention it in its toddler note (27 of the 100 do). The notes are about
cooking rather than nutrition or medicine; the guidance page says so and points readers at
their own health service.

## Layout

```
recipes/     100 markdown recipe cards, numbered 01-100 — the source of truth
images/      optional photographs; empty by default
book/        the typesetter and the site generator
  parse.py       markdown -> structured recipe data
  build.py       recipe data -> a self-contained cookbook.html
  render.py      html -> PDF via headless Chromium, with a vertical-justification pass
  site.py        recipe data -> a static website in site/
  style.css      the print stylesheet
  web/           the website's stylesheet and script
  pantry_data.py the pantry checklist, the kit and the ten rules, shared by both outputs
  toddler_data.py the general toddler guidance, shared by both outputs
  pairings.py    which side goes with which main
  icons.py       method icons, the time dial, the page-anatomy diagram
  verify.py      structural checks across all 100 recipe files
  audit.py       content checks: conversions, unused ingredients, doneness, repetition
  art/           72 food icons, 20 action pictograms, colours, composition
dist/        the built PDF
site/        the built website
build/       intermediate HTML (gitignored)
```

## Building

```bash
npm install     # fonts (Fraunces + Inter, embedded in both outputs)
make verify     # structure: template, macro arithmetic, the twenty-minute limit
make audit      # content: unit conversions, unused ingredients, doneness cues, repeated prose
make book       # markdown -> HTML -> PDF
make site       # markdown -> static website
make            # all of it
```

`verify.py` checks that every recipe has the right shape. `audit.py` goes after the things
that are actually wrong in cookbooks: metric-to-imperial conversions that have drifted,
ingredients listed but never used in the method, steps calling for something the list does not
have, meat cooked without a doneness cue, portions outside a sensible range for their section,
and sentences copy-pasted between recipes. Both must come back clean.

Requires Python 3 with `playwright` and a Chromium build available to it.

Edit anything in `recipes/` and rerun `make` — the contents pages, both cuisine indexes, the
page numbers, the cover statistics, the website filters and the vegetarian counts all
regenerate from the recipe files themselves.

## How a recipe file is structured

Every file follows the same template and `verify.py` enforces it: a heading with number and
title, a meta line (cuisine, method, total time, serves, and `**Vegetarian**` where it applies),
a one-line hook, *Why it works*, *Ingredients*, *Method*, *Chef's notes* (swap / make it faster /
on the side / leftovers), *For the toddler*, a nutrition table, and a *Washing up* line.
`verify.py` also checks the macro arithmetic, that no recipe exceeds twenty minutes, and that no
two share a title.

## The typesetting

Each recipe occupies exactly two A4 pages, and recipes vary a lot in length. Before printing,
`render.py` runs a vertical-justification pass in the browser: for each page it binary-searches
a single parameter that expands or tightens a set of levers — leading between steps and
ingredients, panel padding, and on the densest pages the body size itself — until the content
sits a consistent 4.5 mm above the footer block. Long ingredient lists switch to a two-column
panel automatically. Every one of the 217 pages fits, and none is conspicuously empty.

## Photographs

There are none, by design — the illustrations were removed because they were not earning
their place. The slots remain: drop `NN-hero.jpg` or `NN-step-K.jpg` into `images/` and the
build picks them up. See [images/README.md](images/README.md).

---

## Lunch & Dinner

| # | Recipe | Cuisine | Method | Time | kcal | Page |
|---|---|---|---|---|---|---|
| 01 | [Harissa Chickpea & Cauliflower Crunch](recipes/01-harissa-chickpea-cauliflower-crunch.md) 🌱 | Tunisian / North African | Air Fryer | 19 min | 710 | 14 |
| 02 | [Miso-Glazed Salmon with Charred Tenderstem](recipes/02-miso-glazed-salmon-charred-tenderstem.md) | Japanese | Air Fryer | 18 min | 680 | 16 |
| 03 | [Peri-Peri Chicken Thighs with Blistered Peppers](recipes/03-peri-peri-chicken-blistered-peppers.md) | Portuguese-Mozambican | Air Fryer | 20 min | 660 | 18 |
| 04 | [Tandoori Paneer Tikka Skewers](recipes/04-tandoori-paneer-tikka-skewers.md) 🌱 | Indian | Air Fryer | 19 min | 745 | 20 |
| 05 | [Gochujang Tofu with Smashed Sesame Cucumber](recipes/05-gochujang-tofu-smashed-cucumber.md) 🌱 | Korean | Air Fryer | 19 min | 640 | 22 |
| 06 | [Za'atar Chicken with Lemon Courgette](recipes/06-zaatar-chicken-lemon-courgette.md) | Levantine | Air Fryer | 19 min | 700 | 24 |
| 07 | [Chilli-Lime Prawns with Avocado & Coriander](recipes/07-chilli-lime-prawns-avocado.md) | Mexican | Air Fryer | 14 min | 665 | 26 |
| 08 | [Sicilian Sea Bass with Fennel, Olive & Orange](recipes/08-sicilian-sea-bass-fennel-orange.md) | Italian (Sicilian) | Air Fryer | 18 min | 610 | 28 |
| 09 | [Jerk Chicken with Charred Pineapple](recipes/09-jerk-chicken-charred-pineapple.md) | Jamaican | Air Fryer | 20 min | 760 | 30 |
| 10 | [Shawarma-Spiced Turkey with Sumac Onions](recipes/10-shawarma-turkey-sumac-onions.md) | Middle Eastern | Air Fryer | 17 min | 670 | 32 |
| 11 | [Berbere Chicken & Sweet Potato Bowl](recipes/11-berbere-chicken-sweet-potato.md) | Ethiopian | Air Fryer | 20 min | 690 | 34 |
| 12 | [Cajun Blackened Cod with Charred Corn Salsa](recipes/12-cajun-blackened-cod-corn-salsa.md) | American (Louisiana) | Air Fryer | 18 min | 695 | 36 |
| 13 | [Furikake Salmon Rice Bowl](recipes/13-furikake-salmon-rice-bowl.md) | Hawaiian-Japanese | Air Fryer | 18 min | 745 | 38 |
| 14 | [Chermoula Prawns with Courgette Ribbons](recipes/14-chermoula-prawns-courgette-ribbons.md) | Moroccan | Air Fryer | 15 min | 670 | 40 |
| 15 | [Salt & Pepper Tofu with Pak Choi](recipes/15-salt-pepper-tofu-pak-choi.md) 🌱 | Chinese (Cantonese) | Air Fryer | 19 min | 680 | 42 |
| 16 | [Pad Krapow — Thai Basil Chicken](recipes/16-pad-krapow-thai-basil-chicken.md) | Thai | One Pan | 18 min | 665 | 44 |
| 17 | [Quick Thai Green Curry Prawns](recipes/17-thai-green-curry-prawns.md) | Thai | One Pan | 18 min | 660 | 46 |
| 18 | [Ginger-Garlic Prawn & Broccoli Stir-Fry](recipes/18-ginger-garlic-prawn-broccoli-stirfry.md) | Chinese | Wok | 15 min | 660 | 48 |
| 19 | [Sichuan Cumin Beef with Peppers](recipes/19-sichuan-cumin-beef-peppers.md) | Chinese (Sichuan) | Wok | 16 min | 670 | 50 |
| 20 | [Korean Bulgogi Beef Bowl](recipes/20-korean-bulgogi-beef-bowl.md) | Korean | One Pan | 19 min | 685 | 52 |
| 21 | [Vietnamese Lemongrass Chicken Bowl](recipes/21-vietnamese-lemongrass-chicken-bowl.md) | Vietnamese | One Pan | 18 min | 740 | 54 |
| 22 | [Shogayaki — Japanese Ginger Pork with Cabbage](recipes/22-shogayaki-ginger-pork-cabbage.md) | Japanese | One Pan | 18 min | 645 | 56 |
| 23 | [Kerala Coconut Prawn Fry](recipes/23-kerala-coconut-prawn-fry.md) | Indian (South) | One Pan | 18 min | 640 | 58 |
| 24 | [Egg & Spinach Bhurji](recipes/24-egg-spinach-bhurji.md) 🌱 | Indian | One Pan | 15 min | 610 | 60 |
| 25 | [Fifteen-Minute Chana Masala](recipes/25-fifteen-minute-chana-masala.md) 🌱 | Indian | One Pan | 15 min | 680 | 62 |
| 26 | [Turkish Menemen](recipes/26-turkish-menemen.md) 🌱 | Turkish | One Pan | 16 min | 710 | 64 |
| 27 | [Green Shakshuka](recipes/27-green-shakshuka.md) 🌱 | Israeli / Levantine | One Pan | 17 min | 750 | 66 |
| 28 | [Greek Lemon Chicken & Orzo](recipes/28-greek-lemon-chicken-orzo.md) | Greek | One Pan | 20 min | 745 | 68 |
| 29 | [Prawn Saganaki with Feta](recipes/29-prawn-saganaki-feta.md) | Greek | One Pan | 20 min | 750 | 70 |
| 30 | [Broccoli Aglio e Olio with Anchovy](recipes/30-broccoli-aglio-e-olio-anchovy.md) | Italian | One Pan | 20 min | 750 | 72 |
| 31 | [Tuscan White Bean, Kale & Lemon Skillet](recipes/31-tuscan-white-bean-kale-skillet.md) | Italian (Tuscan) | One Pan | 18 min | 725 | 74 |
| 32 | [Tuna Puttanesca Beans](recipes/32-tuna-puttanesca-beans.md) | Italian | One Pan | 18 min | 770 | 76 |
| 33 | [Gambas al Ajillo with Chickpeas](recipes/33-gambas-al-ajillo-chickpeas.md) | Spanish | One Pan | 18 min | 755 | 78 |
| 34 | [Smoky Paprika Chicken with Piquillo Peppers](recipes/34-smoky-paprika-chicken-piquillo.md) | Spanish | One Pan | 20 min | 710 | 80 |
| 35 | [Chipotle Chicken, Black Bean & Charred Corn Skillet](recipes/35-chipotle-chicken-black-bean-corn.md) | Mexican | One Pan | 20 min | 750 | 82 |
| 36 | [Lomo Saltado](recipes/36-lomo-saltado.md) | Peruvian | Wok | 19 min | 760 | 84 |
| 37 | [Moqueca Express — Brazilian Coconut Fish Stew](recipes/37-moqueca-express-brazilian-fish.md) | Brazilian | One Pan | 20 min | 745 | 86 |
| 38 | [Filipino Adobo Flash Chicken](recipes/38-filipino-adobo-flash-chicken.md) | Filipino | One Pan | 20 min | 650 | 88 |
| 39 | [Nasi Goreng Cauliflower Rice with Fried Egg](recipes/39-nasi-goreng-cauliflower-rice.md) | Indonesian | Wok | 18 min | 640 | 90 |
| 40 | [Sambal Green Beans with Egg](recipes/40-sambal-green-beans-egg.md) | Malaysian | Wok | 17 min | 750 | 92 |
| 41 | [Burmese Golden Turmeric Chicken](recipes/41-burmese-golden-turmeric-chicken.md) | Burmese | One Pan | 19 min | 725 | 94 |
| 42 | [Gomen Be Siga — Ethiopian Collards with Beef](recipes/42-ethiopian-gomen-be-siga.md) | Ethiopian | One Pan | 20 min | 640 | 96 |
| 43 | [Ras el Hanout Turkey with Herbs & Almonds](recipes/43-ras-el-hanout-turkey-almonds.md) | Moroccan | One Pan | 18 min | 760 | 98 |
| 44 | [West African Peanut Stew Express](recipes/44-west-african-peanut-stew.md) | Ghanaian / Senegalese | One Pan | 20 min | 755 | 100 |
| 45 | [Georgian Walnut-Garlic Chicken with Green Beans](recipes/45-georgian-walnut-garlic-chicken.md) | Georgian | One Pan | 20 min | 645 | 102 |
| 46 | [Deconstructed Vietnamese Summer Roll Bowl](recipes/46-vietnamese-summer-roll-bowl.md) | Vietnamese | No Cook | 18 min | 690 | 104 |
| 47 | [Chicken Fattoush with Crisped Chickpeas](recipes/47-chicken-fattoush-crisped-chickpeas.md) | Lebanese | Air Fryer | 20 min | 700 | 106 |
| 48 | [Salmon Poke Bowl](recipes/48-salmon-poke-bowl.md) | Hawaiian-Japanese | No Cook | 16 min | 730 | 108 |
| 49 | [Prawn Ceviche Tostada Salad](recipes/49-prawn-ceviche-tostada-salad.md) | Peruvian-Mexican | No Cook | 17 min | 690 | 110 |
| 50 | [Turkish Çoban Salad with Tuna & Sumac](recipes/50-turkish-coban-salad-tuna-sumac.md) | Turkish | No Cook | 14 min | 705 | 112 |

## On the Side

| # | Recipe | Cuisine | Method | Time | kcal | Page |
|---|---|---|---|---|---|---|
| 86 | [Charred Lemon Broccoli with Almonds](recipes/86-charred-lemon-broccoli-almonds.md) 🌱 | Italian | Air Fryer | 10 min | 175 | 115 |
| 87 | [Smashed Cucumber with Garlic & Sesame](recipes/87-smashed-cucumber-garlic-sesame.md) 🌱 | Chinese | No Cook | 8 min | 95 | 117 |
| 88 | [Harissa Carrots with Yoghurt](recipes/88-harissa-carrots-yoghurt.md) 🌱 | Tunisian | Air Fryer | 14 min | 140 | 119 |
| 89 | [Garlicky Greens with Chilli & Lemon](recipes/89-garlicky-greens-chilli-lemon.md) 🌱 | Greek | One Pan | 8 min | 150 | 121 |
| 90 | [Shirazi Salad](recipes/90-shirazi-salad.md) 🌱 | Iranian | No Cook | 8 min | 120 | 123 |
| 91 | [Coconut Sambol](recipes/91-coconut-sambol.md) 🌱 | Sri Lankan | No Cook | 8 min | 150 | 125 |
| 92 | [Crispy Rosemary Potatoes](recipes/92-crispy-rosemary-potatoes.md) 🌱 | British | Air Fryer | 18 min | 230 | 127 |
| 93 | [Sigeumchi Namul — Sesame Spinach](recipes/93-sigeumchi-namul-sesame-spinach.md) 🌱 | Korean | One Pan | 8 min | 95 | 129 |
| 94 | [Tomato, Red Onion & Sumac Salad](recipes/94-tomato-red-onion-sumac-salad.md) 🌱 | Turkish | No Cook | 6 min | 105 | 131 |
| 95 | [Quick Pickled Red Onions](recipes/95-quick-pickled-red-onions.md) 🌱 | Mexican | No Cook | 8 min | 90 | 133 |
| 96 | [Buttered Cabbage with Caraway](recipes/96-buttered-cabbage-caraway.md) 🌱 | Polish | One Pan | 10 min | 125 | 135 |
| 97 | [Sesame Green Beans with Ginger](recipes/97-sesame-green-beans-ginger.md) 🌱 | Japanese | One Pan | 8 min | 110 | 137 |
| 98 | [Cucumber, Mint & Yoghurt Raita](recipes/98-cucumber-mint-raita.md) 🌱 | Indian | No Cook | 6 min | 75 | 139 |
| 99 | [Blistered Padrón Peppers](recipes/99-blistered-padron-peppers.md) 🌱 | Spanish | Air Fryer | 8 min | 70 | 141 |
| 100 | [Charred Broccolini with Miso Butter](recipes/100-charred-broccolini-miso-butter.md) 🌱 | Japanese | Air Fryer | 12 min | 160 | 143 |

## Breakfast

| # | Recipe | Cuisine | Method | Time | kcal | Page |
|---|---|---|---|---|---|---|
| 51 | [Sweet Potato, Egg & Chilli Hash](recipes/51-sweet-potato-egg-chilli-hash.md) 🌱 | American | Air Fryer | 18 min | 420 | 146 |
| 52 | [Halloumi, Tomato & Za'atar Plate](recipes/52-halloumi-tomato-zaatar-plate.md) 🌱 | Cypriot | Air Fryer | 12 min | 445 | 148 |
| 53 | [Masala Omelette Muffins](recipes/53-masala-omelette-muffins.md) 🌱 | Indian | Air Fryer | 15 min | 200 | 150 |
| 54 | [Banana, Oat & Almond Butter Bake](recipes/54-banana-oat-almond-butter-bake.md) 🌱 | British | Air Fryer | 18 min | 430 | 152 |
| 55 | [Crispy Chickpea, Avocado & Lemon Toast](recipes/55-crispy-chickpea-avocado-lemon-toast.md) 🌱 | Modern Levantine | Air Fryer | 12 min | 500 | 154 |
| 56 | [Tamagoyaki with Grilled Salmon & Rice](recipes/56-tamagoyaki-grilled-salmon-rice.md) | Japanese | One Pan | 18 min | 540 | 156 |
| 57 | [Gyeran Bap — Korean Egg Rice](recipes/57-gyeran-bap-korean-egg-rice.md) 🌱 | Korean | One Pan | 10 min | 455 | 158 |
| 58 | [Ten-Minute Chicken & Ginger Congee](recipes/58-chicken-ginger-congee.md) | Chinese | One Pan | 18 min | 510 | 160 |
| 59 | [Rava Uttapam with Coconut Chutney](recipes/59-rava-uttapam-coconut-chutney.md) 🌱 | Indian (South) | One Pan | 18 min | 455 | 162 |
| 60 | [Persian Herb & Feta Omelette](recipes/60-persian-herb-feta-omelette.md) 🌱 | Iranian | One Pan | 15 min | 400 | 164 |
| 61 | [Huevos Rancheros Rápidos](recipes/61-huevos-rancheros-rapidos.md) 🌱 | Mexican | One Pan | 15 min | 495 | 166 |
| 62 | [Pan con Tomate with Soft Eggs](recipes/62-pan-con-tomate-soft-eggs.md) 🌱 | Spanish | One Pan | 10 min | 425 | 168 |
| 63 | [Ful Medames](recipes/63-ful-medames.md) 🌱 | Egyptian | One Pan | 12 min | 370 | 170 |
| 64 | [Buckwheat Galette with Egg & Greens](recipes/64-buckwheat-galette-egg-greens.md) 🌱 | French (Breton) | One Pan | 18 min | 360 | 172 |
| 65 | [Khao Tom — Thai Rice Soup with Prawns](recipes/65-khao-tom-thai-rice-soup-prawns.md) | Thai | One Pan | 15 min | 310 | 174 |
| 66 | [Egg & Tomato Stir-Fry](recipes/66-egg-tomato-stir-fry.md) 🌱 | Chinese | Wok | 10 min | 430 | 176 |
| 67 | [Sinangag — Filipino Garlic Rice & Egg](recipes/67-sinangag-filipino-garlic-rice-egg.md) 🌱 | Filipino | Wok | 12 min | 430 | 178 |
| 68 | [Ten-Minute Bircher Muesli](recipes/68-ten-minute-bircher-muesli.md) 🌱 | Swiss | No Cook | 10 min | 430 | 180 |
| 69 | [Danish Rye with Smoked Mackerel & Cucumber](recipes/69-danish-rye-smoked-mackerel.md) | Danish | No Cook | 10 min | 560 | 182 |
| 70 | [Orange, Date & Almond Yoghurt Bowl](recipes/70-orange-date-almond-yoghurt-bowl.md) 🌱 | Moroccan | No Cook | 8 min | 465 | 184 |

## Something Afterwards

| # | Recipe | Cuisine | Method | Time | kcal | Page |
|---|---|---|---|---|---|---|
| 71 | [Cinnamon Peaches with Yoghurt & Pistachio](recipes/71-cinnamon-peaches-yoghurt-pistachio.md) 🌱 | Turkish | Air Fryer | 12 min | 285 | 187 |
| 72 | [Bananas with Dark Chocolate & Tahini](recipes/72-banana-dark-chocolate-tahini.md) 🌱 | Modern Levantine | Air Fryer | 10 min | 255 | 189 |
| 73 | [Spiced Apple & Oat Crumble Cups](recipes/73-spiced-apple-oat-crumble-cups.md) 🌱 | British | Air Fryer | 18 min | 310 | 191 |
| 74 | [Charred Pineapple with Chilli, Lime & Coconut](recipes/74-charred-pineapple-chilli-lime-coconut.md) 🌱 | Mexican | Air Fryer | 12 min | 225 | 193 |
| 75 | [Pan-Roasted Figs with Honey & Walnuts](recipes/75-pan-roasted-figs-honey-walnuts.md) 🌱 | Greek | One Pan | 10 min | 305 | 195 |
| 76 | [Mango & Coconut Sticky Oats](recipes/76-mango-coconut-sticky-oats.md) 🌱 | Thai | One Pan | 15 min | 310 | 197 |
| 77 | [Fifteen-Minute Cardamom Kheer](recipes/77-cardamom-kheer.md) 🌱 | Indian | One Pan | 18 min | 305 | 199 |
| 78 | [Apricots Poached in Cinnamon & Orange](recipes/78-apricots-poached-cinnamon-orange.md) 🌱 | Turkish | One Pan | 15 min | 265 | 201 |
| 79 | [Ginger Milk Curd](recipes/79-ginger-milk-curd.md) 🌱 | Chinese (Cantonese) | One Pan | 10 min | 224 | 203 |
| 80 | [Rosewater, Pistachio & Pomegranate Yoghurt](recipes/80-rosewater-pistachio-pomegranate-yoghurt.md) 🌱 | Iranian | No Cook | 10 min | 255 | 205 |
| 81 | [Chocolate Avocado Mousse](recipes/81-chocolate-avocado-mousse.md) 🌱 | Mexican | No Cook | 10 min | 280 | 207 |
| 82 | [Espresso & Ricotta Cream with Cocoa](recipes/82-espresso-ricotta-cream-cocoa.md) 🌱 | Italian | No Cook | 8 min | 260 | 209 |
| 83 | [Date, Almond & Cacao Truffles](recipes/83-date-almond-cacao-truffles.md) 🌱 | Levantine | No Cook | 15 min | 276 | 211 |
| 84 | [Mango & Coconut Cream Bowl](recipes/84-mango-coconut-cream-bowl.md) 🌱 | Filipino | No Cook | 10 min | 275 | 213 |
| 85 | [Berry & Skyr Whip with Walnut Rubble](recipes/85-berry-skyr-whip-walnut-rubble.md) 🌱 | Icelandic | No Cook | 10 min | 270 | 215 |

## By cuisine

- **American** — 51
- **American (Louisiana)** — 12
- **Brazilian** — 37
- **British** — 54, 73, 92
- **Burmese** — 41
- **Chinese** — 18, 58, 66, 87
- **Chinese (Cantonese)** — 15, 79
- **Chinese (Sichuan)** — 19
- **Cypriot** — 52
- **Danish** — 69
- **Egyptian** — 63
- **Ethiopian** — 11, 42
- **Filipino** — 38, 67, 84
- **French (Breton)** — 64
- **Georgian** — 45
- **Ghanaian / Senegalese** — 44
- **Greek** — 28, 29, 75, 89
- **Hawaiian-Japanese** — 13, 48
- **Icelandic** — 85
- **Indian** — 04, 24, 25, 53, 77, 98
- **Indian (South)** — 23, 59
- **Indonesian** — 39
- **Iranian** — 60, 80, 90
- **Israeli / Levantine** — 27
- **Italian** — 30, 32, 82, 86
- **Italian (Sicilian)** — 08
- **Italian (Tuscan)** — 31
- **Jamaican** — 09
- **Japanese** — 02, 22, 56, 97, 100
- **Korean** — 05, 20, 57, 93
- **Lebanese** — 47
- **Levantine** — 06, 83
- **Malaysian** — 40
- **Mexican** — 07, 35, 61, 74, 81, 95
- **Middle Eastern** — 10
- **Modern Levantine** — 55, 72
- **Moroccan** — 14, 43, 70
- **Peruvian** — 36
- **Peruvian-Mexican** — 49
- **Polish** — 96
- **Portuguese-Mozambican** — 03
- **Spanish** — 33, 34, 62, 99
- **Sri Lankan** — 91
- **Swiss** — 68
- **Thai** — 16, 17, 65, 76
- **Tunisian** — 88
- **Tunisian / North African** — 01
- **Turkish** — 26, 50, 71, 78, 94
- **Vietnamese** — 21, 46
