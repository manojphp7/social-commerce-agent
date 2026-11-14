import re

from agent.state import AgentState
from agent.nodes.options import SIZE_ALIASES, find_color, find_size  # noqa: F401


CONFIRM_MESSAGES = {
    "confirm",
    "confirm order",
    "yes confirm",
    "place order",
    "please confirm order",
    "confirm kar do",
    "order confirm",
}

# Words that name a kind of product.
PRODUCT_CLASS_PATTERN = (
    r"\b(shoes?|sneakers?|sandals?|slippers?|chappals?|joote|jute|boots?|"
    r"shirts?|t-?shirts?|jeans|trousers|pants|dress(?:es)?|bags?|watch(?:es)?|"
    r"jackets?|hoodies?|kurtas?|kapde)\b"
)

PRODUCT_REQUEST_PATTERNS = [
    r"\b(show|find|search|display|suggest|recommend)\b",
    r"\b(want|need|looking for)\b",
    r"\b(dikha|dikhao|dikhana|dikhado|chahiye|chahie|batao|btao)\b",
    r"\b(available|products|collection|catalog|catalogue|items)\b",
    PRODUCT_CLASS_PATTERN,
]

# "I don't care, show anything": only meaningful once a search is running.
VAGUE_PATTERNS = [
    r"\b(jo bhi|kuch bhi|koi bhi|anything|whatever|sab dikha|sabhi|all of them)\b",
]

PRODUCT_QUESTION_PATTERNS = [
    r"\b(price|cost|rate|sizes?|colou?rs?|availability)\b",
    r"\b(kitne ka|kitne ki|kya price|kya rate)\b",
    r"\b(iska|iski|iske|uska|uski|uske)\b",
    r"\b(previous|pichle|pichhli|uploaded|sent)\b",
]

GREETING_PATTERNS = [
    r"^\s*(hi+|hello+|hey+|hlo|hola|namaste|namaskar)\b",
    r"\b(good (morning|afternoon|evening))\b",
    r"\b(kaise ho|kese ho|kaisi ho|kaise hain|how are you|kya haal)\b",
]

SMALLTALK_PATTERNS = [
    r"\b(thanks|thank you|thanku|shukriya|dhanyawad|bye|ok|okay|theek hai|thik hai)\b",
]

ORDINALS = {
    "1": 0, "1st": 0, "first": 0, "pehla": 0, "pahla": 0, "pehli": 0, "one": 0,
    "2": 1, "2nd": 1, "second": 1, "dusra": 1, "doosra": 1, "dusri": 1, "two": 1,
    "3": 2, "3rd": 2, "third": 2, "teesra": 2, "tisra": 2, "teesri": 2, "three": 2,
    "4": 3, "4th": 3, "fourth": 3, "chautha": 3, "four": 3,
    "5": 4, "5th": 4, "fifth": 4, "paanchva": 4, "five": 4,
    "6": 5, "6th": 5, "sixth": 5, "six": 5,
    "7": 6, "7th": 6, "seventh": 6, "seven": 6,
    "8": 7, "8th": 7, "eighth": 7, "eight": 7,
    "9": 8, "9th": 8, "ninth": 8, "nine": 8,
    "10": 9, "10th": 9, "tenth": 9, "ten": 9,
}


QUANTITY_WORDS = {"piece", "pieces", "pc", "pcs", "item", "items", "unit", "units", "pair", "pairs"}


def contains_option(message: str, option: str) -> bool:
    pattern = rf"(?<!\w){re.escape(option.lower())}(?!\w)"
    return bool(re.search(pattern, message.lower()))


def matches_any(message: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)


def parse_ordinal(message: str, count: int) -> int | None:
    """'pehla wala', '2', 'third one' -> index into the shown product list."""
    words = re.findall(r"[a-z0-9]+", message.lower())
    for pos, word in enumerate(words):
        idx = ORDINALS.get(word)
        if idx is None or idx >= count:
            continue
        # "2 pieces", "1 pair" is a quantity, not a list position.
        if pos + 1 < len(words) and words[pos + 1] in QUANTITY_WORDS:
            continue
        # Bare digits only count in short replies ("2", "number 2"),
        # so "size 3" or "9 number" in a long sentence is not a pick.
        if word.isdigit() and not (len(words) <= 2 or "number" in words):
            continue
        return idx
    return None


def detect_intent(state: AgentState) -> dict:

    message = (state.get("message_text") or "").strip().lower()
    normalized_message = re.sub(r"[^\w\s]", "", message).strip()

    product = state.get("product")
    products = state.get("products") or []
    searching = bool(state.get("search_group"))

    has_class = matches_any(message, [PRODUCT_CLASS_PATTERN])

    if state.get("image_path"):
        intent = "product_image"

    elif normalized_message in CONFIRM_MESSAGES:
        intent = "confirm_order"

    # "pehla wala", "2" -> pick from the list that was just shown.
    elif products and not product and parse_ordinal(message, len(products)) is not None:
        intent = "product_select"

    # While a product is selected, size/colour/quantity beat everything else.
    # (Otherwise "size M chahiye" is mistaken for a NEW product search.)
    elif product and re.search(r"\b(\d+)\s*(?:pieces?|pcs?|items?|units?|pair|pairs)\b", message):
        intent = "quantity_update"

    elif product and find_size(message, product.get("sizes") or []):
        intent = "size_selection"

    elif product and find_color(message, product.get("colors") or []):
        intent = "color_selection"

    elif product and not has_class and matches_any(message, PRODUCT_QUESTION_PATTERNS):
        intent = "product_question"

    # Size/quantity answer while nothing is selected yet: ask to pick first
    # instead of starting a new search with the word "pieces".
    elif (
        products and not product and not has_class
        and re.search(r"\b(\d+\s*(?:pieces?|pcs?|pair|pairs)|size|sizes)\b", message)
    ):
        intent = "size_selection"

    elif matches_any(message, PRODUCT_REQUEST_PATTERNS):
        intent = "product_lookup"

    elif searching and not product and matches_any(message, VAGUE_PATTERNS):
        intent = "product_lookup"

    elif matches_any(message, PRODUCT_QUESTION_PATTERNS):
        # "price kya hai?" with no selected product but a list on screen.
        intent = "product_lookup" if products else "general_conversation"

    elif matches_any(message, GREETING_PATTERNS):
        intent = "greeting"

    elif matches_any(message, SMALLTALK_PATTERNS):
        intent = "smalltalk"

    # Follow-up answer inside a running search: "sport type ka ho".
    elif searching and not product and message:
        intent = "product_lookup"

    elif message:
        intent = "general_conversation"

    else:
        intent = "unknown"

    print("Detected Intent:", intent)

    return {"intent": intent}
