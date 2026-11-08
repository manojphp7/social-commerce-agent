from typing import Literal

from agent.state import AgentState


def detect_intent(state: AgentState) -> dict:

    message = state.get("message_text") or ""

    if state.get("image_path"):
        intent = "product_image"

    elif message:
        intent = "text_message"

    else:
        intent = "unknown"

    print("Detected Intent:", intent)

    return {
        "intent": intent
    }