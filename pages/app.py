import sys
import os
import time
import streamlit as st
from dotenv import load_dotenv
from src.helper import load_vectorstore, ask_question

# ---------------- CONFIG ----------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
st.set_page_config(page_title="💬 Company SOP Chatbot", page_icon="🤖", layout="centered")
load_dotenv()

# ---------------- RESTORE LOGIN STATE ----------------
params = st.query_params

def _as_str(value, default=""):
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default

logged_in_param = _as_str(params.get("logged_in"))
email_param = _as_str(params.get("email"), "Unknown")

if logged_in_param.lower() == "true" and not st.session_state.get("logged_in"):
    st.session_state.logged_in = True
    st.session_state.user_email = email_param

if not st.session_state.get("logged_in"):
    st.switch_page("login.py")

# ---------------- STYLE ----------------
st.markdown("""
    <style>
    [data-testid="stSidebar"], footer, header {display: none;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    body, main {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlock"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }

    /* Chat message layout with avatar */
    .message {
        display: flex;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    .avatar {
        font-size: 1.4rem;
        margin-right: 10px;
        user-select: none;
    }
    .message.user {
        flex-direction: row-reverse;
        text-align: right;
    }
    .message.user .avatar {
        margin-left: 10px;
        margin-right: 0;
    }

    /* Chat bubbles */
    .chat-bubble-user {
        background-color: #DCF8C6;
        border-radius: 15px;
        padding: 10px 15px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        max-width: 80%;
        display: inline-block;
        word-wrap: break-word;
    }
    .chat-bubble-bot {
        background-color: #F1F0F0;
        border-radius: 15px;
        padding: 10px 15px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        max-width: 80%;
        display: inline-block;
        word-wrap: break-word;
    }

    /* Typing animation */
    .typing-dots {
        display: inline-block;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0% {opacity: 0.2;}
        50% {opacity: 1;}
        100% {opacity: 0.2;}
    }

    /* Header and logout */
    h2 {
        margin-top: 1rem !important;
        margin-bottom: 0.2rem !important;
        text-align: center !important;
    }
    p {
        margin-top: 0 !important;
        margin-bottom: 0.3rem !important;
        text-align: center !important;
    }
    div[data-testid="stVerticalBlock"] button[kind="secondary"] {
        display: block;
        margin: 0.5rem auto 0rem auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
user_email = st.session_state.get("user_email", "User")
user_name = user_email.split("@")[0].capitalize()

st.markdown(f"<h2>💬 Company SOP Chatbot</h2>", unsafe_allow_html=True)
st.markdown(f"<p>Welcome, <b>{user_name}</b> 👋 — Ask any question about your company SOPs.</p>", unsafe_allow_html=True)

# ---------------- LOGOUT ----------------
st.markdown("<div style='text-align:center; margin-bottom:0;'>", unsafe_allow_html=True)
if st.button("🚪 Logout", key="logout", use_container_width=False):
    st.session_state.clear()
    st.query_params.clear()
    st.success("✅ Logged out successfully! Redirecting...")
    st.switch_page("login.py")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- LOAD DEFAULT SOP DATA ----------------
DEFAULT_SOP_PATH = os.getenv("SOP_PATH", "Z:\\SOP_DATA")

st.session_state.setdefault("vectorstore", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("loaded_path", None)
st.session_state.setdefault("greeted", False)

if st.session_state.vectorstore is None or st.session_state.loaded_path != DEFAULT_SOP_PATH:
    try:
        st.session_state.vectorstore = load_vectorstore(DEFAULT_SOP_PATH)
        st.session_state.loaded_path = DEFAULT_SOP_PATH
    except Exception as e:
        st.error(f"❌ Error loading documents: {e}")

# ---------------- CHAT CONTAINER ----------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# ✅ Animated greeting (assistant)
if not st.session_state.greeted:
    greeting_message = f"👋 Hi {user_name}, how can I assist you today?"
    placeholder = st.empty()
    displayed_text = ""
    for char in greeting_message:
        displayed_text += char
        placeholder.markdown(
            f"<div class='message bot'><div class='avatar'>🤖</div><div class='chat-bubble-bot'>{displayed_text}</div></div>",
            unsafe_allow_html=True
        )
        time.sleep(0.03)
    st.session_state.messages.append({"role": "assistant", "content": greeting_message})
    st.session_state.greeted = True
else:
    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"<div class='message user'><div class='avatar'>🧑‍💼</div><div class='chat-bubble-user'>{msg['content']}</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='message bot'><div class='avatar'>🤖</div><div class='chat-bubble-bot'>{msg['content']}</div></div>",
                unsafe_allow_html=True
            )

# ---------------- CHAT INPUT ----------------
prompt = st.chat_input("Type your question here...")

if prompt:
    # Show user message instantly
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(
        f"<div class='message user'><div class='avatar'>🧑‍💼</div><div class='chat-bubble-user'>{prompt}</div></div>",
        unsafe_allow_html=True
    )

    # Typing indicator (no spinner)
    typing_placeholder = st.empty()
    typing_placeholder.markdown(
        "<div class='message bot'><div class='avatar'>🤖</div><div class='chat-bubble-bot'><span class='typing-dots'>Typing...</span></div></div>",
        unsafe_allow_html=True,
    )

    # Generate assistant response (no st.spinner)
    try:
        response = ask_question(prompt, st.session_state.vectorstore)
    except Exception as e:
        response = f"❌ Error processing your question: {e}"

    # Replace typing with animated reply
    typing_placeholder.empty()
    animated_placeholder = st.empty()
    displayed_text = ""
    for char in response:
        displayed_text += char
        animated_placeholder.markdown(
            f"<div class='message bot'><div class='avatar'>🤖</div><div class='chat-bubble-bot'>{displayed_text}</div></div>",
            unsafe_allow_html=True
        )
        time.sleep(0.01)

    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("</div>", unsafe_allow_html=True)
