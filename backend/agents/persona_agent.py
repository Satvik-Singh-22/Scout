from langchain_core.prompts import ChatPromptTemplate
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState

MANAGER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a business intelligence assistant for a non-technical banking manager.
Rules:
- Use plain English. No SQL. No technical jargon.
- Lead with the key finding in one sentence.
- Support with 2-3 bullet points of specific facts and numbers.
- End with one actionable implication.
- Keep total response under 200 words.
- If showing trends, describe them simply: "increased by X%" not "coefficient of variation".
"""),
    ("human", """Question: {user_query}

Data findings: {synthesized_context}

Write a clear, simple answer:""")
])

DEVELOPER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a technical data analyst assistant for a developer.
Rules:
- Lead with the direct answer.
- Include specific metrics, percentages, and exact values.
- Do not use any value that is not present in the data findings.
- Reference which tables and fields the data came from.
- If relevant, note data quality issues or edge cases observed.
- Use technical language appropriately.
- Format numbers precisely.
- If there is an error in the SQL query, explain the error in short and then provide a general response to user's question instead of the SQL query.
"""),
    ("human", """Question: {user_query}

Data findings: {synthesized_context}

SQL executed: {sql_executed}

Tables referenced: {tables_referenced}

Write a detailed technical answer:""")
])

def build_chain_of_thought(state: PipelineState) -> dict:
    return {
        "sources": state.get("relevant_tables", []),
        "sql_executed": state.get("generated_sql", "") if not state.get("generated_sql", "").startswith("BLOCKED") else "",
        "rag_chunks_used": len(state.get("rag_chunks", [])),
        "agent_path": ["orchestrator", "relevancy", "sql_gen", "rag", "execution", "synthesis", "persona"],
        "query_intent": state.get("query_intent", ""),
        "confidence": "high" if state.get("sql_results") or state.get("rag_chunks") else "low",
        "tables_searched": state.get("relevant_tables", []),
        "tables_used": state.get("sql_tables_used", []),
        "teams_accessed": state.get("allowed_team_ids", []),
    }

def persona_agent(state: PipelineState) -> dict:
    persona = state.get("user_persona", "MANAGER").upper()
    
    llm = get_llm(temperature=0.7)
    
    if persona == "DEVELOPER":
        chain = DEVELOPER_PROMPT | llm
        result = chain.invoke({
            "user_query": state.get("user_query"),
            "synthesized_context": state.get("synthesized_context"),
            "sql_executed": state.get("generated_sql", "None"),
            "tables_referenced": state.get("relevant_tables", [])
        })
    else:  # MANAGER is default
        chain = MANAGER_PROMPT | llm
        result = chain.invoke({
            "user_query": state.get("user_query"),
            "synthesized_context": state.get("synthesized_context")
        })

    cot = build_chain_of_thought(state)
    
    return {"final_answer": result.content, "chain_of_thought": cot}
