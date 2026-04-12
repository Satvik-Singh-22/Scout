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
Imagine a clipboard that gets passed along an assembly line. 
Every worker in the line reads from this clipboard to know what the previous person did, 
and writes down their own results before passing it on.
This file defines exactly what pieces of paper are on that clipboard.
It tracks the user's original question, what tables were found, what the database query was, 
and what the final answer should sound like. It ensures no information is lost as the agents do their work.
"""
from typing import TypedDict, List

class PipelineState(TypedDict):
    user_query: str           # The raw question from the user
    user_id: str              # UUID of the user (from JWT)
    user_persona: str         # "EXECUTIVE" or "TECHNICAL"
    team_id: str              # User's home team UUID (organisational affiliation)
    allowed_team_ids: List[str]  # List of team UUIDs this user's pipeline can access
    current_date: str         # ISO date string e.g. "2025-01-15"
    query_intent: str         # "SQL_ONLY" | "RAG_ONLY" | "HYBRID" | "GENERAL" | "SCHEMA_LOOKUP"
    routing_decision: dict    # {"use_sql": bool, "use_rag": bool, "reasoning": str}
    relevant_tables: list     # List of table name strings selected by relevancy agent
    generated_sql: str        # The SQL string from sql_gen agent
    sql_tables_used: List[str] # List of tables explicitly used by sql_gen agent
    sql_results: list         # List of row dicts from execution agent
    sql_retry_count: int       # Number of SQL retry attempts (max 1)
    sql_error: str             # Error message from failed SQL execution (passed to retry)
    rag_chunks: list          # List of text chunk strings from rag agent
    synthesized_context: str  # Combined narrative from synthesis agent
    final_answer: str         # Final user-facing answer from persona agent
    chain_of_thought: dict    # Full CoT JSON built by persona agent

    # Multi-turn conversation context (empty strings / empty list on first turn)
    previous_query: str            # The user's last question
    previous_answer: str           # The assistant's last answer
    previous_sql: str              # SQL executed in last turn (empty string if none)
    previous_tables_used: List[str]  # Tables confirmed used last turn
