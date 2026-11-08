
from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes.intent import detect_intent
from agent.nodes.language import detect_language
from agent.nodes.product import find_product
from agent.nodes.order import handle_order
from agent.nodes.response import generate_response
from database import checkpointer

builder = StateGraph(AgentState)

builder.add_node("detect_intent", detect_intent)
builder.add_node("detect_language", detect_language)
builder.add_node("find_product", find_product)
builder.add_node("handle_order", handle_order)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "detect_intent")
builder.add_edge("detect_intent", "detect_language")
builder.add_edge("detect_language", "find_product")
builder.add_edge("find_product", "handle_order")
builder.add_edge("handle_order", "generate_response")
builder.add_edge("generate_response", END)

graph = builder.compile(checkpointer=checkpointer)
