"""
ELI5 (What does this file do?):
Imagine a factory assembly line, but for answering questions instead of building cars. 
This file builds and manages that assembly line, which we call a "pipeline." 
When a user asks a question, this file decides the exact step-by-step path the question should take. 
For example, it steps from the "Orchestrator" (who decides what kind of question it is), 
to "Relevancy" (who finds the right data charts), 
to "SQL Gen" (who writes the database query), and finally to "Persona" (who frames the final answer perfectly). 
It decides who does what, and in what order, ensuring smooth teamwork.
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


def route_after_orchestrator(state: PipelineState) -> str:
    """
    Branches immediately after the orchestrator based on query_intent:
      - GENERAL      → general agent (LLM answers directly, no data access)
      - SCHEMA_LOOKUP → schema agent (describe tables/columns, no SQL execution)
      - everything else → relevancy (SQL_ONLY, RAG_ONLY, HYBRID full pipeline)
    """
    intent = state.get("query_intent", "HYBRID")
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

    graph.set_entry_point("orchestrator")

    # Branch immediately after orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "general": "general",
            "schema": "schema",
            "relevancy": "relevancy",
        }
    )

    # Short-circuit nodes go straight to END — no synthesis/persona needed
    graph.add_edge("general", END)
    graph.add_edge("schema", END)

    # After relevancy, run SQL gen and RAG in parallel
    graph.add_edge("relevancy", "sql_gen")
    graph.add_edge("relevancy", "rag")

    # SQL gen flows into execution
    graph.add_edge("sql_gen", "execution")

    # After execution: conditionally retry or continue to synthesis
    graph.add_conditional_edges("execution", _should_retry_sql, {
        "sql_retry": "sql_retry",
        "synthesis": "synthesis",
    })

    # Retry flows back into execution for a second attempt
    graph.add_edge("sql_retry", "execution")

    # RAG feeds into synthesis directly
    graph.add_edge("rag", "synthesis")

    graph.add_edge("synthesis", "persona")
    graph.add_edge("persona", END)

    return graph.compile()


pipeline = build_pipeline()
