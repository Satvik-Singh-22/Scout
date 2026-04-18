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
Intent Classifier — Route to SLACK, JIRA, or BOTH

Single LLM call (max_tokens ≈ 5) that decides which external sources
to query.  Uses the existing Groq key pool via ``get_llm()``.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.agents.llm import get_llm

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a routing classifier. Reply with exactly one word:
SLACK — queries explicitly about Slack messages, channels, or conversations
JIRA  — queries explicitly about Jira tickets, bugs, or issues
BOTH  — queries that mention or require both Slack and Jira

If the query mentions Slack explicitly, prefer SLACK.
If it mentions Jira or tickets explicitly, prefer JIRA.
Reply with only: SLACK, JIRA, or BOTH"""),
    ("human", "{query}"),
])


def classify(query: str) -> str:
    """
    Classify a user query into SLACK, JIRA, or BOTH.

    Returns one of the three literal strings.  Defaults to BOTH on any
    unexpected LLM output so that both sources are searched.
    """
    try:
        chain = CLASSIFIER_PROMPT | get_llm(temperature=0) | StrOutputParser()
        raw = chain.invoke({"query": query}).strip().upper()

        # Accept only the three valid labels
        if raw in {"SLACK", "JIRA", "BOTH"}:
            logger.info("[SLACK_JIRA] Intent classified as %s", raw)
            return raw
    except Exception as exc:
        logger.warning("[SLACK_JIRA] Intent classification failed: %s — defaulting to BOTH", exc)

    logger.info("[SLACK_JIRA] Unexpected intent output — defaulting to BOTH")
    return "BOTH"
