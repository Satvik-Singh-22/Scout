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
This agent now does one thing at a time.
1) Ask the LLM for a tiny search keyword (1-3 words).
2) Call Pinecone tool directly in Python with that keyword.
3) Pass the raw schema text through untouched so SQL generation sees full definitions.

The LLM is NOT allowed to summarize schema tool output here.
"""
import re
import json
import ast
from langchain_core.prompts import ChatPromptTemplate
from backend.agents.llm import get_llm
from sqlalchemy import text, bindparam
from backend.agents.state import PipelineState
from backend.agents.tools.search_schema_tool import search_schema
from backend.db.session import get_sync_session

_SEARCH_FAILURE_MARKERS = (
    "No relevant schemas found",
    "Schema search unavailable",
    "Schema search encountered an error",
    "Schema search failed",
)

_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "show", "give",
    "what", "which", "where", "when", "who", "whom", "have", "has", "had", "was",
    "were", "are", "is", "not", "all", "last", "week", "month", "year", "today",
    "yesterday", "please", "about", "only", "need", "data", "table", "tables",
}


def _has_valid_schema_search_results(results: str) -> bool:
    if not results:
        return False
    return not any(marker in results for marker in _SEARCH_FAILURE_MARKERS)


def _normalize_tool_result(raw_result) -> dict:
    """Normalize tool return value into {schema_string, table_names}."""
    if isinstance(raw_result, dict):
        schema_string = str(raw_result.get("schema_string", "") or "")
        table_names = raw_result.get("table_names", []) or []
        if not isinstance(table_names, list):
            table_names = []
        return {
            "schema_string": schema_string,
            "table_names": [str(t).strip() for t in table_names if str(t).strip()],
        }

    if isinstance(raw_result, str):
        raw = raw_result.strip()
        if not raw:
            return {"schema_string": "", "table_names": []}

        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw)
                if isinstance(parsed, dict):
                    return _normalize_tool_result(parsed)
            except Exception:
                pass

        # Legacy fallback: plain schema string
        return {
            "schema_string": raw,
            "table_names": _extract_table_names(raw),
        }

    return {"schema_string": "", "table_names": []}


def _extract_keywords(user_query: str) -> list[str]:
    normalized = "".join(ch.lower() if (ch.isalnum() or ch == "_") else " " for ch in user_query)
    ordered_keywords: list[str] = []
    seen: set[str] = set()
    for token in normalized.split():
        if len(token) < 3 or token in _STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        ordered_keywords.append(token)
    return ordered_keywords[:8]


def _build_search_keyword(user_query: str) -> str:
    """
    Build a compact semantic keyword phrase for Pinecone retrieval.
    This avoids passing long conversational questions directly to embeddings.
    """
    keywords = _extract_keywords(user_query)
    if keywords:
        return " ".join(keywords[:2])

    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in user_query)
    fallback_tokens = [t for t in normalized.split() if len(t) >= 3]
    if fallback_tokens:
        return " ".join(fallback_tokens[:2])

    return user_query.strip()[:40] or "general"


def _sanitize_keyword(raw_keyword: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\s]", " ", (raw_keyword or "").strip().lower())
    tokens = [t for t in cleaned.split() if t]
    if not tokens:
        return ""
    return " ".join(tokens[:3])


KEYWORD_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a database routing assistant.
Return ONLY a 1-to-3 word search keyword for schema retrieval.
Do not return punctuation, explanation, JSON, or extra text.

Examples:
- User: What is the total transaction volume this month, broken down by region?
  Output: transaction volume
- User: Show API error spikes last week
  Output: api errors
""",
    ),
    ("human", "{user_query}"),
])


def _llm_search_keyword(user_query: str) -> str:
    try:
        llm = get_llm(temperature=0, json_mode=False)
        prompt_messages = KEYWORD_PROMPT.format_messages(user_query=user_query)
        response = llm.invoke(prompt_messages)
        raw = getattr(response, "content", str(response))
        keyword = _sanitize_keyword(raw)
        if keyword:
            return keyword
    except Exception as exc:
        print(f"[RELEVANCY] keyword LLM error: {exc}")

    return _build_search_keyword(user_query)


def _format_schema_candidates(rows) -> str:
    if not rows:
        return ""

    lines = []
    for i, row in enumerate(rows, start=1):
        semantic_def = row.semantic_definition or "No description available."
        lines.append(
            f"[{i}] Table: {row.table_name} (relevance: fallback)\n"
            f"     Description: {semantic_def}"
        )
    return "\n---\n".join(lines)


def _fallback_schema_search(state: PipelineState, user_query: str) -> dict:
    """
    Fallback path when Pinecone is unavailable or returns no hits.
    Uses master_config for the user's allowed teams with keyword matching.
    """
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        team_ids = [state["team_id"]]

    # Strong prior for follow-up questions: reuse previous tables when available.
    previous_tables = state.get("previous_tables_used", [])

    try:
        with get_sync_session() as session:
            if previous_tables:
                query_prev = text(
                    "SELECT table_name, semantic_definition FROM master_config "
                    "WHERE is_active = TRUE "
                    "AND team_id IN :team_ids "
                    "AND table_name IN :tables "
                    "LIMIT 8"
                ).bindparams(
                    bindparam("team_ids", expanding=True),
                    bindparam("tables", expanding=True),
                )
                prev_rows = session.execute(
                    query_prev,
                    {"team_ids": list(team_ids), "tables": list(previous_tables)},
                ).fetchall()
                formatted = _format_schema_candidates(prev_rows)
                if formatted:
                    return {
                        "schema_string": formatted,
                        "table_names": [row.table_name for row in prev_rows if getattr(row, "table_name", None)],
                    }

            keywords = _extract_keywords(user_query)
            if keywords:
                clauses = []
                params = {"team_ids": list(team_ids)}
                bind_params = [bindparam("team_ids", expanding=True)]

                for i, kw in enumerate(keywords):
                    pname = f"kw_{i}"
                    params[pname] = f"%{kw}%"
                    bind_params.append(bindparam(pname))
                    clauses.append(
                        f"lower(table_name) LIKE :{pname} "
                        f"OR lower(coalesce(semantic_definition, '')) LIKE :{pname} "
                        f"OR lower(cast(columns_metadata as text)) LIKE :{pname}"
                    )

                query_kw = text(
                    "SELECT table_name, semantic_definition FROM master_config "
                    "WHERE is_active = TRUE "
                    "AND team_id IN :team_ids "
                    f"AND ({' OR '.join(clauses)}) "
                    "LIMIT 8"
                ).bindparams(*bind_params)

                kw_rows = session.execute(query_kw, params).fetchall()
                formatted = _format_schema_candidates(kw_rows)
                if formatted:
                    return {
                        "schema_string": formatted,
                        "table_names": [row.table_name for row in kw_rows if getattr(row, "table_name", None)],
                    }

            query_broad = text(
                "SELECT table_name, semantic_definition FROM master_config "
                "WHERE is_active = TRUE AND team_id IN :team_ids "
                "LIMIT 8"
            ).bindparams(bindparam("team_ids", expanding=True))
            broad_rows = session.execute(query_broad, {"team_ids": list(team_ids)}).fetchall()
            return {
                "schema_string": _format_schema_candidates(broad_rows),
                "table_names": [row.table_name for row in broad_rows if getattr(row, "table_name", None)],
            }
    except Exception as exc:
        print(f"[RELEVANCY] DB fallback error: {exc}")
        return {"schema_string": "", "table_names": []}

def _extract_table_names(raw_schemas: str) -> list[str]:
    if not raw_schemas:
        return []

    tables: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(r"Table:\s*([a-zA-Z0-9_\.]+)")
    for match in pattern.findall(raw_schemas):
        table = match.strip()
        if table and table.lower() not in seen:
            seen.add(table.lower())
            tables.append(table)
    return tables


def relevancy_agent(state: PipelineState) -> dict:
    if state["query_intent"] == "RAG_ONLY":
        print("[DEBUG] RAG_ONLY intent detected — skipping relevancy agent")
        return {"relevant_tables": [], "synthesized_context": ""}

    user_query = state["user_query"]

    print("[DEBUG] RELEVANCY AGENT — generating compact keyword with LLM")
    search_keyword = _llm_search_keyword(user_query)
    print(f"[RELEVANCY] Pinecone search keyword: '{search_keyword}'")

    # Tool execution happens in plain Python here. No AgentExecutor/tool loop.
    try:
        raw_result = search_schema.invoke({"search_keyword": search_keyword})
        parsed_result = _normalize_tool_result(raw_result)
        if not parsed_result["schema_string"]:
            print("[RELEVANCY] search_schema tool returned None")
    except Exception as e:
        print(f"[RELEVANCY] search_schema tool error: {e}")
        parsed_result = {"schema_string": "", "table_names": []}

    schema_search_results = parsed_result["schema_string"]

    if not _has_valid_schema_search_results(schema_search_results):
        print("[RELEVANCY] Pinecone unavailable or empty. Falling back to master_config search.")
        parsed_result = _fallback_schema_search(state, user_query)
        schema_search_results = parsed_result.get("schema_string", "")

    if not schema_search_results:
        print("[RELEVANCY] No schema context available from Pinecone or fallback search.")
        return {"relevant_tables": [], "synthesized_context": ""}

    raw_schemas = str(schema_search_results)
    tables = parsed_result.get("table_names") or _extract_table_names(raw_schemas)
    tables = [t for t in tables if t]
    return {
        "relevant_tables": tables,
        "synthesized_context": raw_schemas,
    }
