import re

from agent.state import AgentState
from agent.nodes.options import find_color, find_size
from agent.nodes.messages import money, t


def _summary_fields(language, product, size, color, quantity) -> dict:
    return {
        "name": product["name"],
        "size": size or t(language, "not_required"),
        "color": color or t(language, "not_required"),
        "qty": quantity,
        "total": money(float(product["price"]) * quantity),
    }


def handle_order(state: AgentState) -> dict:

    language = state.get("language")
    product = state.get("product")

    if not product:
        return {"reply": t(language, "need_product")}

    message = (state.get("message_text") or "").strip().lower()
    intent = state.get("intent")

    sizes = product.get("sizes") or []
    colors = product.get("colors") or []

    selected_size = state.get("selected_size")
    selected_color = state.get("selected_color")
    quantity = state.get("quantity") or 1

    detected_size = find_size(message, sizes)
    detected_color = find_color(message, colors)

    if detected_size:
        selected_size = detected_size

    if detected_color:
        selected_color = detected_color

    quantity_match = re.search(
        r"\b(\d+)\s*(?:pieces?|pcs?|items?|units?|pair|pairs)\b", message
    )

    if quantity_match:
        quantity = max(1, int(quantity_match.group(1)))

    result = {
        "selected_size": selected_size,
        "selected_color": selected_color,
        "quantity": quantity,
    }

    if sizes and not selected_size:
        result["reply"] = t(language, "select_size", options=", ".join(sizes))
        return result

    if colors and not selected_color:
        result["reply"] = t(language, "select_color", options=", ".join(colors))
        return result

    fields = _summary_fields(language, product, selected_size, selected_color, quantity)

    # Confirm only after an explicit customer confirmation.
    if intent == "confirm_order":
        result["reply"] = t(language, "order_confirmed", **fields)
        # Order done: start the next conversation topic from a clean slate.
        result.update(
            {
                "product": None,
                "products": [],
                "search_group": None,
                "selected_size": None,
                "selected_color": None,
                "quantity": 1,
            }
        )
        return result

    result["reply"] = t(language, "order_summary", **fields)
    return result
