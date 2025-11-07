import streamlit as st
from src.db_helper import validate_user

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Login - SOP Chatbot", page_icon="🔐", layout="centered")

# ---------------- HIDE SIDEBAR & FOOTER ----------------
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], footer, header {display: none;}
    </style>
""", unsafe_allow_html=True)

# ---------------- RESTORE LOGIN FROM QUERY PARAMS ----------------
params = st.query_params
if params.get("logged_in") == "true":
    st.session_state.logged_in = True
    st.session_state.user_email = params.get("email", "Unknown")

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ---------------- REDIRECT IF ALREADY LOGGED IN ----------------
if st.session_state.logged_in:
    st.switch_page("pages/app.py")

# ---------------- LOGIN UI ----------------
st.title("🔐 Secure Login Portal")
st.caption("Access your company SOP chatbot below.")
st.markdown("---")

email = st.text_input("📧 Company Email*")
password = st.text_input("🔑 Password*", type="password")

if st.button("Login"):
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        with st.spinner("🔍 Verifying your credentials..."):
            if validate_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email

                # ✅ Save login info to query params (persistent across pages)
                st.query_params["email"] = email
                st.query_params["logged_in"] = "true"

                st.success("✅ Login successful! Redirecting...")
                st.switch_page("pages/app.py")
            else:
                st.error("❌ Invalid email or password. Please try again.")
