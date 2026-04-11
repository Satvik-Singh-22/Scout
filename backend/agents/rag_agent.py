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