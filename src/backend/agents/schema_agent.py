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
Think of this file as the tour guide for our data warehouse.
Sometimes a user isn't asking for actual numbers, but just wants to know "what kind of data do you have?"
Instead of trying to do complicated math, this guide simply opens the catalog and describes what is available.
For example, it will tell you, "We have a table for users, and it holds their names and emails." 
It doesn't fetch the data itself, just the *menu* of what's possible to ask for.
"""
import json
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text
from backend.agents.state import PipelineState
from backend.agents.llm import get_llm
from backend.db.session import get_sync_session

SCHEMA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data catalogue assistant for a banking intelligence system.
Answer the user's question about available data using only the schema information provided.

Rules:
- Only describe tables and columns that appear in the schema below.
- If the user asks what data is available about a topic, list the relevant tables and their most useful columns.
- If the user asks about a specific table, describe what it contains and list its columns with types and descriptions.
- Do not generate SQL. Do not say "you could run a query". Just describe the data.
- Be specific — mention actual column names, not vague descriptions.
- If no relevant tables exist for what they're asking about, say so clearly.

Prior conversation context:
{previous_context_block}
If the question is a follow-up (e.g. "tell me more about that table", "what about its columns"),
use the prior context to resolve which table or topic they mean.

Available schema:
{schema}
"""),
    ("human", "{user_query}")
])

def schema_agent(state: PipelineState) -> dict:
    print("[DEBUG] SCHEMA AGENT")

    # Fetch all tables this user has access to (same scope as relevancy agent)
    team_ids = state.get("allowed_team_ids", [])
    if not team_ids:
        team_ids = [state["team_id"]]

    try:
        with get_sync_session() as session:
            result = session.execute(
                text(
                    "SELECT table_name, semantic_definition, columns_metadata "
                    "FROM master_config "
                    "WHERE team_id IN :team_ids AND is_active = TRUE "
                    "ORDER BY table_name"
                ),
                {"team_ids": tuple(team_ids)}
            )
            rows = result.fetchall()
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return {
            "final_answer": "Unable to retrieve schema information at this time.",
            "relevant_tables": [],
            "chain_of_thought": {
                "sources": [], "sql_executed": "", "sql_results": [], "rag_chunks_used": 0,
                "agent_path": ["orchestrator", "schema"],
                "query_intent": "SCHEMA_LOOKUP", "confidence": "low",
                "tables_searched": [], "tables_used": [], 
                "teams_accessed": state.get("allowed_team_ids", []),
                "chart_type": "TABLE"
            }
        }

    if not rows:
        return {
            "final_answer": (
                "No tables are currently registered for your team. "
                "Please contact your Data Owner to onboard data."
            ),
            "relevant_tables": [],
            "chain_of_thought": {
                "sources": [], "sql_executed": "", "sql_results": [], "rag_chunks_used": 0,
                "agent_path": ["orchestrator", "schema"],
                "query_intent": "SCHEMA_LOOKUP", "confidence": "high",
                "tables_searched": [], "tables_used": [], 
                "teams_accessed": state.get("allowed_team_ids", []),
                "chart_type": "TABLE"
            }
        }

    # Build a readable schema string for the prompt
    schema_lines = []
    table_names = []
    for row in rows:
        table_name, semantic_def, columns_metadata = row.table_name, row.semantic_definition, row.columns_metadata
        table_names.append(table_name)
        schema_lines.append(f"\nTable: {table_name}")
        schema_lines.append(f"Description: {semantic_def}")
        schema_lines.append("Columns:")
        cols = columns_metadata if isinstance(columns_metadata, list) else json.loads(columns_metadata or "[]")
        for col in cols:
            schema_lines.append(f"  - {col['name']} ({col['type']}): {col.get('description', '')}")

    schema_str = "\n".join(schema_lines)

    previous_query = state.get("previous_query", "")
    previous_answer = state.get("previous_answer", "")

    if previous_query:
        previous_context_block = (
            f"Previous question: {previous_query}\n"
            f"Previous answer: {previous_answer[:400]}"
        )
    else:
        previous_context_block = "No prior conversation."

    chain = SCHEMA_PROMPT | get_llm()
    response = chain.invoke({
        "user_query": state["user_query"],
        "schema": schema_str,
        "previous_context_block": previous_context_block
    })

    final_answer = response.content.strip()

    chain_of_thought = {
        "sources": table_names,
        "sql_executed": "",
        "sql_results": [],
        "rag_chunks_used": 0,
        "agent_path": ["orchestrator", "schema"],
        "query_intent": "SCHEMA_LOOKUP",
        "confidence": "high",
        "tables_searched": table_names,
        "tables_used": [],
        "teams_accessed": state.get("allowed_team_ids", []),
        "chart_type": "TABLE"
    }

    return {
        "final_answer": final_answer,
        "relevant_tables": table_names,
        "chain_of_thought": chain_of_thought
    }
