"""Publication details for the printed editions, and the economics of selling them.

The copyright page omits any field left empty rather than printing a placeholder,
so the book is always correct to print even while something here is unset.

The pricing figures at the bottom are the ones to be sceptical of: they decide
whether the book is worth selling, and none of them is confirmed against a primary
source. `make pricing` reports what they imply. Check them in KDP's own
printing-cost calculator before setting a price.
"""

TITLE = 'The 20-Minute Table'
SUBTITLE = 'A hundred fast, whole-food recipes for the years when dinner has to happen anyway'
AUTHOR = 'Nawaz Dhandala'
PUBLISHER = 'HackerBay'
PUBLISHER_SITE = 'HackerBay.io'
YEAR = 2026
EDITION = 'First edition'
SITE = 'twentyminutetable.hackerbay.io'
REPO = 'github.com/hackerbay/twenty-minute-table'

# One ISBN per printed format. The Kindle edition uses an Amazon ASIN and needs none.
#
# Allocated from HackerBay, Inc.'s own Bowker block (prefix 978-1-950600), so the
# publisher of record is yours rather than Amazon's, and the book could be printed
# somewhere else later without new numbers.
#
# These are reserved here but NOT yet registered against the title at Bowker.
# Assigning them there means filling in real publication metadata — format, date,
# contributors, price — so it is left as a deliberate step before publishing.
ISBN = {
    'paperback': '978-1-950600-01-4',
    'hardback': '978-1-950600-02-1',
}

# --- Kindle economics ------------------------------------------------------
# KDP charges a delivery fee per megabyte against the 70% royalty option, so the
# weight of the illustrations comes straight off the margin. epub.py fails the
# build if the edition cannot clear MIN_MARGIN at this price, because the fix is
# a lighter file, and that has to happen before publication, not after.
KINDLE_LIST_USD = 9.99          # must sit inside the 70% band to earn that rate
KINDLE_ROYALTY_RATE = 0.70
KDP_70_BAND = (2.99, 12.99)     # US; the upper bound rose from 9.99 in July 2026
KDP_DELIVERY_PER_MB = 0.15      # USD, charged on the CONVERTED file size, which is
                                # NOT the EPUB size: KDP measured 4.56 MB against our
                                # 4.23 MB EPUB, so estimates from the EPUB run light.
MIN_KINDLE_MARGIN = 0.25        # royalty after delivery, as a share of list price

# --- print economics -------------------------------------------------------
# KDP pays 60% of list minus the printing cost, so on a colour book the page
# count sets the floor under the price.
#
# Every figure below was read from KDP's own Printing Cost & Royalty Calculator
# on 2026-08-31, for 8.25x11 at 224 pages on Amazon.com, and cross-checked
# against the published rate tables. 8.25x11 is a LARGE trim (over 6.12in wide
# or over 9in tall), which is the more expensive per-page band.
#
# Ink and paper are locked permanently once a title is published — a book cannot
# be moved between premium colour, standard colour and black-and-white later.
PRINT_ROYALTY_RATE = 0.60       # verified: the calculator returns 60% at these prices
MIN_PRINT_MARGIN = 0.25         # royalty after printing, as a share of list price

# fixed cost, per-page cost — USD, Amazon.com, large trim
INK = {
    'premium colour':  (1.00, 0.0800),   # verified — paperback, 42-828 pages
    'standard colour': (1.00, 0.0402),   # verified — paperback, 72-600 pages
}
# The interior is entirely vector art and flat colour, with no photographs, so
# premium colour buys nothing this book can use.
INK_CHOICE = 'standard colour'

# Hardcover is PREMIUM COLOUR ONLY — the calculator rejects standard colour with
# "Standard color is currently not available for hardcover books", so a hardback
# cannot be made cheaper the way the paperback can.
HARDBACK_INK = 'premium colour'

# List prices. Set these from KDP's calculator once the real print cost is known;
# pricing.py will tell you the minimum each edition needs to clear MIN_PRINT_MARGIN.
LIST_USD = {
    'paperback': 28.99,
    'hardback': 69.99,
}

# Verified in the calculator: hardcover, 8.25x11, 224 pages, premium colour,
# Amazon.com. $5.65 fixed + 224 * $0.08 = $23.57. Minimum list price $39.28.
HARDBACK_PRINT_COST_USD = 23.57

# The content is CC BY 4.0, so the copyright page says that rather than the
# "all rights reserved" boilerplate, which would contradict the LICENSE files.
LICENCE = (
    'The recipes and the text of this book are licensed under the Creative Commons '
    'Attribution 4.0 International licence. You may share and adapt them, including '
    'commercially, provided you give credit. The software that typesets this book is '
    'licensed separately under the MIT licence. Both are at ' + REPO + '.'
)

MORAL_RIGHTS = (
    'The right of ' + AUTHOR + ' to be identified as the author of this work has been '
    'asserted in accordance with the Copyright, Designs and Patents Act 1988.'
)

DISCLAIMER = (
    'Cooking times and quantities assume a domestic kitchen and a cold start; ovens, '
    'pans and air fryers vary, so use the doneness cues rather than the clock. Nutrition '
    'figures are estimates for a quarter of the finished dish and are not dietary advice. '
    'Check every recipe against your own household’s allergies and dietary needs — '
    'the ingredient lists name common allergens but cannot anticipate yours. The notes on '
    'feeding a toddler are about cooking, not medicine; for anything concerning a child’s '
    'health, diet or development, ask your own health service.'
)

TYPE_NOTE = (
    'Set in Fraunces, drawn by Phaedra Charles and Flavia Zimbardi, and Inter, drawn by '
    'Rasmus Andersson. Both are licensed under the SIL Open Font License.'
)
