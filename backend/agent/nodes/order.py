
import re

from agent.state import AgentState


def handle_order(state: AgentState) -> dict:

    product = state.get("product")

    if not product:
        return {
            "reply": "Please select a product first."
        }

    message = (state.get("message_text") or "").strip().lower()

    sizes = product.get("sizes") or []
    colors = product.get("colors") or []

    selected_size = state.get("selected_size")
    selected_color = state.get("selected_color")

    # Detect size from customer message
    if sizes and not selected_size:

        size_aliases = {
            "small": ["small", "s"],
            "medium": ["medium", "med", "m"],
            "large": ["large", "l"],
            "extra large": ["extra large", "x-large", "xl"],
            "xxl": ["xxl", "2xl"],
        }

        for size in sizes:

            normalized_size = size.lower()

            aliases = size_aliases.get(
                normalized_size,
                [normalized_size]
            )

            for alias in aliases:

                pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

                if re.search(pattern, message):
                    selected_size = size
                    break

            if selected_size:
                break

    # Detect color from customer message
    if colors and not selected_color:

        for color in colors:

            pattern = rf"(?<!\w){re.escape(color.lower())}(?!\w)"

            if re.search(pattern, message):
                selected_color = color
                break

    # Detect quantity; default is 1
    quantity = state.get("quantity") or 1

    quantity_match = re.search(
        r"\b(\d+)\s*(?:pieces?|pcs?|items?|units?)\b",
        message
    )

    if quantity_match:
        quantity = max(1, int(quantity_match.group(1)))

    # Ask for size only if product has size variations
    if sizes and not selected_size:
        return {
            "selected_color": selected_color,
            "quantity": quantity,
            "reply": f"Please select a size: {', '.join(sizes)}"
        }

    # Ask for color only if product has color variations
    if colors and not selected_color:
        return {
            "selected_size": selected_size,
            "quantity": quantity,
            "reply": f"Please select a color: {', '.join(colors)}"
        }

    # Order details are ready
    total = float(product["price"]) * quantity

    return {
        "selected_size": selected_size,
        "selected_color": selected_color,
        "quantity": quantity,
        "reply": (
            f"Order details confirmed!\n"
            f"Product: {product['name']}\n"
            f"Size: {selected_size or 'Not required'}\n"
            f"Color: {selected_color or 'Not required'}\n"
            f"Quantity: {quantity}\n"
            f"Total: ₹{total:.2f}"
        )
    }
