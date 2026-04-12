from openpyxl.worksheet.dimensions import RowDimension
import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.sql_gen_agent import sql_gen_agent
from backend.agents.state import PipelineState

class RowMock:
    def __init__(self, table_name, columns_metadata):
        self.table_name = table_name
        self.columns_metadata = columns_metadata

class TestSQLGenAgent(unittest.TestCase):

    @patch("backend.agents.sql_gen_agent.get_sync_session")
    def test_sql_generation(self, mock_get_sync_session):
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            RowMock("mock_employee_transactions", json.dumps([
                {"name": "id", "type": "UUID"},
                {"name": "amount", "type": "DECIMAL"},
                {"name": "status", "type": "VARCHAR"}
            ])),
            RowMock("mock_transaction_timestamps", json.dumps([
                {"name": "id", "type": "UUID"},
                {"name": "timestamp", "type": "TIMESTAMP"}
            ])),
            RowMock("mock_customer_feedback", json.dumps([
                {"name": "id", "type": "UUID"},
                {"name": "feedback", "type": "TEXT"}
            ])),
            RowMock("mock_employee_details", json.dumps([
                {"name": "id", "type": "UUID"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "role", "type": "VARCHAR"}
            ]))
        ]
        mock_session.execute.return_value = mock_result

        state: PipelineState = {
            "user_query": "What is the total transactions amount in last week?",
            "user_id": "test",
            "user_persona": "Manager",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_employee_transactions", "mock_transaction_timestamps"],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": []
        }
        
        print("Testing SQL Generation Agent...")
        result = sql_gen_agent(state)
        sql = result.get("generated_sql", "").upper()
        used_tables = result.get("sql_tables_used", [])
        
        print("Generated SQL:", sql)
        print("Used Tables:", used_tables)
        
        self.assertTrue(sql.startswith("SELECT"), "Query must be a SELECT statement")
        self.assertIn("MOCK_EMPLOYEE_TRANSACTIONS", sql, "Query must query the mock_transactions table")
        self.assertIn("mock_employee_transactions", used_tables, "Used tables must be reported")

if __name__ == '__main__':
    unittest.main()
