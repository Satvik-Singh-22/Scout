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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.state import PipelineState

class TestSynthesisAgent(unittest.TestCase):

    def test_synthesis(self):
        state: PipelineState = {
            "user_query": "Did complaints rise when transactions failed?",
            "user_id": "test",
            "user_persona": "TECHNICAL",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "HYBRID",
            "routing_decision": {},
            "relevant_tables": ["mock_transactions"],
            "generated_sql": "SELECT COUNT(*) FROM mock_transactions WHERE status='FAILED'",
            "sql_results": [{"count": 45}],
            "rag_chunks": ["Customers reported huge latency spikes today."],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }
        
        print("Testing Synthesis Agent...")
        result = synthesis_agent(state)
        
        context = result.get("synthesized_context", "")
        print(context)
        
        # Test will query Groq locally using LLM, it should reference '45' and 'latency'.
        self.assertTrue(len(context) > 10)

if __name__ == '__main__':
    unittest.main()
