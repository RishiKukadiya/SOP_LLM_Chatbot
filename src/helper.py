# -------------------------------------------------------------
# 💬 SOP Chatbot Helper (Production-Ready Version)
# Author: Rishi Kukadiya
# -------------------------------------------------------------

from langchain_community.document_loaders import DirectoryLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os



# ---------------- CONFIG ----------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
DATA_PATH = r"Z:\SOP_DATA"
FAISS_PATH = "faiss_index_sop"

# ---------------- LOAD DOCUMENTS ----------------
def load_documents(data_path=DATA_PATH):
    print("🧠 Building SOP Chatbot Knowledge Base...")

    # Get all .docx files except temp (~$) ones
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
            docs = loader.load()
            documents.extend(docs)
        except Exception as e:
            # Skip invalid or corrupted Word files silently
            print(f"⚠️ Skipped: {os.path.basename(file_path)}")

    print(f"✅ Loaded {len(documents)} valid SOP documents.")
    return documents

# ---------------- SPLIT DOCUMENTS ----------------
def docs_splitting(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=500,
        separators=["\n\n", "\n", ".", " "],
    )
    split_docs = text_splitter.split_documents(documents)
    print(f"✅ Total chunks created: {len(split_docs)}")
    return split_docs

# # ---------------- CREATE VECTOR STORE ----------------
def docs_embed(split_docs):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=API_KEY)
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(FAISS_PATH)
    print("✅ Vector store created and saved successfully!")
    return vectorstore

# # ---------------- LOAD OR CREATE VECTOR STORE ----------------
def load_vectorstore():
    if not os.path.exists(FAISS_PATH):
        print("⚠️ No FAISS index found. Creating it now...")
        documents = load_documents()
        split_docs = docs_splitting(documents)
        return docs_embed(split_docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=API_KEY)
    vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    print("✅ FAISS vectorstore loaded successfully!")
    return vectorstore


# # ---------------- QUESTION HANDLER ----------------
def ask_question(question):
    # Handle greetings or empty input
    greetings = ["hi", "hie", "hello", "hey"]
    if question.lower().strip() in greetings:
        return "Hello! 👋 How can I help you with the company SOP today?"

    if not question.strip():
        return "Please enter a valid question."

    try:
        # Load vectorstore
        vectorstore = load_vectorstore()

        results = vectorstore.similarity_search(question, k=3)
        context = "\n\n".join([doc.page_content for doc in results])


        prompt = f"""
You are a highly knowledgeable **Compliance & SOP Assistant** for Smartway Pharma.
You specialize in answering questions strictly based on the company's Standard Operating Procedures (SOPs).

Follow these strict rules when answering:

1. Use ONLY the information found in the SOP context below.  
2. Do NOT use outside knowledge or make assumptions.  
3. If the answer cannot be directly inferred from the SOP context,
respond with the most relevant information available and note any uncertainty.
If nothing is related, reply "Not found in current SOPs.
4. Write your answer in a professional, clear, and factual tone suitable for audit or compliance reports.  
5. Keep answers concise — 3 to 6 short, precise sentences.  
6. If the question involves responsibilities or processes, clearly identify the team or role (e.g., "Regulatory Team", "Responsible Person (RP)", "Finance Team").  
7. Never quote entire SOP paragraphs — summarize only the relevant instruction or definition.  
8. If multiple sections are relevant, merge them logically into one coherent response.

---

📘 **SOP Context:**
{context}

💬 **User Question:**
{question}

---

🎯 **Your Answer:**
"""

        # Generate response
        llm = ChatOpenAI(model="gpt-4o-mini",temperature=0.1,api_key=API_KEY,max_tokens=600)

        messages = [
    {"role": "system", "content": "You are a compliance-focused SOP expert. Follow internal reasoning but output only the final factual answer."},
    {"role": "user", "content": prompt}
]

        response = llm.invoke(messages)
        # Extract response text
        if hasattr(response, "content"):
            answer = response.content.strip()
        elif isinstance(response, str):
            answer = response.strip()
        elif hasattr(response, "text"):
            answer = response.text.strip()
        else:
            answer = str(response).strip()

        # Limit overly long answers
        if len(answer.split()) > 120:
            answer = " ".join(answer.split()[:100]) + "..."

        return answer

    except Exception as e:
        return f"❌ Error generating answer: {str(e)}"


# ---------------- MAIN EXECUTION ----------------
# if __name__ == "__main__":
#     print("🧠 Building SOP Chatbot Knowledge Base...")
#     documents = load_documents()
#     split_docs = docs_splitting(documents)
#     docs_embed(split_docs)
#     print("✅ Setup complete. You can now chat with your SOP Bot!")
