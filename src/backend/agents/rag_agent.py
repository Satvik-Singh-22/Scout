"""
ELI5 (What does this file do?):
Think of this file as a super-fast researcher flipping through a giant filing cabinet of documents.
When someone asks a question about customer feedback or text documents, 
this agent dives into our special text database (ChromaDB), finds the 5 most relevant paragraphs 
matching the question, and hands them back to the team. 
If the question is purely about numbers (SQL_ONLY), it politely steps back and says "Not my department!"
"""
import logging
from backend.agents.state import PipelineState
from backend.vectorstore.chroma_manager import get_retriever

logger = logging.getLogger(__name__)

def rag_agent(state: PipelineState) -> dict:

    query = state.get("user_query", "")
    intent = state.get("query_intent", "")
    print("[DEBUG] RAG AGENT")
    # Skip RAG for SQL-only queries
    if intent == "SQL_ONLY":
        return {"rag_chunks": []}

    # Skip very short queries
    if not query or len(query) < 10:
        return {"rag_chunks": []}

    try:
        retriever = get_retriever()

        docs = retriever.invoke(query)

        chunks = [
            {
                "content": doc.page_content[:500],
                "source": doc.metadata.get("source"),
                "category": doc.metadata.get("category"),
                "date": doc.metadata.get("date")
            }
            for doc in docs
        ]
        
        return {"rag_chunks": chunks}

    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")
        return {"rag_chunks": []}