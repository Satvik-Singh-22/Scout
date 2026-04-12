"""
ELI5 (What does this file do?):
If normal databases store clear rows and columns of facts, our "Chroma manager" stores feelings and thoughts!
It runs our special Vector Database (ChromaDB), which holds text documents (like customer reviews) 
in a way that lets the AI search them by "meaning" rather than just exact keywords. 
This file gets that special database ready so our RAG agent can quickly fetch relevant paragraphs.
"""
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

_vectorstore = None
def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        _vectorstore = Chroma(
            collection_name="customer_reviews",
            embedding_function=embeddings,
            persist_directory=os.getenv(
                "CHROMA_PERSIST_PATH",
                "./chroma_data"
            )
        )
    return _vectorstore


def get_retriever():
    return get_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5}
    )