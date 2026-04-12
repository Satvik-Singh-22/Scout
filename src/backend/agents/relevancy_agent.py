import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from sqlalchemy import text
from backend.agents.state import PipelineState
from backend.db.session import get_sync_session

class RelevancyOutput(BaseModel):
    tables: list[str] = Field(description="list of relevant table names")
    reasoning: str = Field(description="one sentence reasoning")

RELEVANCY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data architect for a banking system.
Given a user's question and a list of available tables with their descriptions,
identify which tables are needed to answer the question.
Select ONLY the tables genuinely needed to answer the question. 
Err on the side of fewer tables — 1-2 is usually correct.
Do NOT select a table just because it sounds related.

Examples:
- "transaction failure rate" → mock_transactions only (not mock_payment_events)
- "API error spike" → mock_api_gateway_logs only
- "customer complaints about payments" → mock_customer_feedback + mock_transactions

Return ONLY a JSON object: {{"tables": ["table1", "table2"], "reasoning": "one sentence"}}
Max 3 tables unless the question genuinely requires more.
Available tables:
{available_tables}
"""),
    ("human", "User question: {user_query}")
])

def relevancy_agent(state: PipelineState) -> dict:
    if state["query_intent"] == "RAG_ONLY":
        return {"relevant_tables": []}
    
    # Query database for available tables based on allowed_team_ids
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        # Fallback if allowed_team_ids is somehow not set but team_id is
        team_ids = [state["team_id"]]
        
    available_tables_str = ""
    try:
        with get_sync_session() as session:
            # Query the master config table
            query = text("SELECT table_name, semantic_definition FROM master_config WHERE team_id IN :team_ids AND is_active = TRUE")
            result = session.execute(query, {"team_ids": tuple(team_ids)})
            rows = result.fetchall()
            for row in rows:
                available_tables_str += f"{row.table_name}: {row.semantic_definition}\n"
    except Exception as e:
        print(f"Error fetching configured tables: {e}")
        return {"relevant_tables": []}
        
    if not available_tables_str.strip():
        return {"relevant_tables": []}

    # Build a previous-tables hint — strong prior for follow-up questions
    previous_hint = ""
    if state.get("previous_tables_used"):
        previous_hint = (
            f"\nNote: The previous question used these tables: "
            f"{', '.join(state['previous_tables_used'])}. "
            f"Prefer these if the current question is a follow-up."
        )

    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=RelevancyOutput)
    chain = RELEVANCY_PROMPT | llm | parser
    print("[DEBUG] RELEVANCY AGENT")
    result = chain.invoke({
        "available_tables": available_tables_str + previous_hint,
        "user_query": state["user_query"]
    })
    
    tables = result.get("tables", [])
    return {"relevant_tables": tables}
