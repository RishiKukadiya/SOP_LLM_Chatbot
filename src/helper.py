import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import time

# ---------------- ENV SETUP ----------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

FAISS_PATH = "faiss_index_sop"

# ---------------- CACHE: EMBEDDINGS & LLM ----------------
@st.cache_resource(show_spinner=False)
def get_embeddings():
    """Cache OpenAI embeddings for fast reloads."""
    return OpenAIEmbeddings(model="text-embedding-3-large", api_key=API_KEY)

@st.cache_resource(show_spinner=False)
def get_llm():
    """Cache LLM instance to reuse same client for all calls."""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=API_KEY, max_tokens=600)

# ---------------- CACHE: VECTORSTORE ----------------
@st.cache_resource(show_spinner=False)
def load_vectorstore(data_path=None):
    """
    Load or build FAISS vectorstore.
    Uses caching for 3–5× faster reloads.
    """
    embeddings = get_embeddings()

    if os.path.exists(FAISS_PATH):
        try:
            vectorstore = FAISS.load_local(
                FAISS_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            return vectorstore
        except Exception as e:
            st.warning(f"⚠️ Failed to load FAISS index. Rebuilding... ({e})")

    if not data_path:
        raise ValueError("❌ No FAISS index or data path provided.")

    return build_vectorstore(data_path, embeddings)

def build_vectorstore(data_path, embeddings):
    """
    Build a FAISS vectorstore from .docx SOP files.
    Optimized to skip temporary files and provide feedback.
    """
    st.info("📂 Reading and processing SOP documents...")

    # 🔹 Efficient document collection
    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(data_path)
        for f in files
        if f.endswith(".docx") and not f.startswith("~$")
    ]

    if not all_files:
        raise FileNotFoundError("❌ No valid .docx files found in the folder.")

    documents = []
    skipped = 0
    for file_path in all_files:
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents.extend(loader.load())
        except Exception:
            skipped += 1
            print(f"⚠️ Skipped unreadable file: {file_path}")

    # 🔹 Split large docs into efficient chunks
    st.info("✂️ Splitting documents into text chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    split_docs = text_splitter.split_documents(documents)

    # 🔹 Create FAISS index
    st.info("🧠 Building FAISS vectorstore (this may take a few seconds)...")
    start = time.time()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(FAISS_PATH)
    end = time.time()

    st.success(f"✅ Vectorstore built successfully in {end - start:.2f} seconds.")
    if skipped:
        st.warning(f"⚠️ {skipped} files were skipped due to read issues.")

    return vectorstore

# ---------------- ASK QUESTION ----------------
def ask_question(question, vectorstore=None):
    """
    Ask question to the LLM using the SOP FAISS vectorstore.
    Uses cached LLM and embeddings for maximum speed.
    """
    if not question.strip():
        return "⚠️ Please enter a valid question."

    greetings = ["hi", "hie", "hello", "hey"]
    if question.lower().strip() in greetings:
        return "👋 Hello! How can I assist you with your company's SOPs today?"

    # 🔹 Ensure vectorstore is loaded
    if vectorstore is None:
        try:
            vectorstore = load_vectorstore()
        except Exception as e:
            return f"⚠️ Unable to load SOP data: {str(e)}"

    # 🔹 Retrieve most relevant context (faster top-3 results)
    try:
        results = vectorstore.similarity_search(question, k=3)
    except Exception as e:
        return f"⚠️ Error during vector search: {str(e)}"

    context = "\n\n".join([doc.page_content for doc in results])

    # 🔹 Reuse cached LLM
    llm = get_llm()

    # 🔹 Optimized prompt for low latency
    prompt = f"""
    You are a highly knowledgeable **Compliance & SOP Assistant** for Smartway Pharma.
    Answer based on the company's SOPs.

    🧩 **Rules:**
    1.summarize the sop data and gives a logically answer the questions.
    2. Use the SOP context below — no assumptions.
    3. If answer not in SOPs, reply: "Not found in current SOPs."
    4. Be concise (3–9 short factual sentences).
    5. Mention responsible team if relevant (e.g., Regulatory Team, RP, QA).
    6. Summarize logically, don’t copy paragraphs.
    7.when some wrong question ask to assistent so its give answer(e.g.,Any courier company can be used for export if they have valid insurance. (❌ Wrong – must be listed on R-OAR.))

    📘 **SOP Context:**
    {context}

    💬 **User Question:** {question}

    🎯 **Answer:**
    """

    try:
        response = llm.invoke([{"role": "user", "content": prompt}])
        # Fast extraction (works for all versions)
        if hasattr(response, "content"):
            return response.content.strip()
        elif isinstance(response, str):
            return response.strip()
        else:
            return str(response).strip()
    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"
