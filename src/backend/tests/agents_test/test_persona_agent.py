import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.persona_agent import persona_agent
from backend.agents.state import PipelineState

class TestPersonaAgent(unittest.TestCase):

    def test_persona(self):
        state: PipelineState = {
            "user_query": "What is the status of our systems over the week?",
            "user_id": "test",
            "user_persona": "TECHNICAL",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "SQL_ONLY",
            "routing_decision": {},
            "relevant_tables": ["mock_system_metrics"],
            "generated_sql": "SELECT cpu, mem FROM mock_system_metrics",
            "sql_results": [{"cpu": "90%", "mem": "80%"}],
            "rag_chunks": [],
            "synthesized_context": "The CPU is at 90% today and has remain consistently around the same over the week. Memory is 80% and has been increasing over the week from 50% to 80%.",
            "final_answer": "",
            "chain_of_thought": {}
        }
        
        print("Testing TECHNICAL Persona formatting...")
        result = persona_agent(state)
        
        print("Final Answer:")
        print(result.get("final_answer"))
        
        print("CoT:")
        print(result.get("chain_of_thought"))
        
        self.assertIn("tables_searched", result.get("chain_of_thought", {}))

if __name__ == '__main__':
    unittest.main()
