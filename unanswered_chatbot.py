import json
import re
from rapidfuzz import process, fuzz
from datetime import datetime
import os

# Load FAQ data
with open("chat_data.json", "r", encoding="utf-8") as file:
    faq_data = json.load(file)

UNANSWERED_FILE = "unanswered.json"

def clean_text(text):
    """Normalize text for better matching."""
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def save_unanswered(question):
    """Save unknown questions for future learning."""
    data = []
    if os.path.exists(UNANSWERED_FILE):
        with open(UNANSWERED_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    entry = {"question": question, "timestamp": datetime.now().isoformat()}
    data.append(entry)

    with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def chatbot_response(user_input):
    """Get chatbot answer using fuzzy matching."""
    user_input_clean = clean_text(user_input)
    questions = list(faq_data.keys())

    # Find best fuzzy match
    best_match, score, _ = process.extractOne(
        user_input_clean, questions, scorer=fuzz.token_set_ratio
    )

    # Debug info
    print(f"[DEBUG] Matched '{best_match}' with score: {score}")

    # If a confident match is found, return the answer
    if score > 70:  # Increased threshold to make it stricter
        return faq_data[best_match]
    else:
        save_unanswered(user_input)
        print(f"[INFO] Logged unanswered question: {user_input}")
        return "Sorry, I don’t have an answer for that yet — but I’ll learn soon!"

# ---------- MAIN CHAT LOOP ----------
print("Chatbot is ready! Type 'exit' to stop.\n")

while True:
    user_prompt = input("You: ").strip()
    if user_prompt.lower() in ["exit", "quit", "bye", "stop"]:
        print("Chatbot: Bye! See you soon 👋")
        break

    response = chatbot_response(user_prompt)
    print("Chatbot:", response)
