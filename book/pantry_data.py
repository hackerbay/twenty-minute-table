"""The pantry checklist, the kit and the ten rules.

Shared by the book (build.py) and the website (site.py) so the two can never
drift apart. Edit here and both pick it up.
"""

SHELVES = [
  ("Oils &amp; acids", ["Extra virgin olive oil", "Neutral high-smoke oil (groundnut or rapeseed)",
    "Toasted sesame oil", "Red wine vinegar", "Rice vinegar", "Lemons", "Limes"]),
  ("The spice tin", ["Cumin, ground", "Cumin seed", "Smoked paprika", "Ground coriander", "Turmeric",
    "Chilli flakes", "Cinnamon", "Dried oregano", "Za&rsquo;atar", "Sumac", "Ras el hanout",
    "Garam masala", "Berbere", "Chinese five-spice", "Cajun blend", "Cardamom pods"]),
  ("Pastes &amp; bottles", ["Rose harissa", "Gochujang", "White miso", "Thai green curry paste",
    "Sambal oelek", "Chipotle in adobo", "Tahini", "Fish sauce", "Light soy", "Dark soy",
    "Mirin", "Runny honey", "Maple syrup"]),
  ("Tins &amp; jars", ["Chickpeas &times; 3", "Black beans", "Cannellini beans", "Brown lentils",
    "Dried split fava beans", "Chopped tomatoes", "Full-fat coconut milk", "Tuna in olive oil",
    "Anchovies", "Olives", "Capers", "Piquillo peppers"]),
  ("The fridge", ["Eggs, by the dozen", "Thick Greek yoghurt", "Skyr", "Feta", "Halloumi",
    "Ricotta", "Cottage cheese", "Ginger", "Garlic", "Spring onions", "Fresh chillies",
    "Spinach", "Coriander", "Flat-leaf parsley"]),
  ("The freezer", ["Raw king prawns", "Salmon fillets", "White fish fillets", "Peas", "Edamame",
    "Ginger-garlic paste, in cubes", "Flatbreads", "Sliced sourdough"]),
  ("Fast carbohydrate", ["Basmati or jasmine rice", "A cooked batch of rice", "Orzo", "Rice noodles",
    "Couscous", "Rolled oats", "Rye bread", "Buckwheat flour"]),
  ("Finishers", ["Toasted almonds", "Walnuts", "Pistachios", "Sesame seeds", "Pumpkin seeds",
    "Nori", "Medjool dates", "Dark chocolate, 70% or above"]),
]



KIT = ["An air fryer, or a hot oven and a shallow tray", "One wide, heavy frying pan", "A wok, or a second frying pan",
"One sharp knife", "One large chopping board", "A microplane", "Tongs", "A box grater",
"Four bowls you are happy to eat from"]

RULES = [
  ("Preheat before you chop.", "The air fryer or the pan should be properly hot by the time the board is clear. This alone takes three or four minutes off almost every recipe here, and it is the difference between food that browns and food that steams."),
  ("Cut for the clock.", "Nothing cooking in under fifteen minutes should be thicker than your thumb. Small and even beats big and hopeful, and it is why the meat in this book is nearly always sliced or cut into strips rather than left whole."),
  ("Season twice.", "Once in the pan, once at the table. The second pass is nearly always acid &mdash; a squeeze of lemon, a splash of vinegar &mdash; and it is what makes fast food taste finished rather than merely cooked."),
  ("Always add something raw.", "Herbs, sliced chilli, spring onion, a spoonful of yoghurt. Fifteen seconds of work, and it is the difference between a meal and a plate of cooked ingredients."),
  ("Wash up while it rests.", "Two minutes with the pan still warm, instead of ten with it cold. Every recipe here is built around one pan or one basket for exactly this reason, and the line at the foot of each page tells you what you are committing to."),
  ("Read it through once first.", "Thirty seconds now saves three minutes of standing over a hot pan working out what comes next. Every recipe in this book is short enough to hold in your head, which is deliberate."),
  ("Salt the water, not just the food.", "Pasta, couscous, rice and greens season from the inside if the water they meet is salty. Nothing you add afterwards ever reaches the middle."),
  ("Buy the thigh, not the breast.", "It costs less, it cooks faster than you expect, and it forgives the minute you lose looking for the tongs. Fattier fish forgives in the same way that lean white fish does not."),
  ("One pan means one pan.", "If a recipe tempts you into a second, ask whether the thing you would cook in it could go in beside the first instead. It usually can, and the washing up halves."),
  ("Cook the same one twice in a fortnight.", "The second time takes two-thirds as long, because your hands already know it. That, rather than any shortcut, is where twenty minutes actually comes from."),
]
