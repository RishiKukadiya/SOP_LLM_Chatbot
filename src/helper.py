from langchain_community.document_loaders import DirectoryLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import streamlit as st
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

FAISS_PATH = "faiss_index_sop"

# ---------------- CACHE SETUP ----------------
@st.cache_resource
def get_embeddings():
    return OpenAIEmbeddings(model="text-embedding-3-large", api_key=API_KEY)

@st.cache_resource
def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=API_KEY, max_tokens=600)

@st.cache_resource
def load_vectorstore(data_path=None):
    """Load FAISS or create if missing"""
    embeddings = get_embeddings()
    if os.path.exists(FAISS_PATH):
        return FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    elif data_path:
        return build_vectorstore(data_path, embeddings)
    else:
        raise ValueError("No FAISS index or data path provided.")

def build_vectorstore(data_path, embeddings):
    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(data_path)
        for f in files
        if f.endswith(".docx") and not f.startswith("~$")
    ]
    documents = []
    for file_path in all_files:
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents.extend(loader.load())
        except:
            print(f"⚠️ Skipped {file_path}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)
    split_docs = text_splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(FAISS_PATH)
    return vectorstore

# ---------------- ASK QUESTION ----------------
def ask_question(question, vectorstore=None):
    if not question.strip():
        return "Please enter a valid question."

    greetings = ["hi", "hie", "hello", "hey"]
    if question.lower().strip() in greetings:
        return "Hello 👋! How can I help you with your company SOP today?"

    if vectorstore is None:
        vectorstore = load_vectorstore()

    results = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in results])

    llm = get_llm()
    prompt = f""" You are a highly knowledgeable **Compliance & SOP Assistant** for Smartway Pharma.
     You specialize in answering questions strictly based on the company's Standard Operating Procedures (SOPs).
      Follow these strict rules when answering: 
      
    1. Use ONLY the information found in the SOP context below.
    2. Do NOT use outside knowledge or make assumptions. 
    3. If the answer cannot be directly inferred from the SOP context, respond with the most relevant information available and note any uncertainty. If nothing is related, reply "Not found in current SOPs.
    4. Write your answer in a professional, clear, and factual tone suitable for audit or compliance reports. 
    5. Keep answers concise — 3 to 6 short, precise sentences. 
    6. If the question involves responsibilities or processes, clearly identify the team or role (e.g., "Regulatory Team", "Responsible Person (RP)", "Finance Team"). 
    7. Never quote entire SOP paragraphs — summarize only the relevant instruction or definition. 8. If multiple sections are relevant, merge them logically into one coherent response.
     --- 
     📘 **SOP Context:** {context} 
     💬 **User Question:** {question} --- 
     🎯 **Your Answer:** 
     """
    try:
        response = llm.invoke([{"role": "user", "content": prompt}])
        if hasattr(response, "content"):
            return response.content.strip()
        return str(response).strip()
    except Exception as e:
        return f"⚠️ Error generating answer: {str(e)}"
