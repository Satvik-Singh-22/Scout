from sqlalchemy import text
from backend.db.session import get_sync_session
from backend.agents.state import PipelineState
import re

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]

def validate_sql(sql: str) -> tuple[bool, str]:
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper.split(): # Split to prevent false positives like 'DROP' in a string value 'DROPLET'
            return False, f"Forbidden keyword detected: {keyword}"
    if not sql_upper.strip().startswith("SELECT"):
        return False, "Query must start with SELECT"
    return True, ""

def verify_table_authorization(sql_tables: list[str], authorized_tables: list[str]) -> bool:
    """
    Check that every table the LLM reports using appears in authorized_tables.
    This prevents the LLM from accessing tables outside the master_config scope.
    """
    auth_lower = [t.lower() for t in authorized_tables]
    for table in sql_tables:
        if table.lower() not in auth_lower:
            return False
    return True

def execution_agent(state: PipelineState) -> dict:
    sql = state.get("generated_sql", "")
    if not sql:
        return {"sql_results": []}
    
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return {"sql_results": [], "generated_sql": f"BLOCKED: {error}"}
    
    # Use the explicitly stored tables from the sql_gen_agent
    used_tables = state.get("sql_tables_used", [])
    if not verify_table_authorization(used_tables, state["relevant_tables"]):
        return {"sql_results": [], "generated_sql": "BLOCKED: Unauthorized table reference"}
    print("[DEBUG] EXECUTION AGENT query: ", sql)
    try:
        with get_sync_session() as session:
            result = session.execute(text(sql))
            rows = [dict(row._mapping) for row in result.fetchmany(1000)]
            print("Success")
            return {"sql_results": rows, "sql_error": ""}
    except Exception as e:
        error_msg = str(e)
        print("Error")
        return {
            "sql_results": [],
            "generated_sql": f"EXECUTION_ERROR: {error_msg}",
            "sql_error": error_msg
        }

