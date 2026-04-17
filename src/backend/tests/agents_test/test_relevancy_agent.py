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

from backend.agents.relevancy_agent import (
    relevancy_agent,
    _extract_keywords,
    _build_search_keyword,
    _has_valid_schema_search_results,
    _extract_table_names,
    _normalize_tool_result,
)
from backend.agents.tools.search_schema_tool import _SIMILARITY_THRESHOLD
from backend.agents.state import PipelineState

class RowMock:
    def __init__(self, table_name, semantic_definition):
        self.table_name = table_name
        self.semantic_definition = semantic_definition

class TestRelevancyAgent(unittest.TestCase):

    def test_similarity_threshold_is_not_overly_strict(self):
        self.assertLessEqual(_SIMILARITY_THRESHOLD, 0.55)

    def test_has_valid_schema_search_results(self):
        self.assertTrue(_has_valid_schema_search_results("[1] Table: mock_transactions"))
        self.assertFalse(_has_valid_schema_search_results("No relevant schemas found for keyword"))
        self.assertFalse(_has_valid_schema_search_results("Schema search unavailable: Pinecone is not configured."))

    def test_extract_keywords(self):
        keywords = _extract_keywords("Show transaction failures and payment complaints from last week")
        self.assertIn("transaction", keywords)
        self.assertIn("failures", keywords)
        self.assertIn("payment", keywords)
        self.assertIn("complaints", keywords)
        self.assertNotIn("last", keywords)
        self.assertNotIn("week", keywords)

    def test_build_search_keyword_compacts_query(self):
        keyword = _build_search_keyword("What is the total transaction volume this month, broken down by region?")
        self.assertTrue(len(keyword.split()) <= 2)
        self.assertNotEqual(
            keyword,
            "What is the total transaction volume this month, broken down by region?",
        )

    def test_extract_table_names(self):
        raw = "[1] Table: mock_transactions (relevance: 0.88)\n---\n[2] Table: mock_regions (relevance: 0.71)"
        self.assertEqual(_extract_table_names(raw), ["mock_transactions", "mock_regions"])

    def test_normalize_tool_result_stringified_dict(self):
        raw = '{"schema_string": "[1] Table: mock_transactions", "table_names": ["mock_transactions"]}'
        normalized = _normalize_tool_result(raw)
        self.assertEqual(normalized["schema_string"], "[1] Table: mock_transactions")
        self.assertEqual(normalized["table_names"], ["mock_transactions"])

    @patch("backend.agents.relevancy_agent._llm_search_keyword")
    @patch("backend.agents.relevancy_agent._fallback_schema_search")
    @patch("backend.agents.relevancy_agent.search_schema")
    def test_relevancy_uses_fallback_when_pinecone_empty(
        self,
        mock_search_schema,
        mock_fallback,
        mock_llm_keyword,
    ):
        mock_llm_keyword.return_value = "payment transactions"
        mock_search_schema.invoke.return_value = {"schema_string": "", "table_names": []}
        mock_fallback.return_value = {
            "schema_string": "[1] Table: mock_transactions (relevance: fallback)\n     Description: payment transactions",
            "table_names": ["mock_transactions"],
        }

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

        result = relevancy_agent(state)

        self.assertEqual(result.get("relevant_tables"), ["mock_transactions"])
        self.assertIn("Table: mock_transactions", result.get("synthesized_context", ""))
        mock_search_schema.invoke.assert_called_once_with({"search_keyword": "payment transactions"})
        mock_fallback.assert_called_once()

    @patch("backend.agents.relevancy_agent.get_sync_session")
    def test_fallback_db_search_returns_candidate_rows(self, mock_get_sync_session):
        mock_session = MagicMock()
        mock_get_sync_session.return_value.__enter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            RowMock("mock_transactions", "Records of all payment transactions including amounts and status"),
            RowMock("mock_customer_feedback", "Customer feedback and reviews"),
        ]
        mock_session.execute.return_value = mock_result

        from backend.agents.relevancy_agent import _fallback_schema_search

        state = {
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "previous_tables_used": [],
        }
        result = _fallback_schema_search(state, "payment transactions")

        self.assertIn("mock_transactions", result["schema_string"])
        self.assertIn("mock_customer_feedback", result["schema_string"])
        self.assertIn("mock_transactions", result["table_names"])
        self.assertIn("mock_customer_feedback", result["table_names"])

if __name__ == '__main__':
    unittest.main()
