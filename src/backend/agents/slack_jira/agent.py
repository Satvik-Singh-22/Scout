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

"""
Slack/Jira Agent — Main Orchestrator

This is the top-level entry point that the LangGraph pipeline calls when
``agent_mode == "SLACK_JIRA"``.  It wires together every sub-component:

  1. Cache check
  2. Intent classification  (SLACK / JIRA / BOTH)
  3. Coreference rewrite    (lightweight, no LLM)
  4. Parallel retrieval      (Slack API + Jira REST)
  5. Embedding rerank        (all-MiniLM-L6-v2)
  6. Context building        (flat labeled prompt block)
  7. LLM generation          (Groq via existing key pool)

The function signature matches the LangGraph node contract:
``def slack_jira_agent(state: PipelineState) -> dict``
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.agents.llm import get_llm
from backend.agents.state import PipelineState
from backend.agents.slack_jira.config import FINAL_COUNT
from backend.agents.slack_jira.core import (
    cache,
)
from backend.agents.slack_jira.core import intent_classifier
from backend.agents.slack_jira.core import coreference
from backend.agents.slack_jira.core import reranker
from backend.agents.slack_jira.core import context_builder
from backend.agents.slack_jira.tools import slack_tool, jira_tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Final generation prompt
# ---------------------------------------------------------------------------
_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful enterprise assistant that answers questions
using context retrieved from Slack conversations and Jira tickets.

Rules:
- Answer based ONLY on the provided context.
- Be concise and direct.
- If the context is insufficient, say so honestly rather than guessing.
- Cite source references (Slack channels, Jira ticket keys) where relevant.
- Keep responses under 300 words unless a detailed answer is genuinely needed."""),
    ("human", "{context}"),
])


# ---------------------------------------------------------------------------
# Pipeline node
# ---------------------------------------------------------------------------

def slack_jira_agent(state: PipelineState) -> dict:
    """
    LangGraph node — handles the full Slack/Jira retrieval-generation cycle.

    Reads ``user_query``, ``previous_query``, ``previous_answer`` from
    pipeline state.  Returns ``final_answer`` and ``chain_of_thought``
    updates.
    """
    query = state.get("user_query", "")
    print("[DEBUG] SLACK/JIRA AGENT")

    # ----- 1. Cache check --------------------------------------------------
    cached = cache.get(query, "SLACK_JIRA")
    if cached:
        logger.info("[SLACK_JIRA] Cache HIT for query: %s", query[:80])
        return cached

    # ----- 2. Intent classification ----------------------------------------
    intent = intent_classifier.classify(query)

    # ----- 3. Reconstruct minimal history from state -----------------------
    history = _build_history_from_state(state)

    # ----- 4. Coreference rewrite ------------------------------------------
    resolved_query = coreference.rewrite(query, history)
    logger.info("[SLACK_JIRA] Resolved query: %s", resolved_query[:120])

    # ----- 5. Parallel retrieval (based on intent) -------------------------
    slack_raw: list[dict] = []
    jira_raw: list[dict] = []

    if intent in ("SLACK", "BOTH"):
        slack_raw = slack_tool.search(resolved_query)
    if intent in ("JIRA", "BOTH"):
        jira_raw = jira_tool.search(resolved_query)

    # ----- 6. Embedding rerank ---------------------------------------------
    slack_top = reranker.rerank(resolved_query, slack_raw, "text", top_n=FINAL_COUNT)
    jira_top = reranker.rerank(resolved_query, jira_raw, "description", top_n=FINAL_COUNT)

    # ----- 7. Build context ------------------------------------------------
    context = context_builder.build(resolved_query, slack_top, jira_top, history)

    # ----- 8. Generate answer ----------------------------------------------
    if not slack_top and not jira_top:
        # Nothing retrieved — give a helpful empty-state answer
        answer = (
            "I couldn't find any relevant results from Slack or Jira for your query. "
            "This could be because the search credentials aren't configured yet, "
            "or there are no matching conversations/tickets. "
            "Try rephrasing your question or checking the Slack/Jira integration settings."
        )
    else:
        chain = _ANSWER_PROMPT | get_llm(temperature=0) | StrOutputParser()
        answer = chain.invoke({"context": context}).strip()

    # ----- 9. Build Chain of Thought ---------------------------------------
    cot = {
        "sources": [],
        "sql_executed": "",
        "sql_results": [],
        "rag_chunks_used": 0,
        "agent_path": ["orchestrator", "slack_jira"],
        "query_intent": f"SLACK_JIRA:{intent}",
        "confidence": "high" if (slack_top or jira_top) else "low",
        "tables_searched": [],
        "tables_used": [],
        "teams_accessed": state.get("allowed_team_ids", []),
        "chart_type": "TABLE",
        "slack_jira_detail": {
            "sub_intent": intent,
            "query_resolved": resolved_query,
            "slack_sources": [s.get("channel", "") for s in slack_top],
            "jira_sources": [j.get("key", "") for j in jira_top],
            "slack_count": len(slack_raw),
            "jira_count": len(jira_raw),
            "slack_reranked": len(slack_top),
            "jira_reranked": len(jira_top),
        },
    }

    result = {
        "final_answer": answer,
        "chain_of_thought": cot,
    }

    # ----- 10. Cache and return --------------------------------------------
    cache.set(query, intent, result)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_history_from_state(state: PipelineState) -> list[dict]:
    """
    Reconstruct a minimal conversation history list from the pipeline
    state fields that ``chat.py`` already populates.
    """
    history: list[dict] = []

    prev_q = state.get("previous_query", "")
    prev_a = state.get("previous_answer", "")

    if prev_q:
        history.append({"role": "USER", "content": prev_q})
    if prev_a:
        history.append({"role": "ASSISTANT", "content": prev_a})

    return history
