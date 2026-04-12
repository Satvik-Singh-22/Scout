import sys
import os
from datetime import date
from pprint import pprint

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.pipeline import pipeline
from backend.agents.state import PipelineState

def test_full_pipeline():
    print("Testing Full Agent Pipeline with Neon Database and RAG...\n")

    queries = [
        "What was the total payment volume this week?",
        "What are customers saying about the mobile app's new UI?",
        "Did transaction failures go up when we received complaints about API latency?"
    ]

    for q in queries:
        # Initialize the state explicitly according to PipelineState TypedDict
        state: PipelineState = {
            "user_query": q,
            "user_id": "00000000-0000-0000-0000-000000000000",
            "user_persona": "ENTERPRISE_ANALYST",
            "team_id": "19429a9e-efdf-4b4b-8839-593f0a965bf4",
            "allowed_team_ids": [
                "19429a9e-efdf-4b4b-8839-593f0a965bf4", # Team A - Payments
                "304f82e2-851b-4975-9475-ce29e56cba2c", # Team B - Operations
                "f83c7f6d-00c2-4053-89ef-151a8d13f93c", # Team C - Customer Support
                "a628ecc9-6c10-43c5-98a4-45868c78cacf", # Team D - KYC
                "364aad12-2bac-4b9e-8a51-317e7eb96ddd"  # Team E - Products
            ],

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

        print(f"\n{'='*80}\nQuery: '{q}'\n{'='*80}")
        try:
            # We invoke the fully compiled StateGraph
            result_state = pipeline.invoke(state)
            
            print("\n--- Pipeline Execution Complete ---")
            print(f"Intent Resolved: {result_state.get('query_intent')}")
            print(f"Tables Relevant: {result_state.get('relevant_tables')}")
            if result_state.get('generated_sql'):
                print(f"SQL Generated:   {result_state.get('generated_sql')}")
                
            print("\n--- Final Answer ---")
            print(result_state.get("final_answer"))
            
            print("\n--- Chain of Thought ---")
            pprint(result_state.get("chain_of_thought"))
            
        except Exception as e:
            print(f"Error calling pipeline: {e}\n")

if __name__ == "__main__":
    test_full_pipeline()
