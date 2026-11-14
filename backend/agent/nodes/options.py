"""Find which size / colour a customer means, tolerating spelling variants."""

import re

from rapidfuzz import fuzz


SIZE_ALIASES = {
    "s": ["s", "small"],
    "small": ["s", "small"],
    "m": ["m", "medium", "med"],
    "medium": ["m", "medium", "med"],
    "l": ["l", "large"],
    "large": ["l", "large"],
    "xl": ["xl", "xlarge", "x-large", "extra large"],
    "xlarge": ["xl", "xlarge", "x-large", "extra large"],
    "extralarge": ["xl", "xlarge", "x-large", "extra large"],
    "xxl": ["xxl", "2xl"],
    "2xl": ["xxl", "2xl"],
}

# Colours that people spell / say differently. Each set = the same colour.
# Add new names here; any member of a set matches any other member
# (customer writes "mahndi", shop has "Mehndi" -> match).
COLOR_GROUPS = [
    {"red", "lal", "laal", "lall", "laall", "lal rang", "crimson", "scarlet", "लाल"},
    {"maroon", "marun", "maron", "marune", "burgundy", "wine", "wine red", "मरून"},
    {"pink", "gulabi", "gulaabi", "gulabee", "gulaabee", "baby pink", "light pink",
     "hot pink", "rose pink", "rose", "गुलाबी"},
    {"rani", "rani pink", "rani color", "rani colour", "magenta", "fuchsia", "fuschia",
     "रानी"},
    {"onion pink", "onion", "pyaji", "pyazi"},
    {"peach", "peech", "aadu", "adu"},
    {"coral", "salmon"},
    {"orange", "narangi", "naarangi", "narangee", "नारंगी"},
    {"kesari", "kesariya", "saffron", "bhagwa", "केसरी"},
    {"yellow", "pila", "peela", "pela", "pilla", "peeli", "pili", "peli", "haldi",
     "haldi yellow", "lemon yellow", "lemon", "पीला", "पीली"},
    {"mustard", "mustard yellow", "sarson", "sarso"},
    {"green", "hara", "haara", "harra", "hari", "sabz", "dark green", "light green",
     "bottle green", "parrot green", "tota", "हरा", "हरी"},
    {"mehndi", "mehandi", "mahndi", "mahandi", "mehendi", "mahendi", "mehdi", "mendi",
     "mehndi green", "mehandi green", "henna", "मेहंदी", "मेहन्दी"},
    {"pista", "pista green", "pistachio", "pishta", "पिस्ता"},
    {"olive", "olive green", "army green", "military green"},
    {"mint", "mint green", "pudina", "sea green", "seagreen"},
    {"rama", "rama green", "ramagreen"},
    {"blue", "neela", "nila", "neeli", "nili", "royal blue", "नीला", "नीली"},
    {"sky blue", "skyblue", "asmani", "aasmani", "asmaani", "baby blue", "light blue",
     "आसमानी"},
    {"navy", "navy blue", "dark blue", "midnight blue", "nevy"},
    {"firozi", "ferozi", "feroza", "firoza", "turquoise", "teal", "फिरोजी"},
    {"morpankhi", "mor pankhi", "morpankh", "peacock", "peacock blue",
     "peacock green", "मोरपंखी"},
    {"purple", "jamuni", "jamni", "jamunee", "baingani", "baigani", "baigni",
     "bengani", "violet", "बैंगनी", "जामुनी"},
    {"lavender", "lilac", "lilak", "lavendar", "levender"},
    {"white", "safed", "safaid", "safeid", "सफेद", "सफ़ेद"},
    {"off white", "offwhite", "off-white", "ivory", "ivary"},
    {"cream", "creamy", "malai", "kareem"},
    {"beige", "biege", "skin", "skin color", "skin colour", "nude", "biscuit"},
    {"black", "kala", "kaala", "kali", "kaali", "blk", "काला", "काली"},
    {"grey", "gray", "gry", "slate", "charcoal", "ash", "grye", "ग्रे", "स्लेटी"},
    {"silver", "chandi", "silvar", "chaandi"},
    {"gold", "golden", "sona", "sunehri", "sunahri", "sunheri", "goldan", "सुनहरा"},
    {"brown", "bhura", "bhoora", "bhoori", "bhuri", "coffee", "chocolate", "choco",
     "भूरा"},
    {"khaki", "kaki", "khakhi"},
    {"rust", "rusty", "kattha", "brick", "brick red"},
    {"copper", "tamba", "taamba"},
    {"multi", "multicolor", "multicolour", "multi color", "multi colour", "rangeen",
     "rangin", "rang birangi"},
]


def _has_word(message: str, option: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(option.lower())}(?!\w)", message.lower()))


def find_size(message: str, sizes: list[str]) -> str | None:
    # Longest matching alias wins: "extra large" is XL, not L.
    best, best_len = None, 0
    for size in sizes:
        key = size.lower().replace(" ", "")
        aliases = SIZE_ALIASES.get(key, [size.lower()])
        for alias in aliases:
            if _has_word(message, alias) and len(alias) > best_len:
                best, best_len = size, len(alias)
    return best


def _color_aliases(color: str) -> set[str]:
    key = color.lower().strip()
    for group in COLOR_GROUPS:
        if key in group:
            return group | {key}
    return {key}


FUZZY_MIN_SCORE = 82   # "mahndi"->"mehndi", "pela"->"peela"; not "beach"->"peach"


def find_color(message: str, colors: list[str]) -> str | None:
    """Customer text -> one of the product's colours (as stored in the DB).

    1. the exact stored name (longest wins: "Rani Pink" before "Pink")
    2. any known spelling / Hindi name of that colour
    3. typos, by similarity
    """
    message = message.lower()

    # 1) literal
    literal = [c for c in colors if _has_word(message, c.lower().strip())]
    if literal:
        return max(literal, key=len)

    # 2) known variants (longest variant wins)
    best, best_len = None, 0
    for color in colors:
        for alias in _color_aliases(color):
            if _has_word(message, alias) and len(alias) > best_len:
                best, best_len = color, len(alias)
    if best:
        return best

    # 3) typos
    words = [w for w in re.findall(r"[a-z]+", message) if len(w) >= 4]
    best, best_score = None, 0
    for color in colors:
        for alias in _color_aliases(color):
            if " " in alias or len(alias) < 4 or not alias.isascii():
                continue
            for word in words:
                score = fuzz.ratio(word, alias)
                if score >= FUZZY_MIN_SCORE and score > best_score:
                    best, best_score = color, score
    return best
