import streamlit as st
import os
import PyPDF2
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# Sentence embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

st.title("📄🤖 PDF Chatbot")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded_file:
    # Read PDF
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # Split into chunks
    def chunk_text(text, max_tokens=300):
        sentences = text.split(". ")
        chunks, current = [], ""
        for sentence in sentences:
            if len(current) + len(sentence) <= max_tokens:
                current += sentence + ". "
            else:
                chunks.append(current.strip())
                current = sentence + ". "
        if current:
            chunks.append(current.strip())
        return chunks

    chunks = chunk_text(text)

    # Embed and index with FAISS
    embeddings = embedder.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    st.success(f"PDF loaded with {len(chunks)} chunks.")

    # Store chunks in session state
    st.session_state.chunks = chunks
    st.session_state.index = index
    st.session_state.embeddings = embeddings
    
# Ask a question
if "chunks" in st.session_state:
    question = st.text_input("Ask a question about the PDF")
    if question:
        q_embedding = embedder.encode([question])
        D, I = st.session_state.index.search(np.array(q_embedding), k=5)

        context = "\n".join([st.session_state.chunks[i] for i in I[0]])

        prompt = f"""Use the context below to answer the question.
        Context: {context}
        Question: {question}
        """

        response = model.generate_content(prompt)
        st.markdown("**Answer:**")
        st.write(response.text)
