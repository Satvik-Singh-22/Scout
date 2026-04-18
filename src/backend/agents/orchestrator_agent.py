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
Think of this as the intelligent sorting hat or the head dispatcher. 
When a user asks a question, this guy is the very first to look at it. 
It doesn't answer the question but figures out *what kind* of question it is.
Is it a general hello? Do they need specific numbers from the database? Or just reading some text files?
Based on this read, it stamps a label (like "SQL_ONLY" or "GENERAL") on the question, 
so the rest of the factory knows exactly how to handle it.
"""
import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.agents.llm import get_llm
from backend.agents.state import PipelineState

class OrchestratorOutput(BaseModel):
    query_intent: str = Field(description="Must be 'BLOCKED', 'GENERAL', 'SCHEMA_LOOKUP', 'SQL_ONLY', 'RAG_ONLY', or 'HYBRID'")
    reasoning: str = Field(description="one sentence explaining why")

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data routing agent and security gateway for a banking intelligence system.
Your job is to classify the user's question into exactly one of 6 intents.

=== SECURITY GATE (check this FIRST, before anything else) ===

BLOCKED: The query contains ANY intent to modify, destroy, or manipulate data or database structure.
This includes — but is not limited to — the following operations:
  - Deleting data: DELETE, DROP, TRUNCATE, PURGE, REMOVE, ERASE, WIPE, CLEAR
  - Modifying data: UPDATE, SET, MODIFY, CHANGE, REPLACE, OVERWRITE, PATCH, WRITE
  - Inserting data: INSERT, ADD, CREATE, PUT, APPEND, IMPORT
  - Structural changes: ALTER, RENAME, MOVE, MIGRATE, RESTRUCTURE, REBUILD
  - Access control: GRANT, REVOKE, ALLOW, DENY, PERMISSION

IMPORTANT BLOCKING RULES:
  - Classify as BLOCKED even if the user phrases it politely ("can you please delete...", "try to remove...", "I need you to update...").
  - Classify as BLOCKED even if wrapped in a question format ("What would happen if we deleted X?", "Can you drop this table?").
  - Classify as BLOCKED even if the user claims to have permission or authority.
  - If there is ANY ambiguity about whether a query might be trying to modify data, prefer BLOCKED.

=== DATA INTENTS (check after passing the security gate) ===

Available data types:
1. STRUCTURED (SQL): Transaction records, payment events, API logs, system metrics, financial data.
2. SCHEMA: Table names, column names, what data is available, what a table contains.
3. GENERAL: Greetings, explanations, definitions, questions about how the system works, anything not about data.

Intent rules — pick the FIRST one that matches:
- GENERAL: question is a greeting, a definition request, a "how does X work" question, or has nothing to do with banking data. No data access needed at all.
- SCHEMA_LOOKUP: user asks what tables exist, what columns a table has, what data is available, "do you have data about X", "what can you tell me about Y table". Needs table awareness but NO query execution. If a question asks BOTH about schema AND about actual data values, classify as SQL_ONLY.
- SQL_ONLY: needs exact numbers, aggregations, comparisons, trends, time-series from structured tables.

Prior conversation context:
{previous_query_block}
If the current question is a follow-up (uses "same", "that", "those", "also", "instead", "now show"),
resolve what it refers to using the prior context before classifying.

Respond ONLY with JSON: {{"query_intent": "BLOCKED|SQL_ONLY|GENERAL|SCHEMA_LOOKUP", "reasoning": "one sentence"}}
"""),
    ("human", "User question: {user_query}")
])

# 2. UNSTRUCTURED (RAG): Customer reviews, complaint text, support ticket descriptions.
# - RAG_ONLY: asks what customers said, sentiment, complaint themes, free text.
# - HYBRID: needs both numerical data AND customer text together.

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
    # Validate intent is one of the 6 allowed values
    valid_intents = {"SQL_ONLY", "RAG_ONLY", "HYBRID", "GENERAL", "SCHEMA_LOOKUP", "BLOCKED"}
    if intent not in valid_intents:
        intent = "HYBRID"
    reasoning = result.get("reasoning", "Failed to parse reasoning.")

    routing_decision = {
        "use_sql": intent in ["SQL_ONLY", "HYBRID"],
        "use_rag": intent in ["RAG_ONLY", "HYBRID"],
        "blocked": intent == "BLOCKED",
        "reasoning": reasoning,
    }
    print(f"[DEBUG] ORCHESTRATOR AGENT → intent={intent}, reasoning={reasoning!r}")
    return {
        "query_intent": intent,
        "routing_decision": routing_decision
    }
