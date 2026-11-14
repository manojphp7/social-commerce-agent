import re

from agent.state import AgentState

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Roman-script Hindi words. "me", "to", "do" are left out on purpose
# because they are also normal English words.
HINGLISH_WORDS = {
    "hai", "hain", "ho", "hu", "hun", "hoon", "mujhe", "mereko", "mera", "meri",
    "chahiye", "chahie", "kya", "kaise", "kese", "kaisi", "krna", "karna", "kar",
    "kitna", "kitne", "kitni", "kuch", "aur", "dikha", "dikhao", "dikhana",
    "dikhado", "batao", "bata", "btao", "tumhare", "tumhara", "aapke", "aapka",
    "aap", "tum", "nahi", "nhi", "haan", "han", "ka", "ki", "ke", "ko", "se",
    "mein", "pas", "paas", "jo", "bhi", "koi", "acha", "accha", "ache", "achha",
    "achhe", "bhai", "yaar", "lena", "wala", "wali", "wale", "kab", "kahan",
    "kidhar", "abhi", "bohot", "bahut", "thoda", "lie", "liye", "mai", "main",
    "hum", "kaun", "kaunsa", "konsa", "isme", "iska", "iski", "uska", "joote",
    "jute", "kapde", "dedo", "dena", "de", "theek", "thik", "sahi", "kaam",
}

ENGLISH_WORDS = {
    "show", "me", "the", "i", "want", "please", "what", "is", "do", "you",
    "have", "how", "much", "can", "need", "looking", "for", "this", "that",
    "with", "are", "your", "my", "any", "would", "like", "which", "where",
    "price", "available",
}


def detect_language(state: AgentState) -> dict:

    message = (state.get("message_text") or "").strip()
    previous = state.get("language")

    if not message:
        # Image-only message: keep the language of the conversation.
        return {"language": previous if previous in ("english", "hinglish", "hindi") else "unknown"}

    words = re.findall(r"[a-z0-9']+", message.lower())
    hinglish_hits = sum(1 for w in words if w in HINGLISH_WORDS)
    english_hits = sum(1 for w in words if w in ENGLISH_WORDS)

    if DEVANAGARI.search(message):
        language = "hindi"
    elif hinglish_hits and hinglish_hits >= english_hits:
        language = "hinglish"
    elif english_hits:
        language = "english"
    elif previous in ("english", "hinglish", "hindi"):
        # Neutral message ("sport shoes", "M", "confirm"): do not flip language.
        language = previous
    else:
        language = "english"

    print("Detected Language:", language)

    return {"language": language}
