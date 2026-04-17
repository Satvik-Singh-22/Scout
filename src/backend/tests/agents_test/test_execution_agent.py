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

    @patch("backend.agents.execution_agent.logger")
    @patch("backend.agents.execution_agent.get_sync_session")
    def test_db_error_logs_and_returns_execution_error(self, mock_get_sync_session, mock_logger):
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.side_effect = RuntimeError("column foo does not exist")

        state: PipelineState = {
            "user_query": "Show totals",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"],
            "generated_sql": "SELECT * FROM mock_transactions",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": ["mock_transactions"],
        }

        result = execution_agent(state)
        self.assertEqual(result.get("sql_results"), [])
        self.assertIn("column foo does not exist", result.get("execution_error", ""))
        self.assertIn("column foo does not exist", result.get("sql_error", ""))
        self.assertTrue(result.get("generated_sql", "").startswith("EXECUTION_ERROR:"))
        mock_logger.error.assert_called_once()

    def test_no_schema_available_short_circuits_execution(self):
        state: PipelineState = {
            "user_query": "Show totals",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"],
            "generated_sql": "NO_SCHEMA_AVAILABLE",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": [],
        }

        result = execution_agent(state)
        self.assertEqual(result.get("sql_results"), [])
        self.assertEqual(result.get("execution_error"), "NO_SCHEMA_AVAILABLE")
        self.assertEqual(result.get("sql_error"), "NO_SCHEMA_AVAILABLE")

if __name__ == '__main__':
    unittest.main()
