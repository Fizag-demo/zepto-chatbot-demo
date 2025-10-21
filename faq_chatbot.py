import json

# Load data from JSON
with open("chat_data.json", "r") as file:
    faq_data = json.load(file)

def chatbot_response(user_input):
    user_input = user_input.lower().strip()

    # Check for exact match first
    if user_input in faq_data:
        return faq_data[user_input]
    
    # Try partial match (simple fuzzy logic)
    for question, answer in faq_data.items():
        if all(word in question for word in user_input.split()):
            return answer
    
    return "Sorry, I don’t have an answer for that yet — but I’ll learn soon!"

print("Chatbot is ready! Type 'exit' to stop.\n")

while True:
    user_prompt = input("You: ")
    if user_prompt.lower() == "exit":
        print("Chatbot: Bye! See you soon 👋")
        break
    response = chatbot_response(user_prompt)
    print("Chatbot:", response)
