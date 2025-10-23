import streamlit as st
import time
from final_chatbot import chatbot_response  # Import your chatbot logic

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Zepto Chatbot 🛒",
    page_icon="🛒",
    layout="centered"
)

# ------------------ CUSTOM STYLING ------------------
st.markdown("""
    <style>
        body {
            background-color: #faf7ff;
        }
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: 700;
            color: #7B2CBF;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #666;
            margin-bottom: 25px;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
        .user-bubble {
            background-color: #7B2CBF;
            color: white;
            padding: 10px 15px;
            border-radius: 18px;
            margin: 6px 0;
            width: fit-content;
            max-width: 75%;
            align-self: flex-end;
        }
        .bot-bubble {
            background-color: #EDE7F6;
            color: #000;
            padding: 10px 15px;
            border-radius: 18px;
            margin: 6px 0;
            width: fit-content;
            max-width: 75%;
            align-self: flex-start;
        }
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("<div class='title'>🛒 Zepto Chatbot</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your friendly grocery assistant — powered by AI</div>", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ DISPLAY CHAT HISTORY ------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-container'><div class='user-bubble'>🧑‍💻 {msg['content']}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-container'><div class='bot-bubble'>🤖 {msg['content']}</div></div>", unsafe_allow_html=True)

# ------------------ USER INPUT ------------------
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate chatbot response
    with st.spinner("Zepto Bot is thinking..."):
        bot_reply = chatbot_response(user_input)
        time.sleep(0.4)

    # Add bot response
    st.session_state.messages.append({"role": "bot", "content": bot_reply})
    st.rerun()
