
from typing import TypedDict, Optional


class AgentState(TypedDict):

    shop_id: int
    sender_id: str

    message_text: Optional[str]
    image_path: Optional[str]

    ocr_results: list[str]
    sku_candidates: list[str]

    product: Optional[dict]

    selected_size: Optional[str]
    selected_color: Optional[str]
    quantity: Optional[int]

    intent: Optional[str]
    language: Optional[str]

    reply: Optional[str]
