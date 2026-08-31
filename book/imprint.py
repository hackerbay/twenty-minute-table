"""Publication details for the printed editions.

The ISBNs are blank until KDP assigns them (or you buy your own). The copyright
page omits any line that is empty rather than printing a placeholder, so the book
is always correct to print — but `make verify` warns while they are unset,
because a paperback cannot be submitted without one.
"""

TITLE = 'The 20-Minute Table'
SUBTITLE = 'A hundred fast, whole-food recipes for the years when dinner has to happen anyway'
AUTHOR = 'Nawaz Dhandala'
PUBLISHER = ''          # your imprint name, if you use your own ISBN
YEAR = 2026
EDITION = 'First edition'
SITE = 'twentyminutetable.hackerbay.io'
REPO = 'github.com/hackerbay/twenty-minute-table'

# One ISBN per printed format. The Kindle edition uses an Amazon ASIN and needs none.
ISBN = {
    'paperback': '',
    'hardback': '',
}

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
    'Check every recipe against your own household&rsquo;s allergies and dietary needs — '
    'the ingredient lists name common allergens but cannot anticipate yours. The notes on '
    'feeding a toddler are about cooking, not medicine; for anything concerning a child&rsquo;s '
    'health, diet or development, ask your own health service.'
)

TYPE_NOTE = (
    'Set in Fraunces, drawn by Phaedra Charles and Flavia Zimbardi, and Inter, drawn by '
    'Rasmus Andersson. Both are licensed under the SIL Open Font License.'
)
