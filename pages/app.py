import streamlit as st
from src.helper import load_vectorstore, ask_question
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="💬 Company SOP Chatbot", page_icon="🤖", layout="centered")

# ---------------- RESTORE SESSION FROM QUERY PARAMS ----------------
params = st.query_params
if params.get("logged_in") == "true":
    st.session_state.logged_in = True
    st.session_state.user_email = params.get("email", "Unknown")

# ---------------- REDIRECT TO LOGIN IF NOT LOGGED IN ----------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("login.py")

# ---------------- STYLE CLEANUP ----------------
st.markdown("""
    <style>
    [data-testid="stSidebarNav"], footer, header {display: none;}
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
user_email = st.session_state.get("user_email", "User")
st.title("📘 Company SOP Chatbot")
st.caption(f"Welcome, **{user_email}** 👋 — Ask any question about your company SOPs below.")

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ SOP Data Source")
st.sidebar.markdown("---")

data_path = st.sidebar.text_input(
    "📂 Enter your SOP folder path:",
    placeholder="Add your folder path here (e.g. Z:\\SOP_DATA)",
)

# 🚪 Logout Button
if st.sidebar.button("🚪 Logout"):
    # ✅ Clear session and query params
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.query_params.clear()  # <-- New replacement for st.experimental_set_query_params()
    st.success("✅ Logged out successfully! Redirecting...")
    st.switch_page("login.py")

# ---------------- SESSION STATE ----------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "loaded_path" not in st.session_state:
    st.session_state.loaded_path = None

# ---------------- LOAD VECTORSTORE ----------------
if data_path and (st.session_state.vectorstore is None or st.session_state.loaded_path != data_path):
    with st.spinner("⚙️ Loading SOP knowledge base..."):
        try:
            st.session_state.vectorstore = load_vectorstore(data_path)
            st.session_state.loaded_path = data_path
            st.sidebar.success("🎉 SOP data loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading documents: {e}")

# ---------------- DISPLAY CHAT HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- CHAT INPUT ----------------
prompt = st.chat_input("Ask a question about your company SOP...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("🤖 Generating answer..."):
            response = ask_question(prompt, st.session_state.vectorstore)
            placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
