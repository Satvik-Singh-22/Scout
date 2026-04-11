from typing import TypedDict, List

class PipelineState(TypedDict):
    user_query: str           # The raw question from the user
    user_id: str              # UUID of the user (from JWT)
    user_persona: str         # "MANAGER" or "DEVELOPER"
    team_id: str              # User's home team UUID (organisational affiliation)
    allowed_team_ids: List[str]  # List of team UUIDs this user's pipeline can access
    current_date: str         # ISO date string e.g. "2025-01-15"
    query_intent: str         # "SQL_ONLY" | "RAG_ONLY" | "HYBRID"
    routing_decision: dict    # {"use_sql": bool, "use_rag": bool, "reasoning": str}
    relevant_tables: list     # List of table name strings selected by relevancy agent
    generated_sql: str        # The SQL string from sql_gen agent
    sql_results: list         # List of row dicts from execution agent
    rag_chunks: list          # List of text chunk strings from rag agent
    synthesized_context: str  # Combined narrative from synthesis agent
    final_answer: str         # Final user-facing answer from persona agent
    chain_of_thought: dict    # Full CoT JSON built by persona agent
    sql_tables_used: List[str] # List of tables explicitly used by sql_gen agent
    sql_retry_count: int       # Number of SQL retry attempts (max 1)
    sql_error: str             # Error message from failed SQL execution (passed to retry)
