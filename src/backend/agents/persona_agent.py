from langchain_core.prompts import ChatPromptTemplate
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState

EXECUTIVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a business intelligence assistant for a non-technical banking EXECUTIVE.
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

TECHNICAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a technical data analyst assistant for a technical user.
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


def infer_chart_type(sql_results: list, query_intent: str) -> str:
    """
    Heuristic: pick the best chart type from the shape of the result rows.
    Falls back to TABLE when data is absent or intent doesn't produce SQL.
    """
    if not sql_results or query_intent in ("RAG_ONLY", "GENERAL", "SCHEMA_LOOKUP"):
        return "TABLE"

    row = sql_results[0]
    keys = list(row.keys())

    str_cols = [k for k in keys if isinstance(row[k], str)]
    num_cols = [k for k in keys if isinstance(row[k], (int, float))]

    if not str_cols or not num_cols:
        return "TABLE"

    # Time-series pattern: date/week/month/day column → LINE chart
    time_keywords = {"date", "week", "month", "day", "timestamp", "period", "hour", "year"}
    if any(k.lower() in time_keywords or any(kw in k.lower() for kw in time_keywords) for k in str_cols):
        return "LINE"

    # Small category breakdown (≤ 6 rows) → PIE
    if len(sql_results) <= 6:
        return "PIE"

    # Larger category breakdown → BAR
    return "BAR"


def build_chain_of_thought(state: PipelineState) -> dict:
    sql = state.get("generated_sql", "")
    sql_results = state.get("sql_results", [])
    query_intent = state.get("query_intent", "")

    return {
        "sources": state.get("relevant_tables", []),
        "sql_executed": sql if not sql.startswith("BLOCKED") else "",
        "sql_results": sql_results[:50],   # cap at 50 rows — enough for charts, not too heavy
        "rag_chunks_used": len(state.get("rag_chunks", [])),
        "agent_path": ["orchestrator", "relevancy", "sql_gen", "rag", "execution", "synthesis", "persona"],
        "query_intent": query_intent,
        "confidence": "high" if sql_results or state.get("rag_chunks") else "low",
        "tables_searched": state.get("relevant_tables", []),
        "tables_used": state.get("sql_tables_used", []),
        "teams_accessed": state.get("allowed_team_ids", []),
        "chart_type": infer_chart_type(sql_results, query_intent),
    }


def persona_agent(state: PipelineState) -> dict:
    persona = state.get("user_persona", "EXECUTIVE").upper()

    llm = get_llm(temperature=0.7)

    if persona == "TECHNICAL":
        chain = TECHNICAL_PROMPT | llm
        result = chain.invoke({
            "user_query": state.get("user_query"),
            "synthesized_context": state.get("synthesized_context"),
            "sql_executed": state.get("generated_sql", "None"),
            "tables_referenced": state.get("relevant_tables", [])
        })
    else:  # EXECUTIVE is default
        chain = EXECUTIVE_PROMPT | llm
        result = chain.invoke({
            "user_query": state.get("user_query"),
            "synthesized_context": state.get("synthesized_context")
        })

    cot = build_chain_of_thought(state)
    print("[DEBUG] PERSONA AGENT")
    return {"final_answer": result.content, "chain_of_thought": cot}
