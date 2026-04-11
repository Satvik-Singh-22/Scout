import sys
import os
import json
from datetime import date
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def demo_anomaly_system():
    print("==================================================")
    print("🔎 SCOUT ANOMALY DETECTION SYSTEM DEMO")
    print("==================================================\n")

    # 1. Imports (mocking dependencies first to avoid env errors)
    with patch('backend.agents.llm.get_llm'), patch('backend.db.session.get_sync_session'):
        from backend.agents.anomaly_reasoner_agent import anomaly_reasoner_agent
        from backend.agents.anomaly_checker_agent import anomaly_checker_agent

    # 2. Setup Context
    query = "Analyze recent payment failures"
    tables = ["payments"]
    results = [{"id": 1, "status": "FAILED", "amount": 5000}]
    team_id = "team-dev-001"
    today = "2025-04-11"

    print(f"Query: {query}")
    print(f"Tables: {tables}")
    print(f"Target Team: {team_id}\n")

    # 3. Step 1: Anomaly Reasoner
    print("[STEP 1] Reasoning about potential anomalies...")
    
    # We patch the invoke method of the RunnableSequence to bypass all internal 
    # LangChain complexity (Prompt | LLM | Parser).
    mock_hypotheses = {
        "hypotheses": [
            {
                "title": "Abnormal Failure Rate",
                "description": "The current failure rate is significantly higher than baseline.",
                "verification_sql": "SELECT 0.22 AS metric_value",
                "condition": "metric_value > 0.15",
                "severity": "HIGH",
                "metric_label": "failure rate"
            }
        ],
        "reasoning": "Detected multiple failures in the south region sample."
    }

    with patch('backend.agents.anomaly_reasoner_agent._fetch_table_schemas', return_value="Table: payments"), \
         patch('langchain_core.runnables.base.RunnableSequence.invoke', return_value=mock_hypotheses):
        
        reasoner_output = anomaly_reasoner_agent(query, tables, results, team_id, today)

    if reasoner_output and reasoner_output.hypotheses:
        h = reasoner_output.hypotheses[0]
        print(f"✅ Reasoner identified a hypothesis:")
        print(f"   - Title: {h.title}")
        print(f"   - Condition: {h.condition}")
        print(f"   - Verification SQL: {h.verification_sql}")
    else:
        print("❌ Reasoner failed to identify anomalies.")
        return

    # 4. Step 2: Anomaly Checker (Success Case)
    print("\n[STEP 2] Verifying anomaly (Success Case)...")
    
    mock_session = MagicMock()
    mock_res = MagicMock()
    mock_res._mapping = {"metric_value": 0.22}
    mock_session.execute.return_value.fetchone.return_value = mock_res

    with patch('backend.agents.anomaly_checker_agent.get_sync_session') as mock_session_ctx:
        mock_session_ctx.return_value.__enter__.return_value = mock_session
        
        alerts = anomaly_checker_agent(reasoner_output, team_id)

    if alerts:
        print(f"✅ Checker CONFIRMED the anomaly!")
        print(f"   - Alert Title: {alerts[0]['title']}")
        print(f"   - Description: {alerts[0]['description']}")
    else:
        print("❌ Checker dismissed the anomaly.")

    # 5. Step 3: Anomaly Checker (Retry/Fix Case)
    print("\n[STEP 3] Verifying SQL Self-Healing (Retry Case)...")
    
    # Mock session to fail first, then succeed
    mock_session_retry = MagicMock()
    mock_res_fixed = MagicMock()
    mock_res_fixed._mapping = {"metric_value": 0.22}
    
    mock_session_retry.execute.side_effect = [
        Exception("PSQLError: column 'wrong_col' does not exist"),
        MagicMock(fetchone=lambda: mock_res_fixed)
    ]

    mock_fix_output = {"fixed_sql": "SELECT 0.22 AS metric_value"}
    
    with patch('backend.agents.anomaly_checker_agent.get_sync_session') as mock_session_ctx, \
         patch('langchain_core.runnables.base.RunnableSequence.invoke', return_value=mock_fix_output):
        
        mock_session_ctx.return_value.__enter__.return_value = mock_session_retry
        
        alerts_retry = anomaly_checker_agent(reasoner_output, team_id)

    if alerts_retry:
        print("✅ SQL self-healed after retry!")
        print(f"   - Final SQL: {alerts_retry[0]['data_snapshot']['verification_sql']}")
    else:
        print("❌ Retry logic failed.")

    print("\n==================================================")
    print("✨ DEMO COMPLETED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    demo_anomaly_system()
