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
Imagine a factory assembly line, but for answering questions instead of building cars. 
This file builds and manages that assembly line, which we call a "pipeline." 
When a user asks a question, this file decides the exact step-by-step path the question should take. 
For example, it steps from the "Orchestrator" (who decides what kind of question it is), 
to "Relevancy" (who finds the right data charts), 
to "SQL Gen" (who writes the database query), and finally to "Persona" (who frames the final answer perfectly). 
It decides who does what, and in what order, ensuring smooth teamwork.

When the user toggles to "Slack/Jira" mode in the UI the entry-point router bypasses the
orchestrator entirely and routes directly to the slack_jira agent node.
"""
from langgraph.graph import StateGraph, END
from backend.agents.state import PipelineState
from backend.agents.orchestrator_agent import orchestrator_agent
from backend.agents.relevancy_agent import relevancy_agent
from backend.agents.sql_gen_agent import sql_gen_agent, sql_retry_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.execution_agent import execution_agent
from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.persona_agent import persona_agent
from backend.agents.general_agent import general_agent
from backend.agents.schema_agent import schema_agent
from backend.agents.slack_jira import slack_jira_agent


# ---------------------------------------------------------------------------
# Entry-point router — checks the user's mode toggle BEFORE hitting the
# orchestrator.  This avoids making the orchestrator aware of agent_mode.
# ---------------------------------------------------------------------------
def _route_entry(state: PipelineState) -> str:
    """
    First routing decision at the pipeline entry point.

    If the frontend sends ``agent_mode == "SLACK_JIRA"`` the request goes
    straight to the ``slack_jira`` node.  Everything else (including the
    default empty / "DATABASE" value) proceeds to the orchestrator as
    before.
    """
    mode = state.get("agent_mode", "DATABASE").upper()
    if mode == "SLACK_JIRA":
        return "slack_jira"
    return "orchestrator"
from backend.agents.guard_agent import guard_agent


def route_after_orchestrator(state: PipelineState) -> str:
    """
    Branches immediately after the orchestrator based on query_intent:
      - BLOCKED       → guard agent (funny refusal, zero DB access, no pipeline)
      - GENERAL       → general agent (LLM answers directly, no data access)
      - SCHEMA_LOOKUP → schema agent (describe tables/columns, no SQL execution)
      - everything else → relevancy (SQL_ONLY, RAG_ONLY, HYBRID full pipeline)
    """
    intent = state.get("query_intent", "HYBRID")
    if intent == "BLOCKED":
        return "guard"
    if intent == "GENERAL":
        return "general"
    if intent == "SCHEMA_LOOKUP":
        return "schema"
    return "relevancy"


def _should_retry_sql(state: PipelineState) -> str:
    """
    Conditional edge after execution:
      - If there is an EXECUTION_ERROR and we haven't retried yet → "sql_retry"
      - Otherwise → "synthesis"
    """
    generated_sql = state.get("generated_sql", "")
    retry_count = state.get("sql_retry_count", 0)
    has_error = generated_sql.startswith("EXECUTION_ERROR")

    if has_error and (retry_count < 1):
        return "sql_retry"
    return "synthesis"


def build_pipeline():
    graph = StateGraph(PipelineState)

    # Core data pipeline nodes
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("relevancy", relevancy_agent)
    graph.add_node("sql_gen", sql_gen_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("execution", execution_agent)
    graph.add_node("sql_retry", sql_retry_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("persona", persona_agent)

    # Short-circuit nodes (bypass the full data pipeline)
    graph.add_node("general", general_agent)
    graph.add_node("schema", schema_agent)
    graph.add_node("guard", guard_agent)   # Security gate: blocks destructive queries

    # Slack/Jira agent node (activated by user-mode toggle)
    graph.add_node("slack_jira", slack_jira_agent)

    # --- Entry point: mode-based routing -----------------------------------
    graph.set_entry_point("entry_router")
    graph.add_node("entry_router", lambda state: {})  # pass-through, no state changes
    graph.add_conditional_edges(
        "entry_router",
        _route_entry,
        {
            "slack_jira": "slack_jira",
            "orchestrator": "orchestrator",
        },
    )

    # Slack/Jira goes straight to END — it handles everything internally
    graph.add_edge("slack_jira", END)

    # Branch immediately after orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "guard": "guard",
            "general": "general",
            "schema": "schema",
            "relevancy": "relevancy",
        }
    )

    # Short-circuit nodes go straight to END — no synthesis/persona needed
    graph.add_edge("guard", END)    # Blocked: funny refusal, pipeline never starts
    graph.add_edge("general", END)
    graph.add_edge("schema", END)

    # Sequential pipeline: relevancy -> rag -> sql_gen -> execution
    graph.add_edge("relevancy", "rag")
    graph.add_edge("rag", "sql_gen")

    # SQL gen flows into execution
    graph.add_edge("sql_gen", "execution")

    # After execution: conditionally retry or continue to synthesis
    graph.add_conditional_edges("execution", _should_retry_sql, {
        "sql_retry": "sql_retry",
        "synthesis": "synthesis",
    })

    # Retry flows back into execution for a second attempt
    graph.add_edge("sql_retry", "execution")

    graph.add_edge("synthesis", "persona")
    graph.add_edge("persona", END)

    return graph.compile()


pipeline = build_pipeline()
