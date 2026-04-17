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

    def test_returns_no_schema_available_when_relevant_tables_empty(self):
        state: PipelineState = {
            "user_query": "Total volume by region",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": []
        }

        result = sql_gen_agent(state)
        self.assertEqual(result.get("generated_sql"), "NO_SCHEMA_AVAILABLE")
        self.assertEqual(result.get("sql_tables_used"), [])

    @patch("backend.agents.sql_gen_agent.get_cached_sql")
    @patch("backend.agents.sql_gen_agent.JsonOutputParser")
    @patch("backend.agents.sql_gen_agent.get_llm")
    @patch("backend.agents.sql_gen_agent.get_sync_session")
    def test_bypass_empty_cached_sql(
        self,
        mock_get_sync_session,
        mock_get_llm,
        mock_parser,
        mock_get_cached_sql,
    ):
        mock_get_cached_sql.return_value = ""
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            RowMock("mock_transactions", json.dumps([
                {"name": "id", "type": "UUID"},
                {"name": "amount", "type": "DECIMAL"},
            ]))
        ]
        mock_session.execute.return_value = mock_result

        prompt = MagicMock()
        first_chain = MagicMock()
        final_chain = MagicMock()
        prompt.__or__.return_value = first_chain
        first_chain.__or__.return_value = final_chain
        final_chain.invoke.return_value = {
            "sql": "SELECT SUM(amount) AS total FROM mock_transactions",
            "tables_used": ["mock_transactions"],
        }

        state: PipelineState = {
            "user_query": "Total transactions",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": []
        }

        with patch("backend.agents.sql_gen_agent.SQL_GEN_PROMPT", prompt):
            result = sql_gen_agent(state)

        self.assertTrue(result.get("generated_sql", "").upper().startswith("SELECT"))

    @patch("backend.agents.sql_gen_agent.JsonOutputParser")
    @patch("backend.agents.sql_gen_agent.get_llm")
    @patch("backend.agents.sql_gen_agent.get_sync_session")
    def test_sql_generation_uses_list_params_for_expanding_in(
        self,
        mock_get_sync_session,
        mock_get_llm,
        mock_parser,
    ):
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

        prompt = MagicMock()
        first_chain = MagicMock()
        final_chain = MagicMock()
        prompt.__or__.return_value = first_chain
        first_chain.__or__.return_value = final_chain
        final_chain.invoke.return_value = {
            "sql": "SELECT SUM(amount) AS total_amount FROM mock_employee_transactions",
            "tables_used": ["mock_employee_transactions"],
        }

        state: PipelineState = {
            "user_query": "What is the total transactions amount in last week?",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
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

        with patch("backend.agents.sql_gen_agent.SQL_GEN_PROMPT", prompt):
            result = sql_gen_agent(state)

        execute_call = mock_session.execute.call_args_list[0]
        execute_params = execute_call.args[1]

        self.assertIsInstance(execute_params["tables"], list)
        self.assertIsInstance(execute_params["team_ids"], list)
        self.assertEqual(execute_params["tables"], ["mock_employee_transactions", "mock_transaction_timestamps"])
        self.assertEqual(execute_params["team_ids"], ["team-a"])
        self.assertTrue(result.get("generated_sql", "").upper().startswith("SELECT"))
        self.assertIn("mock_employee_transactions", result.get("sql_tables_used", []))

    @patch("backend.agents.sql_gen_agent.JsonOutputParser")
    @patch("backend.agents.sql_gen_agent.get_llm")
    @patch("backend.agents.sql_gen_agent.get_sync_session")
    def test_sql_generation_handles_dict_columns_metadata(
        self,
        mock_get_sync_session,
        mock_get_llm,
        mock_parser,
    ):
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            RowMock("mock_transactions", [
                {"name": "id", "type": "UUID"},
                {"name": "amount", "type": "DECIMAL"},
            ]),
            RowMock("mock_regions", {
                "columns": [
                    {"name": "region", "type": "VARCHAR"},
                ]
            }),
        ]
        mock_session.execute.return_value = mock_result

        prompt = MagicMock()
        first_chain = MagicMock()
        final_chain = MagicMock()
        prompt.__or__.return_value = first_chain
        first_chain.__or__.return_value = final_chain
        final_chain.invoke.return_value = {
            "sql": "SELECT region, SUM(amount) AS total FROM mock_transactions GROUP BY region",
            "tables_used": ["mock_transactions", "mock_regions"],
        }

        state: PipelineState = {
            "user_query": "Total transaction volume by region",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions", "mock_regions"],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
            "sql_tables_used": []
        }

        with patch("backend.agents.sql_gen_agent.SQL_GEN_PROMPT", prompt):
            result = sql_gen_agent(state)

        self.assertTrue(result.get("generated_sql", "").upper().startswith("SELECT"))
        self.assertIn("mock_transactions", result.get("sql_tables_used", []))
        self.assertIn("mock_regions", result.get("sql_tables_used", []))

if __name__ == '__main__':
    unittest.main()
