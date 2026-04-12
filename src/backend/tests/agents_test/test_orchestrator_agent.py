import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.orchestrator_agent import orchestrator_agent
from backend.agents.state import PipelineState
from datetime import date

def test_orchestrator():
    print("Testing Orchestrator Agent Pipeline...\n")

    queries = [
        "What was the total payment volume this week?",
        "What are customers saying about the mobile app's new UI?",
        "Did transaction failures go up when we received complaints about API latency?"
    ]

    for q in queries:
        state: PipelineState = {
            "user_query": q,
            "user_id": "mock-uuid-1",
            "user_persona": "Enterprise_Analyst",
            "team_id": "mock-team-uuid",
            "allowed_team_ids": ["mock-team-uuid"],
            "current_date": date.today().isoformat(),
            "query_intent": "",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }

        print(f"Query: '{q}'")
        try:
            result = orchestrator_agent(state)
            print("Result:")
            print(f"  Intent: {result.get('query_intent')}")
            print(f"  Routing: {result.get('routing_decision')}\n")
        except Exception as e:
            print(f"Error calling orchestrator: {e}\n")

if __name__ == "__main__":
    test_orchestrator()
