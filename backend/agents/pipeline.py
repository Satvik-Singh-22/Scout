from langgraph.graph import StateGraph, END
from backend.agents.state import PipelineState
from backend.agents.orchestrator_agent import orchestrator_agent
from backend.agents.relevancy_agent import relevancy_agent
from backend.agents.sql_gen_agent import sql_gen_agent, sql_retry_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.execution_agent import execution_agent
from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.persona_agent import persona_agent


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
        # print(generated_sql)
        return "sql_retry"
    return "synthesis"


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("relevancy", relevancy_agent)
    graph.add_node("sql_gen", sql_gen_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("execution", execution_agent)
    graph.add_node("sql_retry", sql_retry_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("persona", persona_agent)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "relevancy")
    
    # After relevancy, run SQL gen and RAG in parallel
    graph.add_edge("relevancy", "sql_gen")
    graph.add_edge("relevancy", "rag")
    
    # SQL gen flows into execution
    graph.add_edge("sql_gen", "execution")

    # After execution: conditionally retry or continue
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

