# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ELI5 (What does this file do?):
Think of this as the master translator who speaks "Database."
You talk to it in plain English ("Show me the top 5 transactions from yesterday"), 
and it perfectly translates that into a complex SQL query (the language the database understands). 
It knows the exact rules and grammar to ask the database for the right numbers. 
And if the database complains that it didn't understand (a SQL error), 
this file has a "retry" ability to look at the error, figure out the typo, and try translating it again!
"""
import logging
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from sqlalchemy import text, bindparam
from backend.agents.state import PipelineState
from backend.db.session import get_sync_session
from langchain_core.prompts import ChatPromptTemplate
from backend.cache.query_cache import get_cached_sql, set_cached_sql
import json

_cache_logger = logging.getLogger(__name__)

class SQLGenOutput(BaseModel):
    sql: str = Field(description="The generated PostgreSQL SELECT query")
    tables_used: list[str] = Field(description="List of table names actually referenced in the SQL")


def _normalize_columns_metadata(raw_columns) -> list[dict]:
    """
    Normalize columns_metadata from DB drivers that may return list, dict, or JSON string.
    """
    if isinstance(raw_columns, list):
        return [col for col in raw_columns if isinstance(col, dict)]

    if isinstance(raw_columns, dict):
        maybe_columns = raw_columns.get("columns")
        if isinstance(maybe_columns, list):
            return [col for col in maybe_columns if isinstance(col, dict)]
        if "name" in raw_columns and "type" in raw_columns:
            return [raw_columns]
        return []

    if isinstance(raw_columns, str):
        try:
            parsed = json.loads(raw_columns)
        except Exception:
            return []
        return _normalize_columns_metadata(parsed)

    return []

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
- CRITICAL: You will be provided with database schemas. If the schema list is empty, DO NOT GUESS table or column names. You must immediately output the exact string: NO_SCHEMA_AVAILABLE.
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
    print(
        f"[DEBUG] SQL GEN AGENT START — intent={state['query_intent']}, "
        f"relevant_tables={state.get('relevant_tables', [])}"
    )
    if state["query_intent"] == "RAG_ONLY" or not state["relevant_tables"]:
        print("[DEBUG] SQL GEN AGENT — Early exit: RAG_ONLY or no relevant_tables")
        return {"generated_sql": "NO_SCHEMA_AVAILABLE", "sql_tables_used": []}

    # ──────────────────────────────────────────────────────────────────────
    # Phase 2: Exact-match cache check — avoids redundant Groq API calls
    # for recurring scheduled queries or identical follow-up questions.
    # Uses MD5 hash of the normalised query; intentionally NOT semantic
    # similarity to preserve temporal precision ("last week" ≠ "this week").
    # ──────────────────────────────────────────────────────────────────────
    user_query = state["user_query"]
    cached_sql = get_cached_sql(user_query)
    if cached_sql is not None and cached_sql.strip() and cached_sql.strip() != "NO_SCHEMA_AVAILABLE":
        _cache_logger.debug("Cache HIT for query: %s...", user_query[:50])
        print(f"[DEBUG] SQL GEN AGENT — Cache HIT, skipping Groq call")
        # Derive tables_used from the relevant_tables already resolved by relevancy_agent
        valid_tables = [t.lower() for t in state["relevant_tables"]]
        return {
            "generated_sql": cached_sql,
            "sql_tables_used": valid_tables,
        }
    if cached_sql is not None and (not cached_sql.strip() or cached_sql.strip() == "NO_SCHEMA_AVAILABLE"):
        _cache_logger.debug("Cache BYPASS for query %s due to empty/NO_SCHEMA_AVAILABLE entry", user_query[:50])
        
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        team_ids = [state["team_id"]]
        
    # Fetch full schema with column metadata
    schema_str = ""
    try:
        with get_sync_session() as session:
            # Query the master config table
            query = text(
                "SELECT table_name, columns_metadata FROM master_config "
                "WHERE LOWER(table_name) IN :tables AND team_id IN :team_ids"
            ).bindparams(
                bindparam("tables", expanding=True),
                bindparam("team_ids", expanding=True),
            )
            result = session.execute(query, {
                "tables": [t.lower() for t in state["relevant_tables"]],
                "team_ids": list(team_ids),
            })
            rows = result.fetchall()
            print(
                f"[DEBUG] SQL GEN AGENT — master_config returned {len(rows)} row(s) "
                f"for tables={state['relevant_tables']}, team_ids={team_ids}"
            )
            for row in rows:
                schema_str += f"Table: {row.table_name}\nColumns:\n"
                cols = _normalize_columns_metadata(row.columns_metadata)
                for col in cols:
                    schema_str += f"  - {col['name']} ({col['type']}): {col.get('description', '')}\n"
                schema_str += "\n"
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return {"generated_sql": "", "sql_tables_used": []}

    if not schema_str:
        print(
            f"[DEBUG] SQL GEN AGENT — No schema found in master_config for "
            f"tables={state['relevant_tables']}. Check that Pinecone table_name "
            f"metadata matches master_config exactly."
        )
        return {"generated_sql": "NO_SCHEMA_AVAILABLE", "sql_tables_used": []}

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

        if isinstance(sql, str) and sql.strip() == "NO_SCHEMA_AVAILABLE":
            return {
                "generated_sql": "NO_SCHEMA_AVAILABLE",
                "sql_tables_used": [],
            }

        # Double check tables are valid within our relevant scope
        valid_tables = [t.lower() for t in state["relevant_tables"]]
        tables = [t for t in tables if t.lower() in valid_tables]
        print("[DEBUG] SQL GEN AGENT")

        # Cache the successfully generated SQL for future identical queries
        if sql:
            set_cached_sql(user_query, sql)
            _cache_logger.debug("Cache SET for query: %s...", user_query[:50])

        return {
            "generated_sql": sql,
            "sql_tables_used": tables
        }
    except Exception as e:
        print(f"Error in SQL generation output parsing: {e}")
        return {"generated_sql": "NO_SCHEMA_AVAILABLE", "sql_tables_used": []}


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

OUTPUT SHAPE RULES:
- For breakdowns by category: SELECT category_col, aggregation AS value ...GROUP BY category_col
- For time-series: SELECT DATE_TRUNC('day', timestamp_col) AS date, aggregation AS value ...GROUP BY 1 ORDER BY 1
- For comparisons: SELECT group_col, metric1, metric2 ...GROUP BY group_col
- Always alias aggregated columns with readable names (total, count, amount, rate — not COUNT(*))
- ORDER BY the aggregated value DESC for category breakdowns

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
                "WHERE LOWER(table_name) IN :tables AND team_id IN :team_ids"
            ).bindparams(
                bindparam("tables", expanding=True),
                bindparam("team_ids", expanding=True),
            )
            result = session.execute(query, {
                "tables": [t.lower() for t in state["relevant_tables"]],
                "team_ids": list(team_ids),
            })
            rows = result.fetchall()
            for row in rows:
                schema_str += f"Table: {row.table_name}\nColumns:\n"
                cols = _normalize_columns_metadata(row.columns_metadata)
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

