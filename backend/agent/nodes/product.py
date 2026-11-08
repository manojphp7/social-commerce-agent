
from sqlalchemy import select
from rapidfuzz import fuzz

from database import SessionLocal
from models import Product
from agent.state import AgentState


def normalize_sku(sku: str) -> str:
    """Normalize OCR SKU text to reduce common character errors."""
    return sku.strip().upper().replace("O", "0").replace(" ", "")


def find_product(state: AgentState) -> dict:

    shop_id = state["shop_id"]
    message = (state.get("message_text") or "").lower()
    sku_candidates = state.get("sku_candidates") or []

    db = SessionLocal()

    try:
        products = db.execute(
            select(Product).where(Product.shop_id == shop_id)
        ).scalars().all()

        matched_product = state.get("product")

        # 1. Match product name or SKU from the message.
        for product in products:

            product_name = product.product_name.lower()
            sku = product.sku.lower()

            if product_name in message or sku in message:
                matched_product = product
                break

        # 2. Match OCR SKU candidates using normalization.
        if not matched_product and sku_candidates:

            normalized_candidates = [
                normalize_sku(candidate)
                for candidate in sku_candidates
                if candidate
            ]

            normalized_products = {
                normalize_sku(product.sku): product
                for product in products
            }

            # Exact match after normalization.
            for candidate in normalized_candidates:
                if candidate in normalized_products:
                    matched_product = normalized_products[candidate]
                    break

            # 3. Fuzzy matching if exact matching fails.
            if not matched_product:

                best_match = None
                best_score = 0
                second_best_score = 0

                for candidate in normalized_candidates:
                    for product in products:

                        score = fuzz.ratio(
                            candidate,
                            normalize_sku(product.sku)
                        )

                        if score > best_score:
                            second_best_score = best_score
                            best_score = score
                            best_match = product

                        elif score > second_best_score:
                            second_best_score = score

                if best_score >= 85 and (best_score - second_best_score) >= 8:
                    matched_product = best_match

        if not matched_product:
            print("Product not found")
            return {"product": None}
        
        if isinstance(matched_product, dict):
            return {"product": matched_product}
    
        product_data = {
            "id": matched_product.id,
            "name": matched_product.product_name,
            "sku": matched_product.sku,
            "price": float(matched_product.price),
            "sizes": matched_product.sizes or [],
            "colors": matched_product.colors or [],
            "is_configurable": matched_product.is_configurable,
        }

        print("Matched Product:", product_data)

        return {"product": product_data}

    finally:
        db.close()
