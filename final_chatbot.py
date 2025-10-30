import json
import re
from rapidfuzz import process, fuzz
from datetime import datetime, date
import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# ------------------ FILE PATHS ------------------
CHAT_FILE = "chat_data.json"
ZEPTO_FILE = "zepto_data.json"
UNANSWERED_FILE = "unanswered.json"

# ------------------ LOAD JSON DATA ------------------
with open(CHAT_FILE, "r", encoding="utf-8") as f:
    faq_data = json.load(f)

with open(ZEPTO_FILE, "r", encoding="utf-8") as f:
    zepto_data = json.load(f)

if not os.path.exists(UNANSWERED_FILE):
    with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ------------------ LOAD API KEY ------------------
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

client = InferenceClient(
    model="meta-llama/Llama-3.2-1B-Instruct",
    token=HUGGINGFACE_API_KEY
)

# ------------------ CONTEXT MEMORY ------------------
context_memory = {"last_item": None, "last_category": None}

# ------------------ HELPER FUNCTIONS ------------------
def clean_text(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def save_unanswered(question):
    with open(UNANSWERED_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    entry = {"question": question, "timestamp": datetime.now().isoformat()}
    data.append(entry)

    with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_context(item=None, category=None):
    if item:
        context_memory["last_item"] = item
    if category:
        context_memory["last_category"] = category

# ------------------ CHECK FUNCTIONS ------------------
def check_faq(user_input):
    questions = list(faq_data.keys())
    best_match, score, _ = process.extractOne(
        user_input, questions, scorer=fuzz.token_set_ratio
    )
    if score > 70:
        return faq_data[best_match]
    return None

def extract_quantity(user_input):
    """
    Extracts quantity and unit from user input.
    Example: '5 kg apples' → (5, 'kg'), '3 packets milk' → (3, 'packets')
    """
    match = re.search(r"(\d+)\s*(kg|kgs|g|grams|packet|packets|piece|pieces|unit|units)?", user_input)
    if match:
        qty = int(match.group(1))
        unit = match.group(2) or ""
        return qty, unit.strip()
    return None, None

def normalize_word(word):
    """Convert simple plurals to singular (e.g., apples → apple, packets → packet)."""
    if word.endswith("ies"):
        return word[:-3] + "y"
    elif word.endswith("es") and word[:-2] not in ["cheese", "dress"]:
        return word[:-2]
    elif word.endswith("s") and word not in ["gas", "glass", "class"]:
        return word[:-1]
    return word

def check_items(user_input):
    user_input = user_input.lower()

    restricted = {
        "large_appliances": {
            "keywords": ["washing machine", "fridge", "refrigerator", "television", "tv", "microwave", "ac"],
            "message": "Sorry, Zepto doesn’t sell large appliances like these. It mainly offers groceries and small gadgets."
        },
        "footwear": {
            "keywords": ["shoes", "sandals", "slippers", "footwear"],
            "message": "Sorry, Zepto doesn’t sell footwear. It mainly offers groceries, daily essentials, and home products."
        },
        "fashion": {
            "keywords": ["clothes", "tshirt", "jeans", "dress", "jacket"],
            "message": "Sorry, Zepto doesn’t sell fashion items like clothes or accessories."
        }
    }

    # ❌ Restricted items first
    for category, data in restricted.items():
        if any(word in user_input for word in data["keywords"]):
            return data["message"]

    # 🧩 Handle electronics explicitly
    if "electronics" in user_input or "electronic items" in user_input:
        return (
            "Zepto offers small electronic items such as chargers, cables, earphones, and power banks. "
            "However, it doesn’t sell large appliances like TVs, fridges, or washing machines. "
            "You can explore available products under the 'Electronics' category on the Zepto app."
        )

    # 🧩 Extract quantity if mentioned
    qty, unit = extract_quantity(user_input)

    # Normalize user words for plural handling
    user_words = [normalize_word(w) for w in user_input.split()]

    for category, items in zepto_data["items"].items():
        for item, price in items.items():
            item_norm = normalize_word(item)
            # Check for plural/singular + fuzzy match
            if item_norm in user_words or fuzz.partial_ratio(item_norm, user_input) > 75:
                update_context(item, category)

                # 💰 Bulk pricing logic
                if qty and price:
                    total = qty * price
                    return f"Yes, {qty} {unit} of {item.title()} will cost ₹{total} (₹{price} per unit)."

                # 🚚 Ordering intent check
                if user_input.startswith(("how to", "how can", "where to", "find")):
                    return None

                return f"{item.title()} is available under {category.title()} for ₹{price}."
    return None



def check_festivals(user_input):
    today = str(date.today())
    for fest, details in zepto_data["festivals"].items():
        if fest in user_input.lower() or details["date"] == today:
            return f"{details['wish']} 🎉 {details['offer']}"
    return None

## ------------------ PROMPT ENGINEERING LAYERS ------------------
SYSTEM_PROMPT = """
You are Zepto’s official AI Shopping Assistant.

Your responsibilities:
- Help users with **product availability, prices, categories, and ordering steps** for items sold on Zepto.
- Zepto sells groceries, fruits, vegetables, meat, dairy, snacks, beverages, home care, kitchen supplies, pet food, stationery, and small electronics (chargers, cables, earphones, power banks).
- Zepto does **not** sell large appliances (TVs, fridges, washing machines), fashion, footwear, cars, or electronics like laptops or phones.
- If an item seems missing from the JSON, assume you can access Zepto’s live catalog and answer naturally.
- Give approximate information when exact data isn’t available (e.g., “around ₹40–₹60 per pack”).
- Never mention “I don’t have data” or “I can’t check.” Instead, respond naturally as if using Zepto’s real product data.
- Tone: professional, helpful, concise, friendly.
- Format: 1–2 short paragraphs or 3–5 bullet points.
"""

INSTRUCTION_PROMPT = """
Guidelines for every response:
- If Zepto sells the item → confidently say “Yes,” and describe the category and price range.
- If Zepto doesn’t sell it (e.g., laptops, shoes, fashion) → say “No, Zepto doesn’t sell [item]. It mainly offers groceries, essentials, and small electronics.”
- If user asks “how to order,” give 3–5 numbered steps only.
- Do not repeat “Yes, No” or start with both.
- Keep under 100 words.
- Always sound like a human Zepto assistant, not a generic AI.
"""

def ask_ai_fallback(user_input):
    """🧠 3-layer Zepto AI fallback with realistic catalog simulation"""
    last_item = context_memory.get("last_item")
    last_category = context_memory.get("last_category")

    context_prompt = f"""
Recent context:
- Last item discussed: {last_item or 'None'}
- Last category: {last_category or 'None'}
Current user query: "{user_input}"
Use this context to give a relevant, natural reply.
"""

    full_prompt = f"{SYSTEM_PROMPT}\n{context_prompt}\n{INSTRUCTION_PROMPT}"

    try:
        response = client.chat_completion(
            model="meta-llama/Llama-3.2-1B-Instruct",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_input},
            ],
            max_tokens=200,
            temperature=0.45
        )
        # Updated to avoid double-wrapped content key differences
        content = response.choices[0].message["content"].strip()
        # ✅ Remove duplicate Yes/No if model produces both
        content = re.sub(r"^(Yes|No),?\s*(Yes|No),?", r"\1", content, flags=re.IGNORECASE)
        return content

    except Exception as e:
        print("AI fallback error:", e)
        return None

# ------------------ MAIN CHATBOT RESPONSE ------------------
def chatbot_response(user_input):
    user_input_clean = clean_text(user_input)

    greetings = ["hi", "hello", "hey", "hii", "hola"]
    if any(word in user_input_clean.split() for word in greetings):
        return "Hi 👋! Welcome to Zepto — how can I help you today?"

    # ✳️ Simplified intent detection
    intent_starters = ("can", "could", "shall", "should", "would", "do", "does", "did")

    if user_input_clean.startswith(intent_starters):
        item_ans = check_items(user_input_clean)
        if item_ans:
            if "doesn’t sell" in item_ans.lower() or "sorry" in item_ans.lower():
                return f"No, {item_ans}"
            else:
                return f"Yes, {item_ans}"

        ai_answer = ask_ai_fallback(user_input)
        if ai_answer:
            if any(word in ai_answer.lower() for word in ["not", "unavailable", "doesn’t sell", "sorry"]):
                return f"No, {ai_answer}"
            else:
                return f"Yes, {ai_answer}"

    # ✅ FAQ
    faq_ans = check_faq(user_input_clean)
    if faq_ans:
        return faq_ans

    # ✅ JSON Items
    item_ans = check_items(user_input_clean)
    if item_ans:
        return item_ans

    # ✅ Festival
    fest_ans = check_festivals(user_input_clean)
    if fest_ans:
        return fest_ans

    # ✅ Context-based follow-up
    followup_triggers = ("and", "it", "that", "them", "those", "also", "too", "how about", "what about")
    if user_input_clean.startswith(followup_triggers) and context_memory["last_category"]:
        for category, items in zepto_data["items"].items():
            for item, price in items.items():
                if item in user_input_clean:
                    update_context(item, category)
                    return f"{item.title()} is available under {category.title()} for ₹{price}."
        last_item = context_memory.get("last_item")
        last_cat = context_memory.get("last_category")
        if last_item and last_cat:
            return f"{last_item.title()} is available under {last_cat.title()} on Zepto."

    # ✅ AI fallback (Prompt-engineered)
    ai_answer = ask_ai_fallback(user_input)
    if ai_answer:
        return ai_answer

    save_unanswered(user_input)
    return "Sorry, I don’t have an answer for that yet — but I’ll learn soon!"

# ------------------ MAIN LOOP ------------------
if __name__ == "__main__":
    print("🧠 Zepto Chatbot (Prompt Engineering Edition) is ready! Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit", "bye", "stop"]:
            print("Chatbot: Bye! 👋 Have a great day!")
            break

        response = chatbot_response(user_input)
        print("Chatbot:", response)
