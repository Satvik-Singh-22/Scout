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

import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.persona_agent import persona_agent


class TestNoDataGuards(unittest.TestCase):
    def test_synthesis_reports_no_schema_available(self):
        state = {
            "user_query": "total volume by region",
            "sql_results": [],
            "rag_chunks": [],
            "generated_sql": "NO_SCHEMA_AVAILABLE",
            "execution_error": "",
            "sql_error": "",
        }
        result = synthesis_agent(state)
        self.assertIn("No relevant database tables were found", result.get("synthesized_context", ""))

    def test_synthesis_reports_execution_error(self):
        state = {
            "user_query": "total volume by region",
            "sql_results": [],
            "rag_chunks": [],
            "generated_sql": "SELECT x FROM y",
            "execution_error": "column region does not exist",
            "sql_error": "",
        }
        result = synthesis_agent(state)
        self.assertIn("SQL execution failed", result.get("synthesized_context", ""))
        self.assertIn("column region does not exist", result.get("synthesized_context", ""))

    @patch("backend.agents.persona_agent.get_llm")
    def test_persona_short_circuits_no_data_without_llm(self, mock_get_llm):
        state = {
            "user_query": "total volume by region",
            "user_persona": "EXECUTIVE",
            "query_intent": "SQL_ONLY",
            "relevant_tables": [],
            "sql_tables_used": [],
            "sql_results": [],
            "rag_chunks": [],
            "generated_sql": "NO_SCHEMA_AVAILABLE",
            "allowed_team_ids": ["team-a"],
            "synthesized_context": "No relevant database tables were found for this query.",
        }
        result = persona_agent(state)
        self.assertIn("wasn't able to retrieve data", result.get("final_answer", ""))
        self.assertEqual(result.get("chain_of_thought", {}).get("confidence"), "low")
        mock_get_llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
