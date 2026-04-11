import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState

class OrchestratorOutput(BaseModel):
    query_intent: str = Field(description="Must be 'SQL_ONLY', 'RAG_ONLY', or 'HYBRID'")
    reasoning: str = Field(description="one sentence explaining why")

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data routing agent for a banking intelligence system.
You decide how to answer a user's question based on available data types.

Available data types:
1. STRUCTURED (SQL): Transaction records, payment events, API logs, system metrics, financial data, branch performance — anything with numbers, dates, counts, regions, amounts.
2. UNSTRUCTURED (RAG): Customer reviews, complaint text, support ticket descriptions — free text expressing opinions or issues.

Respond ONLY with a JSON object. No explanation outside the JSON.
Format: {{"query_intent": "SQL_ONLY|RAG_ONLY|HYBRID", "reasoning": "one sentence"}}

Rules:
- SQL_ONLY: question needs exact numbers, aggregations, comparisons, trends, time-series
- RAG_ONLY: question asks what customers said, customer sentiment, complaint themes
- HYBRID: question needs both numerical data AND customer text context together
"""),
    ("human", "User question: {user_query}")
])

def orchestrator_agent(state: PipelineState) -> dict:
    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=OrchestratorOutput)
    chain = ORCHESTRATOR_PROMPT | llm | parser

    result = chain.invoke({"user_query": state["user_query"]})
    
    intent = result.get("query_intent", "HYBRID").upper()
    reasoning = result.get("reasoning", "Failed to parse reasoning.")
    
    routing_decision = {
        "use_sql": intent in ["SQL_ONLY", "HYBRID"],
        "use_rag": intent in ["RAG_ONLY", "HYBRID"],
        "reasoning": reasoning
    }
    print("[DEBUG] ORCHESTRATOR AGENT")
    return {
        "query_intent": intent,
        "routing_decision": routing_decision
    }
