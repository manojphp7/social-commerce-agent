from typing import TypedDict, Optional


class AgentState(TypedDict):

    shop_id: int
    sender_id: str

    message_text: Optional[str]
    image_path: Optional[str]

    ocr_results: list[str]
    sku_candidates: list[str]

    # Single selected product (used for order flow).
    product: Optional[dict]

    # Last search results shown to the customer (max 3).
    products: list[dict]
    search_group: Optional[str]   # e.g. "shoes" - remembered across turns
    search_exact: Optional[bool]  # False = exact match not found, showing closest

    selected_size: Optional[str]
    selected_color: Optional[str]
    quantity: Optional[int]

    intent: Optional[str]
    language: Optional[str]

    # Last few chat turns: [{"role": "user"|"assistant", "content": "..."}]
    history: list[dict]

    reply: Optional[str]
