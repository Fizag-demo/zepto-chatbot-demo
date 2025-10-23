import streamlit as st
import time
import os
import json
import pandas as pd
from datetime import datetime
from final_chatbot import chatbot_response

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Zepto Chatbot 🛒",
    page_icon="🛒",
    layout="centered"
)

# ------------------ ZEPTO STYLE ------------------
st.markdown("""
<style>
body { background-color: #F8F8F8; font-family: 'Helvetica', sans-serif; }
.title { text-align: center; font-size: 36px; font-weight: 700; color: #800080; margin-bottom: 10px; }
.subtitle { text-align: center; font-size: 18px; color: #666; margin-bottom: 25px; }
.chat-wrapper { background-color: #FFFFFF; border-radius: 12px; padding: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 700px; margin: auto; }
.message-row { display: flex; margin: 6px 0; }
.user-message { background-color: #FFFFFF; color: #000000; padding: 10px 14px; border-radius: 18px 18px 0 18px; border: 1px solid #E0E0E0; max-width: 70%; margin-left: auto; word-wrap: break-word; animation: fadeIn 0.25s ease-in; }
.bot-message { background-color: #800080; color: #FFFFFF; padding: 10px 14px; border-radius: 18px 18px 18px 0; max-width: 70%; margin-right: auto; word-wrap: break-word; animation: fadeIn 0.25s ease-in; }
@keyframes fadeIn { from {opacity: 0; transform: translateY(5px);} to {opacity: 1; transform: translateY(0);} }
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("<div class='title'>🛒 Zepto Chatbot</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your friendly grocery assistant — powered by AI</div>", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ LOGGING FUNCTIONS ------------------
def save_chat_to_json(user_msg, bot_msg):
    folder = "chat_logs"
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"{datetime.now().date()}_chatlog.json")

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_msg,
        "bot": bot_msg
    }

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: logs = json.load(f)
            except json.JSONDecodeError: logs = []
    else:
        logs = []

    logs.append(log_entry)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def save_chat_to_csv(user_msg, bot_msg):
    folder = "data"
    os.makedirs(folder, exist_ok=True)
    csv_file = os.path.join(folder, "chat_logs.csv")

    df = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": "anonymous",
        "user_message": user_msg,
        "bot_message": bot_msg
    }])

    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode="a", header=False, index=False)
    else:
        df.to_csv(csv_file, mode="w", header=True, index=False)

# ------------------ CHAT UI ------------------
chat_container = st.container()
with chat_container:
    st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='message-row'><div class='user-message'>🧑‍💻 {msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='message-row'><div class='bot-message'>🤖 {msg['content']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ CHAT INPUT ------------------
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Zepto Bot is typing..."):
        time.sleep(0.5)
        bot_reply = chatbot_response(user_input)

    st.session_state.messages.append({"role": "bot", "content": bot_reply})

    # Save logs to JSON and CSV
    save_chat_to_json(user_input, bot_reply)
    save_chat_to_csv(user_input, bot_reply)

    st.rerun()

# ------------------ ADMIN PANEL ------------------
st.sidebar.header("🔒 Admin / Dashboard")
mode = st.sidebar.radio("Choose view:", ["Chatbot", "Dashboard", "Admin Logs"])

if mode == "Dashboard":
    st.sidebar.success("📊 Dashboard view enabled")
    st.switch_page("pages/zepto_dashboard.py")

elif mode == "Admin Logs":
    st.sidebar.warning("Restricted access area")
    password = st.sidebar.text_input("Enter Admin Password:", type="password")
    if password == st.secrets.get("ADMIN_PASSWORD"):
        st.sidebar.success("Access granted ✅")
        st.subheader("🧾 Chat Logs (Admin Only)")
        folder = "chat_logs"
        if not os.path.exists(folder):
            st.info("No logs found yet.")
        else:
            files = sorted(os.listdir(folder), reverse=True)
            for file in files:
                st.write(f"📅 **{file}**")
                with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    for entry in logs:
                        st.markdown(f"""
                        **🕒 {entry['timestamp']}**
                        - 🧑‍💻 User: {entry['user']}
                        - 🤖 Bot: {entry['bot']}
                        """)
                st.markdown("---")
    else:
        if password:
            st.sidebar.error("Incorrect password ❌")
