import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState

class OrchestratorOutput(BaseModel):
    query_intent: str = Field(description="Must be 'GENERAL', 'SCHEMA_LOOKUP', 'SQL_ONLY', 'RAG_ONLY', or 'HYBRID'")
    reasoning: str = Field(description="one sentence explaining why")

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data routing agent for a banking intelligence system.
Classify the user's question into exactly one of 5 intents.

Available data types:
1. STRUCTURED (SQL): Transaction records, payment events, API logs, system metrics, financial data.
2. UNSTRUCTURED (RAG): Customer reviews, complaint text, support ticket descriptions.
3. SCHEMA: Table names, column names, what data is available, what a table contains.
4. GENERAL: Greetings, explanations, definitions, questions about how the system works, anything not about data.

Intent rules — pick the FIRST one that matches:
- GENERAL: question is a greeting, a definition request, a "how does X work" question, or has nothing to do with banking data. No data access needed at all.
- SCHEMA_LOOKUP: user asks what tables exist, what columns a table has, what data is available, "do you have data about X", "what can you tell me about Y table". Needs table awareness but NO query execution. If a question asks BOTH about schema AND about actual data values, classify as SQL_ONLY.
- SQL_ONLY: needs exact numbers, aggregations, comparisons, trends, time-series from structured tables.
- RAG_ONLY: asks what customers said, sentiment, complaint themes, free text.
- HYBRID: needs both numerical data AND customer text together.

Prior conversation context:
{previous_query_block}
If the current question is a follow-up (uses "same", "that", "those", "also", "instead", "now show"), 
resolve what it refers to using the prior context before classifying.

Respond ONLY with JSON: {{"query_intent": "SQL_ONLY|RAG_ONLY|HYBRID|GENERAL|SCHEMA_LOOKUP", "reasoning": "one sentence"}}
"""),
    ("human", "User question: {user_query}")
])

def orchestrator_agent(state: PipelineState) -> dict:
    previous_query = state.get("previous_query", "")
    previous_answer = state.get("previous_answer", "")

    if previous_query:
        previous_query_block = (
            f"Previous user question: {previous_query}\n"
            f"Previous assistant answer (summary): {previous_answer[:300]}"
        )
    else:
        previous_query_block = "No prior conversation."

    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=OrchestratorOutput)
    chain = ORCHESTRATOR_PROMPT | llm | parser

    result = chain.invoke({
        "user_query": state["user_query"],
        "previous_query_block": previous_query_block
    })

    intent = result.get("query_intent", "HYBRID").upper()
    # Validate intent is one of the 5 allowed values
    valid_intents = {"SQL_ONLY", "RAG_ONLY", "HYBRID", "GENERAL", "SCHEMA_LOOKUP"}
    if intent not in valid_intents:
        intent = "HYBRID"
    reasoning = result.get("reasoning", "Failed to parse reasoning.")

    routing_decision = {
        "use_sql": intent in ["SQL_ONLY", "HYBRID"],
        "use_rag": intent in ["RAG_ONLY", "HYBRID"],
        "reasoning": reasoning
    }
    print(f"[DEBUG] ORCHESTRATOR AGENT → intent={intent}")
    return {
        "query_intent": intent,
        "routing_decision": routing_decision
    }
