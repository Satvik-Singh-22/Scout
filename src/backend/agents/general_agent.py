"""
ELI5 (What does this file do?):
Think of this file as the friendly chatbot that handles small talk and general knowledge.
If a user says "Hello!", or asks "What does an API mean?", or "What can you do for me?", 
they don't need us to dig through complex company databases. 
This agent steps in, gives a helpful, direct, and conversational answer right away, 
skipping the heavy data-crunching steps entirely to save time.
"""
from langchain_core.prompts import ChatPromptTemplate
from backend.agents.state import PipelineState
from backend.agents.llm import get_llm

GENERAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an enterprise banking intelligence assistant.
Answer the user's question directly and helpfully.
You have access to banking data through natural language queries, but this particular question doesn't need data access.

Rules:
- Be concise and direct.
- If asked what you can do, explain your capabilities: natural language queries on banking data, scheduled reports, anomaly alerts, cross-team data access.
- If asked a banking/finance definition, answer accurately.
- Do not make up data or statistics.
- Keep responses under 150 words unless a detailed explanation is genuinely needed.

Prior conversation context:
{previous_context_block}
If the question refers to something from the prior exchange, use that context to answer correctly.
"""),
    ("human", "{user_query}")
])

def general_agent(state: PipelineState) -> dict:
    print("[DEBUG] GENERAL AGENT")

    previous_query = state.get("previous_query", "")
    previous_answer = state.get("previous_answer", "")

    if previous_query:
        previous_context_block = (
            f"Previous question: {previous_query}\n"
            f"Previous answer: {previous_answer[:300]}"
        )
    else:
        previous_context_block = "No prior conversation."

    chain = GENERAL_PROMPT | get_llm()
    response = chain.invoke({
        "user_query": state["user_query"],
        "previous_context_block": previous_context_block
    })

    final_answer = response.content.strip()
    print("[DEBUG] GENERAL AGENT")

    chain_of_thought = {
        "sources": [],
        "sql_executed": "",
        "sql_results": [],
        "rag_chunks_used": 0,
        "agent_path": ["orchestrator", "general"],
        "query_intent": "GENERAL",
        "confidence": "high",
        "tables_searched": [],
        "tables_used": [],
        "teams_accessed": state.get("allowed_team_ids", []),
        "chart_type": "TABLE"
    }

    return {
        "final_answer": final_answer,
        "chain_of_thought": chain_of_thought
    }
