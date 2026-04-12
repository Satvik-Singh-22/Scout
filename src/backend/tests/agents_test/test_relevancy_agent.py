import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.relevancy_agent import relevancy_agent
from backend.agents.state import PipelineState

class RowMock:
    def __init__(self, table_name, semantic_definition):
        self.table_name = table_name
        self.semantic_definition = semantic_definition

class TestRelevancyAgent(unittest.TestCase):

    @patch("backend.agents.relevancy_agent.get_sync_session")
    def test_relevancy_mapping(self, mock_get_sync_session):
        # Mock the context manager and database execution
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session
        
        # Mock database rows returned
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            RowMock("mock_transactions", "Records of all payment transactions including amounts and status"),
            RowMock("mock_system_logs", "Hardware latency records"),
            RowMock("mock_customer_feedback", "Customer feedback and reviews"),
            RowMock("mock_transaction_timestamps", "Timestamps of all transactions")
        ]
        mock_session.execute.return_value = mock_result

        state: PipelineState = {
            "user_query": "What are my payment transactions in last 2 weeks?",
            "user_id": "test",
            "user_persona": "Enterprise_Analyst",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2023-10-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }
        
        print("Testing Relevancy Agent...")
        result = relevancy_agent(state)
        print("Returned Tables:", result.get("relevant_tables"))
        
        self.assertIn("mock_transactions", result.get("relevant_tables", []), "Agent should extract the mock_transactions table based on context")

if __name__ == '__main__':
    unittest.main()
