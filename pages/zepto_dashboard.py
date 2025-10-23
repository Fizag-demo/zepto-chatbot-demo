import streamlit as st
import pandas as pd
import os
from collections import Counter
from datetime import datetime

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="📊 Zepto Chatbot Analytics", layout="wide")

st.title("📊 Zepto Chatbot Analytics Dashboard")
st.caption("Monitor chatbot usage and user interaction trends")

# ------------------ LOAD CHAT LOGS ------------------
log_file = "data/chat_logs.csv"

if os.path.exists(log_file):
    df = pd.read_csv(log_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # ------------------ STATS ------------------
    st.subheader("🧑‍💻 Chat Summary")
    st.metric("Total Messages", len(df))
    st.metric("Unique Users", df["user_id"].nunique())

    # ------------------ CHATS PER DAY ------------------
    st.subheader("📅 Chats per Day")
    daily_counts = df.groupby(df["timestamp"].dt.strftime("%b %d"))["user_message"].count()
    st.bar_chart(daily_counts)

    # ------------------ FREQUENT QUERIES ------------------
    st.subheader("💬 Most Frequent User Queries")
    all_words = " ".join(df["user_message"].dropna()).lower().split()
    common_words = Counter(all_words).most_common(10)
    st.bar_chart(pd.DataFrame(common_words, columns=["Word", "Count"]).set_index("Word"))

    # ------------------ USER ACTIVITY ------------------
    st.subheader("📈 Last 20 User Messages")
    st.dataframe(df.tail(20))
else:
    st.warning("No chat logs found yet. Start chatting to generate analytics!")
