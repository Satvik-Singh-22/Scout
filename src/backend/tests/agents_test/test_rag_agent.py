import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.rag_agent import rag_agent
from backend.agents.state import PipelineState

class TestRagAgent(unittest.TestCase):

    @patch("backend.agents.rag_agent.get_retriever")
    def test_rag_extraction(self, mock_get_retriever):
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever
        
        mock_doc = MagicMock()
        mock_doc.page_content = "This new mobile app UI was slow, buggy and not useful. The alternatives are better than this"
        mock_doc.metadata = {
            "source": "app_store_review",
            "category": "performance",
            "date": "2023-11-01"
        }
        mock_retriever.invoke.return_value = [mock_doc]

        state: PipelineState = {
            "user_query": "What is user viewpoint about the app?",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "RAG_ONLY",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }
        
        print("Testing RAG Agent...")
        result = rag_agent(state)
        chunks = result.get("rag_chunks", [])
        print(chunks)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["category"], "performance")
        self.assertIn("buggy", chunks[0]["content"])
    @patch("backend.agents.rag_agent.get_retriever")
    def test_top_k_review_selection(self, mock_get_retriever):

        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever

        docs = []

        reviews = [
            ("App is extremely slow and buggy", "performance"),
            ("Loading takes forever", "performance"),
            ("Crashes during login", "stability"),
            ("The UI design looks ugly", "design"),
            ("Too expensive compared to competitors", "pricing"),
            ("Performance drops during peak hours", "performance"),
            ("Animations are laggy", "performance"),
            ("Great idea but poorly optimized", "performance")
        ]

        for text, category in reviews:
            doc = MagicMock()
            doc.page_content = text
            doc.metadata = {
                "source": "app_store_review",
                "category": category
            }
            docs.append(doc)

        mock_retriever.invoke.return_value = docs
        state: PipelineState = {
            "user_query": "Why are users unhappy with the app performance?",
            "user_id": "test",
            "user_persona": "EXECUTIVE",
            "team_id": "team-a",
            "allowed_team_ids": ["team-a"],
            "current_date": "2025-01-01",
            "query_intent": "RAG_ONLY",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {}
        }

        result = rag_agent(state)
        chunks = result["rag_chunks"]

        print("Retrieved chunks:", chunks)

        # Ensure documents were returned
        self.assertGreater(len(chunks), 0)

        # Ensure content contains performance related feedback
        categories = [c["category"] for c in chunks]

        self.assertIn("performance", categories)
if __name__ == '__main__':
    unittest.main()
