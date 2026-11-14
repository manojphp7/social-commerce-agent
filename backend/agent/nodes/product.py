import re

from rapidfuzz import fuzz
from sqlalchemy import select

from database import SessionLocal
from models import Product
from agent.state import AgentState
from agent.nodes.intent import PRODUCT_REQUEST_PATTERNS, matches_any, parse_ordinal


MAX_RESULTS = 10

# Words that carry no product meaning (English + Hinglish filler).
STOPWORDS = {
    "show", "find", "search", "display", "suggest", "recommend", "want", "need",
    "looking", "for", "a", "an", "the", "me", "i", "you", "please", "pls",
    "dikha", "dikhao", "dikhana", "dikhado", "chahiye", "chahie", "batao",
    "bata", "btao", "de", "do", "dena", "dedo", "kya", "hai", "hain", "ho",
    "hu", "hun", "hoon", "ka", "ki", "ke", "ko", "se", "mein", "mujhe",
    "mereko", "tumhare", "tumhara", "aapke", "aapka", "pas", "paas", "jo",
    "bhi", "koi", "kuch", "ache", "acha", "accha", "achha", "achhe", "type",
    "wala", "wali", "wale", "hi", "hello", "hey", "kaise", "aap", "tum",
    "mera", "meri", "of", "and", "or", "with", "have", "any", "your", "ur",
    "available", "products", "product", "collection", "catalog", "catalogue",
    "items", "item", "kitne", "kitna", "price", "rate", "sab", "sabhi", "all",
    "aur", "new", "best", "good", "some", "few", "more", "bhai", "yaar",
    "apne", "apna", "liye", "lie", "k", "wo", "woh", "ye", "yeh", "isme",
    "mai", "main", "hum", "ek", "is", "in", "on", "to", "it", "kar", "karo",
    "dekhna", "dekho", "lena", "chaiye", "yaha", "yahan", "aapne", "idea",
}

# Hindi/Hinglish words -> the word used in product names.
ALIASES = {
    "joote": "shoe", "jute": "shoe", "joota": "shoe", "jooto": "shoe",
    "footwear": "shoe", "chappal": "slipper", "chappals": "slipper",
}


def normalize_sku(sku: str) -> str:
    """Normalize OCR SKU text to reduce common character errors."""
    return sku.strip().upper().replace("O", "0").replace(" ", "")


def _stem(word: str) -> str:
    word = ALIASES.get(word, word)
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    return ALIASES.get(word, word)


def tokenize(text: str) -> list[str]:
    """Search keywords of a message: 'sport shoes dikha' -> ['sport', 'shoe']."""
    tokens = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS or word.isdigit() or len(word) < 2:
            continue
        stem = _stem(word)
        if stem not in tokens:
            tokens.append(stem)
    return tokens


def _haystack(product: dict) -> tuple[str, str]:
    text = f"{product['name']} {product.get('category') or ''} {product['sku']}"
    words = [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]
    return " ".join(words), "".join(words)


def _has(product: dict, token: str) -> bool:
    spaced, compact = _haystack(product)
    return token in spaced or token in compact


def _in_message(message: str, needle: str) -> bool:
    needle = needle.strip().lower()
    return bool(needle) and bool(
        re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", message)
    )


def clean_options(values, configurable) -> list[str]:
    """NULL / [NULL] / [''] / non-configurable products -> no size/colour."""
    if not configurable:
        return []
    return [str(v).strip() for v in (values or []) if v is not None and str(v).strip()]


def load_products(shop_id: int) -> list[dict]:
    """All products of a shop as plain dicts (no detached ORM objects)."""
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Product).where(Product.shop_id == shop_id)
        ).scalars().all()

        return [
            {
                "id": row.id,
                "name": row.product_name,
                "category": row.category,
                "sku": row.sku,
                "price": float(row.price),
                "sizes": clean_options(row.sizes, row.is_configurable),
                "colors": clean_options(row.colors, row.is_configurable),
                "is_configurable": row.is_configurable,
                "image_path": row.image_path,
            }
            for row in rows
        ]
    finally:
        db.close()


def search_products(products, new_tokens, previous_tokens, explicit=False):
    """Returns (results, tokens_used, exact_match_found)."""

    if not new_tokens and not previous_tokens:
        # "kuch bhi dikha" with nothing known yet: show the newest items.
        return sorted(products, key=lambda p: -p["id"])[:MAX_RESULTS], [], True

    attempts = []
    refined = list(dict.fromkeys(previous_tokens + new_tokens)) if (new_tokens and previous_tokens) else None
    only_new = new_tokens or previous_tokens

    if refined and explicit:
        # "suit dikha" after "kurti": a fresh request, try it on its own first.
        attempts += [only_new, refined]
    elif refined:
        # "sport type ka ho" after "shoes": refine the running search.
        attempts += [refined, only_new]
    else:
        attempts.append(only_new)

    def relaxed(tokens):
        # any keyword matches, best score first
        scored = [(sum(_has(p, t) for t in tokens), p) for p in products]
        scored = [(s, p) for s, p in scored if s > 0]
        scored.sort(key=lambda sp: (-sp[0], -sp[1]["id"]))
        return [p for _, p in scored]

    for tokens in attempts:
        found = [p for p in products if all(_has(p, t) for t in tokens)]
        if found:
            found.sort(key=lambda p: -p["id"])
            # Few exact hits: fill the list with the next best matches
            # ("sport shoes" -> sport shoes first, then other shoes).
            for extra in relaxed(tokens):
                if len(found) >= MAX_RESULTS:
                    break
                if extra not in found:
                    found.append(extra)
            return found[:MAX_RESULTS], tokens, True

    tokens = new_tokens or previous_tokens
    scored = relaxed(tokens)
    if scored:
        return scored[:MAX_RESULTS], tokens, True

    return [], tokens, False


def match_by_ocr(products, sku_candidates):
    """Exact (after normalisation), then fuzzy SKU match from OCR text."""

    candidates = [normalize_sku(c) for c in sku_candidates if c]
    if not candidates:
        return None

    by_sku = {normalize_sku(p["sku"]): p for p in products}

    for candidate in candidates:
        if candidate in by_sku:
            return by_sku[candidate]

    best, best_score, second = None, 0, 0
    for candidate in candidates:
        for product in products:
            score = fuzz.ratio(candidate, normalize_sku(product["sku"]))
            if score > best_score:
                second, best_score, best = best_score, score, product
            elif score > second:
                second = score

    if best_score >= 85 and (best_score - second) >= 8:
        return best

    return None


def _reset_if_changed(previous: dict | None, new: dict | None) -> dict:
    if not previous or not new or previous.get("id") != new.get("id"):
        return {"selected_size": None, "selected_color": None, "quantity": 1}
    return {}


def find_product(state: AgentState) -> dict:

    intent = state.get("intent")
    message = (state.get("message_text") or "").lower()
    previous = state.get("product")
    shown = state.get("products") or []

    # The customer picked one of the products we just listed.
    if intent == "product_select":
        idx = parse_ordinal(message, len(shown))
        if idx is not None:
            chosen = shown[idx]
            return {"product": chosen, **_reset_if_changed(previous, chosen)}
        return {}

    products = load_products(state["shop_id"])

    # 1) Image / OCR
    if state.get("image_path"):
        matched = match_by_ocr(products, state.get("sku_candidates") or [])
        if not matched:
            print("No product matched from the new image.")
            # Never reuse an old product for an unrecognised new image.
            return {"product": None}
        return {"product": matched, "products": [], **_reset_if_changed(previous, matched)}

    # 2) Message names exactly one product (name or SKU)
    named = [
        p for p in products
        if _in_message(message, p["name"]) or _in_message(message, p["sku"])
    ]

    if len(named) == 1 and intent not in ("confirm_order",):
        matched = named[0]
        print("Matched Product:", matched)
        result = {"product": matched, "products": [], **_reset_if_changed(previous, matched)}
        if intent in ("product_lookup", "general_conversation", "greeting", "unknown", "product_question"):
            result["intent"] = "product_lookup"
        return result

    # 3) Keyword search ("sport shoes", "jo bhi ho" after a search)
    if intent == "product_lookup":
        new_tokens = tokenize(message)
        previous_tokens = (state.get("search_group") or "").split()

        explicit = matches_any(message, PRODUCT_REQUEST_PATTERNS)
        results, used_tokens, exact = search_products(
            products, new_tokens, previous_tokens, explicit
        )

        if not results and products:
            # Nothing matches: offer the newest items as honest alternatives.
            results = sorted(products, key=lambda p: -p["id"])[:MAX_RESULTS]

        print(f"Search tokens={used_tokens} exact={exact} results={[p['name'] for p in results]}")

        result = {
            "products": results,
            "search_group": " ".join(used_tokens) if exact else state.get("search_group"),
            "search_exact": exact,
            "product": None,
            "selected_size": None,
            "selected_color": None,
            "quantity": 1,
        }

        # A single hit can be ordered directly ("size M").
        if exact and len(results) == 1:
            result["product"] = results[0]

        return result

    # Any other intent: keep the current checkpoint product untouched.
    return {}
