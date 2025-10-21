import streamlit as st
from final_chatbot import chatbot_response  # import your chatbot brain

# ---- Page Configuration ----
st.set_page_config(page_title="Zepto Chatbot", page_icon="🛒", layout="centered")

st.title("🛒 Zepto Chatbot")
st.caption("Your friendly grocery assistant — powered by AI & custom data")

# ---- Chat UI ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User Input Box
user_input = st.text_input("Type your question:", placeholder="Ask me about Zepto offers, prices, or delivery...")

if st.button("Send") and user_input.strip():
    # Get chatbot response
    response = chatbot_response(user_input)
    # Store chat history
    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Chatbot", response))

# ---- Display Chat ----
for speaker, message in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(f"**🧑‍💻 {speaker}:** {message}")
    else:
        st.markdown(f"**🤖 {speaker}:** {message}")
