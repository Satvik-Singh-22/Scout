from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from sqlalchemy import text
from backend.agents.state import PipelineState
from backend.db.session import get_sync_session
from langchain_core.prompts import ChatPromptTemplate
import json

class SQLGenOutput(BaseModel):
    sql: str = Field(description="The generated PostgreSQL SELECT query")
    tables_used: list[str] = Field(description="List of table names actually referenced in the SQL")

def parse_sql_output(raw: str) -> str:
    """Fallback parser if LLM doesn't return clean JSON (rare with JSON mode)."""
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        # Find index of first code split and last backticks
        clean = "\n".join(lines[1:-1] if "```" not in lines[-1] else lines[1:])
        clean = clean.replace("```sql", "").replace("```postgresql", "").replace("```", "")
    return clean.strip()

SQL_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL expert for a PostgreSQL banking database.
Generate a valid PostgreSQL SELECT query to answer the user's question.
Today's date is {current_date}.

Rules:
- Return ONLY a JSON object. No explanation outside the JSON.
- Format: {{"sql": "SELECT ...", "tables_used": ["table1", "table2"]}}
- Only use SELECT statements. Never UPDATE, DELETE, INSERT, DROP, CREATE.
- Only reference tables listed in the schema below.
- When user says "last month", "this week", "yesterday" — resolve to exact dates using {current_date}.
- Use LIMIT 500 on queries that could return large result sets.
- Use proper PostgreSQL date functions: DATE_TRUNC, INTERVAL, EXTRACT.

Prior conversation context:
{previous_context_block}
If the current question is a follow-up (e.g. "filter those by region", "now show last month", 
"same but for FAILED only"), extend or modify the prior SQL rather than starting from scratch.

Database schema:
{schema}
"""),
    ("human", "{user_query}")
])

def sql_gen_agent(state: PipelineState) -> dict:
    if state["query_intent"] == "RAG_ONLY" or not state["relevant_tables"]:
        return {"generated_sql": "", "sql_tables_used": []}
        
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        team_ids = [state["team_id"]]
        
    # Fetch full schema with column metadata
    schema_str = ""
    try:
        with get_sync_session() as session:
            # Query the master config table
            query = text("SELECT table_name, columns_metadata FROM master_config WHERE table_name IN :tables AND team_id IN :team_ids")
            result = session.execute(query, {"tables": tuple(state["relevant_tables"]), "team_ids": tuple(team_ids)})
            rows = result.fetchall()
            for row in rows:
                schema_str += f"Table: {row.table_name}\nColumns:\n"
                cols = row.columns_metadata if isinstance(row.columns_metadata, list) else json.loads(row.columns_metadata)
                for col in cols:
                    schema_str += f"  - {col['name']} ({col['type']}): {col.get('description', '')}\n"
                schema_str += "\n"
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return {"generated_sql": "", "sql_tables_used": []}

    if not schema_str:
        return {"generated_sql": "", "sql_tables_used": []}

    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=SQLGenOutput)
    chain = SQL_GEN_PROMPT | llm | parser

    # Build previous context block — helps the LLM refine rather than regenerate
    previous_sql = state.get("previous_sql", "")
    previous_query = state.get("previous_query", "")
    previous_tables = state.get("previous_tables_used", [])

    if previous_query:
        parts = [f"Previous question: {previous_query}"]
        if previous_sql:
            parts.append(f"Previous SQL executed:\n{previous_sql}")
        if previous_tables:
            parts.append(f"Tables used previously: {', '.join(previous_tables)}")
        previous_context_block = "\n".join(parts)
    else:
        previous_context_block = "No prior conversation."

    try:
        result = chain.invoke({
            "current_date": state["current_date"],
            "schema": schema_str,
            "user_query": state["user_query"],
            "previous_context_block": previous_context_block,
        })
        
        sql = result.get("sql", "")
        tables = result.get("tables_used", [])
        
        # Double check tables are valid within our relevant scope
        valid_tables = [t.lower() for t in state["relevant_tables"]]
        tables = [t for t in tables if t.lower() in valid_tables]
        print("[DEBUG] SQL GEN AGENT")
        return {
            "generated_sql": sql,
            "sql_tables_used": tables
        }
    except Exception as e:
        print(f"Error in SQL generation output parsing: {e}")
        return {"generated_sql": "", "sql_tables_used": []}


# ---------------------------------------------------------------------------
# SQL Retry: invoked when execution_agent hits a SQL error (once only)
# ---------------------------------------------------------------------------

SQL_RETRY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL expert for a PostgreSQL banking database.
A previously generated SQL query failed with an error. Fix it.
Today's date is {current_date}.
Date resolution examples (today = {current_date}):
- "this week" → WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
- "last month" → WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND created_at < DATE_TRUNC('month', CURRENT_DATE)
- "yesterday" → WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
- "this quarter" → WHERE created_at >= DATE_TRUNC('quarter', CURRENT_DATE)
Rules:
- Return ONLY a JSON object. No explanation outside the JSON.
- Format: {{"sql": "SELECT ...", "tables_used": ["table1", "table2"]}}
- Only use SELECT statements. Never UPDATE, DELETE, INSERT, DROP, CREATE.
- Only reference tables listed in the schema below.
- Use LIMIT 500 on queries that could return large result sets.
- Use proper PostgreSQL date functions: DATE_TRUNC, INTERVAL, EXTRACT.
- Do NOT wrap aggregates inside other aggregates (e.g. no json_agg around SUM).
- When using UNION, ensure each SELECT has the same number of columns and apply LIMIT before the UNION, not after.

Database schema:
{schema}
"""),
    ("human", """Original question: {user_query}

Failed SQL:
{failed_sql}

Error message:
{error_message}

Generate a corrected SQL query that avoids this error.""")
])


def sql_retry_agent(state: PipelineState) -> dict:
    """
    Called when execution_agent encounters an EXECUTION_ERROR.
    Re-generates the SQL with the error context so the LLM can fix it.
    Only runs once (the pipeline conditional edge checks sql_retry_count).
    """
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        team_ids = [state["team_id"]]
    # Re-fetch the schema (same logic as sql_gen_agent)
    schema_str = ""
    try:
        with get_sync_session() as session:
            query = text(
                "SELECT table_name, columns_metadata FROM master_config "
                "WHERE table_name IN :tables AND team_id IN :team_ids"
            )
            result = session.execute(query, {
                "tables": tuple(state["relevant_tables"]),
                "team_ids": tuple(team_ids),
            })
            rows = result.fetchall()
            for row in rows:
                schema_str += f"Table: {row.table_name}\nColumns:\n"
                cols = (
                    row.columns_metadata
                    if isinstance(row.columns_metadata, list)
                    else json.loads(row.columns_metadata)
                )
                for col in cols:
                    schema_str += f"  - {col['name']} ({col['type']}): {col.get('description', '')}\n"
                schema_str += "\n"
    except Exception as e:
        print(f"Error fetching schema in retry: {e}")
        return {"sql_retry_count": state.get("sql_retry_count", 0) + 1}

    if not schema_str:
        return {"sql_retry_count": state.get("sql_retry_count", 0) + 1}

    # Extract the original SQL from the EXECUTION_ERROR prefix
    failed_sql = state.get("generated_sql", "")
    if failed_sql.startswith("EXECUTION_ERROR:"):
        # The actual SQL is embedded in the error text; use whatever the LLM last produced
        # Try to extract the SQL from the error string
        import re
        sql_match = re.search(r'\[SQL:\s*(SELECT.*?)(?:\]|$)', failed_sql, re.IGNORECASE | re.DOTALL)
        if sql_match:
            failed_sql = sql_match.group(1).strip().rstrip("]")
        else:
            # Fallback: just pass the whole error string
            pass

    error_message = state.get("sql_error", "Unknown error")

    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=SQLGenOutput)
    chain = SQL_RETRY_PROMPT | llm | parser
    print("[DEBUG] SQL RETRY AGENT")
    try:
        result = chain.invoke({
            "current_date": state["current_date"],
            "schema": schema_str,
            "user_query": state["user_query"],
            "failed_sql": failed_sql,
            "error_message": error_message,
        })

        sql = result.get("sql", "")
        tables = result.get("tables_used", [])

        valid_tables = [t.lower() for t in state["relevant_tables"]]
        tables = [t for t in tables if t.lower() in valid_tables]
        # print(sql)
        return {
            "generated_sql": sql,
            "sql_tables_used": tables,
            "sql_retry_count": state.get("sql_retry_count", 0) + 1,
            "sql_error": "",
        }
    except Exception as e:
        print(f"Error in SQL retry output parsing: {e}")
        return {"sql_retry_count": state.get("sql_retry_count", 0) + 1}

