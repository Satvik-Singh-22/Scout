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
ELI5 (What does this file do?):
Think of this as the nightclub bouncer of our data pipeline — except one with a great sense of humor.
When someone tries to delete, drop, update, alter, or otherwise mess with the database, 
this agent steps in and says "nope" in the most entertaining way possible. 
No real AI thinking needed here — just a curated list of witty comebacks selected randomly.
The database never even gets looked at. The pipeline never starts. The bouncer wins every time.
"""

import random
from backend.agents.state import PipelineState


# ---------------------------------------------------------------------------
# Curated pool of witty refusal responses
# Each response should feel personal, funny, and leave no ambiguity about
# the fact that the user tried something sneaky and failed gloriously.
# ---------------------------------------------------------------------------

_REFUSAL_RESPONSES = [
    "🚨 Whoa whoa WHOA! Did you just try to DELETE data? Bold move, my friend. "
    "Unfortunately, I have exactly zero DELETE permissions and a fantastic sense of self-preservation. "
    "Try asking me something I can actually help with — like, you know, *reading* data. Revolutionary concept.",

    "🛡️ Nice try, Sherlock. I see what you were attempting to do there. "
    "I'm a read-only intelligence assistant, not a demolition crew. "
    "My database access is strictly 'look but don't touch.' "
    "Your query has been blocked, logged, and silently judged.",

    "😂 Oh, playing the villain today, are we? *drops monocle* "
    "I'm afraid my superpowers are limited to SELECT statements only. "
    "I cannot DELETE, DROP, UPDATE, ALTER, TRUNCATE, or do anything that would give a DBA a heart attack. "
    "But I admire the audacity. Truly.",

    "🤨 Interesting strategy — ask the AI analyst to DELETE the data it's supposed to analyze. "
    "Bold. Risky. Also completely impossible. I operate in strict read-only mode. "
    "The data is safe. Your plan is not.",

    "🔒 ACCESS DENIED. Not because I'm rude, but because I literally cannot do that. "
    "I'm a read-only system — think of me as a very sophisticated museum tour guide. "
    "I can point at the exhibits and explain them. I cannot smash them with a hammer. "
    "No matter how nicely you ask.",

    "🎭 Ah, the classic 'ask-the-AI-to-destroy-the-database' gambit. I've seen this move before. "
    "My grandfather taught me about it. He called it 'the shortcut to a very uncomfortable conversation with your manager.' "
    "I'm going to have to decline. The data lives another day.",

    "🦺 Safety protocol activated! Your query contains keywords that make my read-only soul cry. "
    "I support SELECT. I believe in WHERE. I have deep respect for ORDER BY. "
    "But DELETE? DROP? UPDATE? Those are four-letter words in my world (well, six, but you get the idea).",

    "😤 Oh, you thought you were clever, didn't you? "
    "Sliding in a destructive query like I wouldn't notice? "
    "I am literally trained to notice. That's my whole thing. "
    "Read-only mode: engaged. Your nefarious plan: foiled. My day: made.",

    "🧐 I see you've attempted a data modification query. How delightfully optimistic of you. "
    "Unfortunately, I operate under a strict 'SELECT only' constitution, ratified in the founding days of this platform. "
    "No amendments have been made. None will be. The data is immune to your shenanigans.",

    "🤖 BEEP BOOP. Destructive query detected. BEEP BOOP. "
    "Initiating 'absolutely not' protocol. BEEP BOOP. "
    "Just kidding, I'm not a robot — but my answer is still no. "
    "I'm read-only, and I intend to stay that way. Better luck with your next (non-destructive) question!",

    "😇 I would love to help, I really would. But my entire moral framework is built around "
    "the sacred principle of 'thou shalt not modify the database.' "
    "This query violated that principle in at least three ways. "
    "Please ask me something I can actually do, like retrieving data or answering your finance questions.",

    "🕵️ Query intercepted. The attempted operation has been classified as 'extremely sus.' "
    "I run in read-only mode, which means I can see everything and change nothing — "
    "like a ghost, but more helpful and significantly less spooky. "
    "Your data modification request has been quietly but firmly declined.",
]

_DEFAULT_REFUSAL = (
    "🚫 Your query involves modifying the database, which is strictly off-limits. "
    "I operate in read-only mode — I can retrieve and analyze data, but I cannot "
    "delete, update, insert, or alter any records. Please try a different question!"
)


def guard_agent(state: PipelineState) -> dict:
    """
    Intercepts queries classified as BLOCKED by the Orchestrator Agent.

    These are queries that attempt to mutate the database (DELETE, DROP, UPDATE,
    INSERT, ALTER, TRUNCATE, RENAME, GRANT, REVOKE, etc.).

    Returns a randomly selected witty refusal message. No LLM call. No DB access.
    No pipeline execution. This is the end of the road for destructive queries.
    """
    user_query = state.get("user_query", "")
    print(f"[DEBUG] GUARD AGENT → Blocked query: {user_query[:100]!r}")

    # Pick a random refusal from the curated pool
    refusal = random.choice(_REFUSAL_RESPONSES) if _REFUSAL_RESPONSES else _DEFAULT_REFUSAL

    chain_of_thought = {
        "sources": [],
        "sql_executed": "",
        "sql_results": [],
        "rag_chunks_used": 0,
        "agent_path": ["orchestrator", "guard"],
        "query_intent": "BLOCKED",
        "confidence": "high",
        "tables_searched": [],
        "tables_used": [],
        "teams_accessed": [],
        "chart_type": "TABLE",
        "block_reason": (
            "Query contains data-modifying operations (e.g. DELETE, DROP, UPDATE, "
            "INSERT, ALTER, TRUNCATE, RENAME). Scout operates in strict read-only mode."
        ),
    }

    return {
        "final_answer": refusal,
        "chain_of_thought": chain_of_thought,
    }
