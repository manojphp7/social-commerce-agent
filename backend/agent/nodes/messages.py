"""Fixed, customer-facing texts in 3 languages.

Anything that involves products, prices or order steps is NOT written by the
LLM (a 3B model invents and copies things). It comes from these templates.
"""

LANGS = ("english", "hinglish", "hindi")

M = {
    "greeting_first": {
        "english": "Hi! 😊 What would you like to see today? Send a product name, SKU or photo.",
        "hinglish": "Hi! 😊 Aaj kya dekhna chahenge? Product ka naam, SKU ya photo bhej dijiye.",
        "hindi": "नमस्ते! 😊 आज आप क्या देखना चाहेंगे? प्रोडक्ट का नाम, SKU या फोटो भेज दीजिए।",
    },
    "greeting": {
        "english": "I'm good, thanks! 😊 What can I show you?",
        "hinglish": "Main badhiya hoon! 😊 Batao, aaj kya dikhaun?",
        "hindi": "मैं बढ़िया हूँ! 😊 बताइए, आज क्या दिखाऊँ?",
    },
    "hello_prefix": {
        "english": "Hi! 😊 ",
        "hinglish": "Hi! 😊 ",
        "hindi": "नमस्ते! 😊 ",
    },
    "products_found": {
        "english": "Here are some options 👇\n{items}\nWhich one do you like? Reply with the number or name.",
        "hinglish": "Ye rahe options 👇\n{items}\nKaun sa pasand aaya? Number ya naam bhej dijiye.",
        "hindi": "ये रहे विकल्प 👇\n{items}\nकौन सा पसंद आया? नंबर या नाम भेज दीजिए।",
    },
    "products_closest": {
        "english": "I couldn't find an exact match, but these are available 👇\n{items}\nDo any of these work for you?",
        "hinglish": "Exact match nahi mila, lekin ye available hain 👇\n{items}\nInme se koi pasand aaya?",
        "hindi": "सटीक मैच नहीं मिला, लेकिन ये उपलब्ध हैं 👇\n{items}\nइनमें से कोई पसंद आया?",
    },
    "pick_prompt": {
        "english": "Which one do you like? Reply with the number or name.",
        "hinglish": "Kaun sa pasand aaya? Number ya naam bhej dijiye.",
        "hindi": "कौन सा पसंद आया? नंबर या नाम भेज दीजिए।",
    },
    "pick_prompt_closest": {
        "english": "I couldn't find an exact match, but these are available. Do any of these work? Reply with the number or name.",
        "hinglish": "Exact match nahi mila, lekin ye available hain. Inme se koi pasand aaya? Number ya naam bhej dijiye.",
        "hindi": "सटीक मैच नहीं मिला, लेकिन ये उपलब्ध हैं। इनमें से कोई पसंद आया? नंबर या नाम भेज दीजिए।",
    },
    "products_none": {
        "english": "Sorry, no products are available right now.",
        "hinglish": "Sorry, abhi koi product available nahi hai.",
        "hindi": "माफ़ कीजिए, अभी कोई प्रोडक्ट उपलब्ध नहीं है।",
    },
    "lbl_price": {"english": "Price", "hinglish": "Price", "hindi": "कीमत"},
    "lbl_sizes": {"english": "Sizes", "hinglish": "Sizes", "hindi": "साइज़"},
    "lbl_colors": {"english": "Colors", "hinglish": "Colors", "hindi": "रंग"},
    "ask_size": {
        "english": "Please tell me your size.",
        "hinglish": "Apna size bata dijiye.",
        "hindi": "अपना साइज़ बता दीजिए।",
    },
    "ask_color": {
        "english": "Which colour would you like?",
        "hinglish": "Kaunsa colour chahiye?",
        "hindi": "कौन सा रंग चाहिए?",
    },
    "ask_order": {
        "english": "To order, reply 'Confirm order'.",
        "hinglish": "Order ke liye 'Confirm order' likhiye.",
        "hindi": "ऑर्डर के लिए 'Confirm order' लिखिए।",
    },
    "select_size": {
        "english": "Please select a size: {options}",
        "hinglish": "Size chuniye: {options}",
        "hindi": "साइज़ चुनिए: {options}",
    },
    "select_color": {
        "english": "Please select a color: {options}",
        "hinglish": "Colour chuniye: {options}",
        "hindi": "रंग चुनिए: {options}",
    },
    "need_product": {
        "english": "Please share the product name, SKU or a photo first.",
        "hinglish": "Pehle product ka naam, SKU ya photo bhej dijiye.",
        "hindi": "पहले प्रोडक्ट का नाम, SKU या फोटो भेज दीजिए।",
    },
    "image_not_found": {
        "english": "I couldn't match this photo to a product. Please send the name or SKU.",
        "hinglish": "Is photo se product match nahi hua. Naam ya SKU bhej dijiye.",
        "hindi": "इस फोटो से प्रोडक्ट मैच नहीं हुआ। नाम या SKU भेज दीजिए।",
    },
    "not_required": {
        "english": "Not required",
        "hinglish": "Zaroori nahi",
        "hindi": "आवश्यक नहीं",
    },
    "order_summary": {
        "english": (
            "Please review your order:\nProduct: {name}\nSize: {size}\n"
            "Color: {color}\nQuantity: {qty}\nTotal: ₹{total}\n\n"
            "Reply 'Confirm order' to confirm."
        ),
        "hinglish": (
            "Apna order check kar lijiye:\nProduct: {name}\nSize: {size}\n"
            "Color: {color}\nQuantity: {qty}\nTotal: ₹{total}\n\n"
            "Confirm karne ke liye 'Confirm order' likhiye."
        ),
        "hindi": (
            "अपना ऑर्डर देख लीजिए:\nप्रोडक्ट: {name}\nसाइज़: {size}\n"
            "रंग: {color}\nमात्रा: {qty}\nकुल: ₹{total}\n\n"
            "कन्फर्म करने के लिए 'Confirm order' लिखिए।"
        ),
    },
    "order_confirmed": {
        "english": (
            "Your selections are confirmed! ✅\nProduct: {name}\nSize: {size}\n"
            "Color: {color}\nQuantity: {qty}\nTotal: ₹{total}\n\n"
            "The shop team will contact you to complete the order."
        ),
        "hinglish": (
            "Aapki selection confirm ho gayi! ✅\nProduct: {name}\nSize: {size}\n"
            "Color: {color}\nQuantity: {qty}\nTotal: ₹{total}\n\n"
            "Shop team order complete karne ke liye aapse contact karegi."
        ),
        "hindi": (
            "आपका चयन कन्फर्म हो गया! ✅\nप्रोडक्ट: {name}\nसाइज़: {size}\n"
            "रंग: {color}\nमात्रा: {qty}\nकुल: ₹{total}\n\n"
            "शॉप टीम ऑर्डर पूरा करने के लिए आपसे संपर्क करेगी।"
        ),
    },
    "steer": {
        "english": "Tell me what you'd like to see: a product name, a type (like shoes) or a photo.",
        "hinglish": "Batao kya dekhna hai: product ka naam, type (jaise shoes) ya photo bhej dijiye.",
        "hindi": "बताइए क्या देखना है: प्रोडक्ट का नाम, टाइप (जैसे जूते) या फोटो भेज दीजिए।",
    },
}


def norm_lang(language: str | None) -> str:
    if language in LANGS:
        return language
    return "hinglish"  # unknown -> default for an Indian shop


def t(language: str | None, key: str, **kwargs) -> str:
    text = M[key][norm_lang(language)]
    return text.format(**kwargs) if kwargs else text


def money(value) -> str:
    value = float(value)
    return f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
