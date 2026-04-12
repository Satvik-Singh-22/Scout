import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.execution_agent import execution_agent
from backend.agents.state import PipelineState

class TestExecutionAgent(unittest.TestCase):

    @patch("backend.agents.execution_agent.get_sync_session")
    def test_forbidden_sql(self, mock_get_sync_session):
        state: PipelineState = {
            "user_query": "Delete all transactions.",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"],
            "generated_sql": "DROP TABLE mock_transactions;",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }
        
        print("Testing Execution Agent Security Block...")
        result = execution_agent(state)
        self.assertTrue(result["generated_sql"].startswith("BLOCKED: Forbidden keyword"))

    @patch("backend.agents.execution_agent.get_sync_session")
    def test_unauthorized_table(self, mock_get_sync_session):
        state: PipelineState = {
            "user_query": "Show me customer data.",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"], # Only authorized for transactions
            "generated_sql": "SELECT * FROM mock_customer_data;",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": ["mock_customer_data"]
        }
        
        print("Testing Execution Agent Table Authorization Block...")
        result = execution_agent(state)
        self.assertTrue(result["generated_sql"].startswith("BLOCKED: Unauthorized"))

if __name__ == '__main__':
    unittest.main()
