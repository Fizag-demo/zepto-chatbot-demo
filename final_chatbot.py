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

# Create unanswered file if not exists
if not os.path.exists(UNANSWERED_FILE):
    with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ------------------ LOAD API KEY AND INITIALIZE LLAMA ------------------
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

client = InferenceClient(
    model="meta-llama/Llama-3.2-1B-Instruct",
    token=HUGGINGFACE_API_KEY
)

# ------------------ HELPER FUNCTIONS ------------------
def clean_text(text):
    """Normalize user input for matching."""
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def save_unanswered(question):
    """Save unanswered question to file."""
    with open(UNANSWERED_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    entry = {"question": question, "timestamp": datetime.now().isoformat()}
    data.append(entry)

    with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ------------------ CHECK FUNCTIONS ------------------
def check_faq(user_input):
    """Match user input with FAQ data."""
    questions = list(faq_data.keys())
    best_match, score, _ = process.extractOne(
        user_input, questions, scorer=fuzz.token_set_ratio
    )
    if score > 70:
        return faq_data[best_match]
    return None

def check_items(user_input):
    """Search for items and prices in Zepto data."""
    big_appliances = ["washing machine", "fridge", "television", "tv", "microwave", "ac", "refrigerator", "vacuum cleaner"]

    for appliance in big_appliances:
        if appliance in user_input:
            return f"Zepto doesn’t sell large appliances like {appliance}. It mainly offers groceries and small gadgets."

    # 🚫 Restricted non-grocery items
    restricted_keywords = ["shoes", "sandals", "slippers", "footwear"]
    for restricted in restricted_keywords:
        if restricted in user_input:
            return f"Zepto doesn’t sell {restricted}. It mainly offers groceries, snacks, and household essentials."

    # ✅ Regular product match
    for category, items in zepto_data["items"].items():
        for item, price in items.items():
            if item in user_input or fuzz.partial_ratio(item, user_input) > 75:
                return f"{item.title()} is available under {category.title()} for ₹{price}."

    return None

def check_festivals(user_input):
    """Check if question is about today's or upcoming festivals."""
    today = str(date.today())
    for fest, details in zepto_data["festivals"].items():
        if fest in user_input.lower() or details["date"] == today:
            return f"{details['wish']} 🎉 {details['offer']}"
    return None
# ------------------ AI FALLBACK USING LLAMA ------------------
def ask_ai_fallback(user_input):
    """Use LLaMA (Meta) model via Hugging Face for fallback answers."""
    try:
        response = client.chat_completion(
            model="meta-llama/Llama-3.2-1B-Instruct",
            messages=[
                {"role": "system", "content": "You are a helpful AI chatbot for Zepto customers. "
                                              "Answer politely and concisely about Zepto’s products, prices, offers, and delivery. "
                                              "If unsure, apologize briefly but try to be helpful."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7
        )

        return response.choices[0].message["content"].strip()

    except Exception as e:
        print("AI fallback error:", e)
        return None

# ------------------ MAIN RESPONSE FUNCTION ------------------
def chatbot_response(user_input):
    user_input_clean = clean_text(user_input)

    # 👋 Greeting handler
    greetings = ["hi", "hello", "hey", "hii", "hola"]
    if any(word in user_input_clean.split() for word in greetings):
        return "Hi 👋! Welcome to Zepto — how can I help you today?"

    # Check FAQ
    faq_ans = check_faq(user_input_clean)
    if faq_ans:
        return faq_ans

    # Check Zepto items
    item_ans = check_items(user_input_clean)
    if item_ans:
        return item_ans

    # Check Festival
    fest_ans = check_festivals(user_input_clean)
    if fest_ans:
        return fest_ans

    # If not found, use AI
    ai_answer = ask_ai_fallback(user_input)
    if ai_answer and len(ai_answer.strip()) > 0:
        return ai_answer

    # If still nothing, log it
    save_unanswered(user_input)
    return "Sorry, I don’t have an answer for that yet — but I’ll learn soon!"

# ------------------ MAIN LOOP ------------------
if __name__ == "__main__":
    print("🛒 Zepto Chatbot (LLaMA) is ready! Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit", "bye", "stop"]:
            print("Chatbot: Bye! 👋 Have a great day!")
            break

        response = chatbot_response(user_input)
        print("Chatbot:", response)
