import json
import re
from rapidfuzz import process, fuzz

# Load JSON file
with open("chat_data.json", "r", encoding="utf-8") as file:
    faq_data = json.load(file)

def clean_text(text):
    """Lowercase and remove punctuation"""
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def chatbot_response(user_input):
    user_input_clean = clean_text(user_input)
    questions = list(faq_data.keys())

    # Use fuzzy matching to find the closest question
    best_match, score, _ = process.extractOne(
        user_input_clean, 
        questions, 
        scorer=fuzz.token_set_ratio
    )

    # Debug (optional): print the match score
    # print(f"Matched '{best_match}' with score {score}")

    # Lower the threshold so it's more forgiving for user phrasing
    if score > 45:  # was 60 earlier
        return faq_data[best_match]
    else:
        return "Sorry, I don't have an answer for that yet — but I'll learn soon!"

print("Chatbot is ready! Type 'exit' to stop.\n")

while True:
    user_prompt = input("You: ").strip()
    if user_prompt.lower() in ["exit", "quit", "bye", "stop"]:
        print("Chatbot: Bye! See you soon 👋")
        break

    response = chatbot_response(user_prompt)
    print("Chatbot:", response)
