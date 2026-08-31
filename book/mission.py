"""Why the book exists.

Shared by the book's front matter and the website's about page, in the same way
pantry_data and toddler_data are shared, so the two cannot drift apart. Edit it
here and both outputs follow.

Paragraphs carry `<b>` for emphasis and a `{repo}` slot each output fills for
itself: the printed book has nowhere to put a link, so it prints the address;
the website makes it clickable.
"""

KICKER = 'Why this book exists'

# Two lines, so print can break the heading where it wants and the web can let
# it wrap on its own.
HEADING_LINES = ['Eating well should not', 'depend on having time']

PARAS = [
    'Most of the reasons a household stops cooking are practical rather than culinary: '
    'the deciding, the shopping, the hunting for a jar of something at the back of a '
    'cupboard, and the twenty minutes of washing up after a meal that took thirty to '
    'make. Those are the parts this book removes, and it removes them on purpose '
    '&mdash; because once they are gone, cooking from whole ingredients stops being an '
    'aspiration and becomes the easier option.',

    'Every constraint here exists to make that true rather than merely say it. Twenty '
    'minutes from a cold start. One pan or one basket. Four servings. A toddler&rsquo;s '
    'portion out of the same pan, before the salt and before the chilli. None of it '
    'assumes more time, more money or more equipment than you have.',

    'Which is why the whole thing is <b>open source</b>. Every recipe, the typesetter '
    'that turns them into this book, and the website that publishes them are yours: the '
    'recipes under Creative Commons, the software under the MIT licence, all of it at '
    '{repo}. Take them, change them, translate them, print them for the inside of a '
    'cupboard door. Add the dinners your own family actually eats. Nobody needs '
    'permission, and that is the point &mdash; food this plain should not belong to '
    'anyone.',
]


def paras(repo):
    """The paragraphs with the repository address filled in."""
    return [p.replace('{repo}', repo) for p in PARAS]
