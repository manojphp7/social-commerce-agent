from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes.intent import detect_intent
from agent.nodes.language import detect_language
from agent.nodes.product import find_product
from agent.nodes.order import handle_order
from agent.nodes.response import generate_response
from database import checkpointer


ORDER_INTENTS = {
    "size_selection",
    "color_selection",
    "confirm_order",
    "quantity_update",
}


def route_after_product(state: AgentState) -> str:

    # find_product may have changed the intent (e.g. name matched -> lookup),
    # so read it from the merged state.
    intent = state.get("intent")

    product = state.get("product")

    if intent in ORDER_INTENTS and product:
        return "handle_order"

    # Product chosen but size/colour still missing and the message was not
    # understood ("Gray", "m le lunga", typos): ask again with the options
    # instead of letting the LLM improvise.
    if product and intent in ("general_conversation", "unknown"):
        size_missing = bool(product.get("sizes")) and not state.get("selected_size")
        color_missing = bool(product.get("colors")) and not state.get("selected_color")
        if size_missing or color_missing:
            return "handle_order"

    return "generate_response"


builder = StateGraph(AgentState)

builder.add_node("detect_intent", detect_intent)
builder.add_node("detect_language", detect_language)
builder.add_node("find_product", find_product)
builder.add_node("handle_order", handle_order)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "detect_intent")
builder.add_edge("detect_intent", "detect_language")
builder.add_edge("detect_language", "find_product")

builder.add_conditional_edges(
    "find_product",
    route_after_product,
    {
        "handle_order": "handle_order",
        "generate_response": "generate_response",
    },
)

builder.add_edge("handle_order", "generate_response")
builder.add_edge("generate_response", END)

graph = builder.compile(checkpointer=checkpointer)
