from agent.state import AgentState


def detect_language(state: AgentState) -> dict:

    message = state.get("message_text") or ""

    if not message:
        language = "unknown"

    elif any(char in message for char in "अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह"):
        language = "hindi"

    elif any(word in message.lower() for word in ["hai", "hain", "mujhe", "chahiye", "kya", "kaise", "krna","kitna","kitne","kuch","aur"]):
        language = "hinglish"

    else:
        language = "english"

    print("Detected Language:", language)

    return {"language": language}