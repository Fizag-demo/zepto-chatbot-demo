import json
import re
from rapidfuzz import process, fuzz
from datetime import datetime, date
import os
from transformers import pipeline

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

# ------------------ AI FALLBACK MODEL ------------------
ai_model = pipeline("text2text-generation", model="google/flan-t5-base")

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
    big_appliances = ["washing machine", "fridge", "television", "tv", "microwave", "ac", "refrigerator"]

    # Reject big appliances
    for appliance in big_appliances:
        if appliance in user_input:
            return f"Zepto doesn’t sell large appliances like {appliance}. It mainly offers groceries and small gadgets."

    for category, items in zepto_data["items"].items():
        for item, price in items.items():
            if item in user_input:
                return f"{item.title()} is available under {category.title()} for ₹{price}."
    return None

def check_festivals(user_input):
    """Check if question is about today's or upcoming festivals."""
    today = str(date.today())
    for fest, details in zepto_data["festivals"].items():
        if fest in user_input.lower() or details["date"] == today:
            return f"{details['wish']} 🎉 {details['offer']}"
    return None

def ask_ai_fallback(user_input):
    """Use HuggingFace Transformers if JSON doesn’t have an answer."""
    prompt = (
        "You are a helpful AI chatbot for Zepto customers. "
        "If the question is about product price, delivery, offers, or Zepto service, "
        "respond politely with an informative short answer. "
        "If unsure, say you are not sure but try your best.\n\n"
        f"User: {user_input}\nChatbot:"
    )

    response = ai_model(
        prompt,
        max_new_tokens=150,
        num_return_sequences=1,
        temperature=0.7
    )

    return response[0]["generated_text"].strip()

# ------------------ MAIN RESPONSE FUNCTION ------------------
def chatbot_response(user_input):
    user_input_clean = clean_text(user_input)

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
# ------------------ MAIN LOOP ------------------
if __name__ == "__main__":
    print("🛒 Zepto Chatbot is ready! Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit", "bye", "stop"]:
            print("Chatbot: Bye! 👋 Have a great day!")
            break

        response = chatbot_response(user_input)
        print("Chatbot:", response)
