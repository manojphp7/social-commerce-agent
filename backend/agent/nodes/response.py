import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from agent.state import AgentState
from agent.nodes.messages import money, norm_lang, t


# A bigger model (qwen2.5:7b) follows Hinglish much better than 3b.
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
    temperature=0.3,
)

HISTORY_LIMIT = 10          # messages kept in the checkpoint
HISTORY_FOR_LLM = 6         # messages shown to the LLM

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GREETING_START = re.compile(r"^\s*(hi+|hello+|hey+|hlo|hola|namaste|namaskar)\b", re.I)

LANGUAGE_RULE = {
    "english": "Reply in simple English.",
    "hinglish": (
        "Reply in Hinglish: Hindi written in Roman letters mixed with English, "
        "like friends chat on WhatsApp. Never use Devanagari script."
    ),
    "hindi": "Reply in Hindi using Devanagari script.",
}

SYSTEM_PROMPT = """You are the friendly sales assistant of a small shop, chatting on Instagram DM.
{language_rule}

Rules:
- Maximum 2 short sentences. No markdown, no lists, at most one emoji.
- Answer what the customer actually said. Never repeat their words back.
- You do NOT know the catalogue. Never mention product names, prices, sizes or stock.
- If the customer wants to buy or see something, ask for the product name, the type of product, or a photo.
- For small talk, answer in one short line and gently ask what they would like to buy.
Output only the reply text."""


def _items(products: list[dict], language: str) -> str:
    lines = []
    compact = len(products) > 4   # keep 10 items under Instagram's 1000-char DM limit
    for i, p in enumerate(products, start=1):
        line = f"{i}. {p['name']} - ₹{money(p['price'])}"
        if compact:
            lines.append(line)
            continue
        extras = []
        if p.get("sizes"):
            extras.append(f"{t(language, 'lbl_sizes')}: {', '.join(p['sizes'])}")
        if p.get("colors"):
            extras.append(f"{t(language, 'lbl_colors')}: {', '.join(p['colors'])}")
        if extras:
            line += "\n   " + " | ".join(extras)
        lines.append(line)
    return "\n".join(lines)


def _product_detail(product: dict, state: AgentState, language: str) -> str:
    lines = [product["name"], f"{t(language, 'lbl_price')}: ₹{money(product['price'])}"]

    if product.get("sizes"):
        lines.append(f"{t(language, 'lbl_sizes')}: {', '.join(product['sizes'])}")
    if product.get("colors"):
        lines.append(f"{t(language, 'lbl_colors')}: {', '.join(product['colors'])}")

    if product.get("sizes") and not state.get("selected_size"):
        lines.append(t(language, "ask_size"))
    elif product.get("colors") and not state.get("selected_color"):
        lines.append(t(language, "ask_color"))
    else:
        lines.append(t(language, "ask_order"))

    return "\n".join(lines)


def _chat_reply(state: AgentState, language: str) -> str:
    """LLM only for free chat. History is passed so it never 'forgets'."""

    message = state.get("message_text") or ""
    history = state.get("history") or []

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT.format(language_rule=LANGUAGE_RULE[language])
        )
    ]
    for turn in history[-HISTORY_FOR_LLM:]:
        cls = HumanMessage if turn["role"] == "user" else AIMessage
        messages.append(cls(content=turn["content"]))
    messages.append(HumanMessage(content=message))

    try:
        reply = llm.invoke(messages).content.strip()
    except Exception as exc:
        print("LLM failed:", exc)
        return t(language, "steer")

    # Strip labels the model sometimes adds.
    reply = re.sub(r"^(reply|assistant|bot|response)\s*:\s*", "", reply, flags=re.I).strip()

    msg_norm = re.sub(r"\W+", " ", message.lower()).strip()
    rep_norm = re.sub(r"\W+", " ", reply.lower()).strip()

    bad = (
        not reply
        or (len(msg_norm) > 8 and rep_norm.startswith(msg_norm))      # echo
        or (language != "hindi" and DEVANAGARI.search(reply))         # wrong script
    )

    return t(language, "steer") if bad else reply


def _build_reply(state: AgentState) -> str:

    language = norm_lang(state.get("language"))
    intent = state.get("intent")
    product = state.get("product")
    products = state.get("products") or []
    history = state.get("history") or []
    message = state.get("message_text") or ""

    if intent == "product_image":
        if product:
            return _product_detail(product, state, language)
        return t(language, "image_not_found")

    if intent in ("product_lookup", "product_select"):
        if product:
            body = _product_detail(product, state, language)
        elif products:
            key = "products_found" if state.get("search_exact") else "products_closest"
            body = t(language, key, items=_items(products, language))
        else:
            body = t(language, "products_none")

        # First message was "Hi, ..." -> greet once.
        if not history and GREETING_START.match(message):
            body = t(language, "hello_prefix") + body
        return body

    if intent == "product_question":
        if product:
            return _product_detail(product, state, language)
        return t(language, "need_product")

    if intent in ("size_selection", "color_selection", "quantity_update", "confirm_order"):
        # Normally handled by the order node. Reaching here means no product
        # is selected: show the list again so the customer can pick one.
        if products:
            return t(language, "products_found", items=_items(products, language))
        return t(language, "need_product")

    if intent == "greeting":
        return t(language, "greeting" if history else "greeting_first")

    return _chat_reply(state, language)


def generate_response(state: AgentState) -> dict:

    # Order node already produced a reply.
    reply = state.get("reply") or _build_reply(state)
    print("Generated Reply:", reply)

    history = list(state.get("history") or [])
    history.append({"role": "user", "content": state.get("message_text") or "[image]"})
    history.append({"role": "assistant", "content": reply})

    return {"reply": reply, "history": history[-HISTORY_LIMIT:]}
