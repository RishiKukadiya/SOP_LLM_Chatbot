# -------------------------------------------------------------
# 💬 Company SOP Chatbot (Auto Load on Path Enter)
# Author: Rishi Kukdiya
# -------------------------------------------------------------

import streamlit as st
from src.helper import load_documents, docs_splitting, docs_embed, ask_question, load_vectorstore
import os

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="💬 Company SOP Chatbot", page_icon="🤖", layout="centered")

# ---------------- HEADER ----------------
st.title("📘 Company SOP Chatbot")
st.caption("Ask any question about your company SOPs....")

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ SOP Data Source")
st.sidebar.markdown("---")

# Text input for SOP folder path
data_path = st.sidebar.text_input(
    "📂 Enter your SOP folder path:",
    placeholder="Add your folder path here (e.g. Z:\\SOP_DATA)",
)

vectorstore_path = "faiss_index_sop"

# Clear chat button
st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = []
    st.sidebar.success("Chat history cleared!")

st.sidebar.markdown("---")
st.sidebar.info("💡 The chatbot automatically loads data when you enter the folder path and press Enter.")

# ---------------- SESSION STATE ----------------
if "vectorstore_loaded" not in st.session_state:
    st.session_state.vectorstore_loaded = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "loaded_path" not in st.session_state:
    st.session_state.loaded_path = None

# ---------------- AUTO LOAD WHEN PATH ENTERED ----------------
if data_path and data_path != st.session_state.loaded_path:
    with st.spinner("⚙️ Loading SOP knowledge base..."):
        try:
            # Step 1: Load documents from the given folder
            docs = load_documents()
            st.write(f"✅ Loaded {len(docs)} documents from **{data_path}**.")

            # Step 2: Split and embed
            split_docs = docs_splitting(docs)
            st.write(f"✅ Created {len(split_docs)} document chunks.")
            docs_embed(split_docs)

            # Step 3: Mark as loaded
            st.session_state.vectorstore_loaded = True
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
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user's message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate bot response
    with st.chat_message("assistant"):
        if not st.session_state.vectorstore_loaded:
            response = "⚠️ Please enter a valid SOP folder path to load data first."
            st.error(response)
        else:
            with st.spinner("🤖 Thinking... fetching relevant SOP context..."):
                try:
                    response = ask_question(prompt)
                    response = response.strip() if response else "⚠️ No response generated."
                    st.markdown(response)
                except Exception as e:
                    response = f"❌ Error generating answer: {e}"
                    st.error(response)

    # Save bot response
    st.session_state.messages.append({"role": "assistant", "content": response})
