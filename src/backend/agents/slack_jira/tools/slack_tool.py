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
Slack Search Tool — Queries Slack's ``search.messages`` API

Uses a ``xoxp-`` user token (set via ``SLACK_USER_TOKEN`` env var).
Returns up to ``RETRIEVE_COUNT`` messages matching the query, each
containing: text, channel name, username, timestamp (human-readable),
and permalink.

If the token is missing the function returns an empty list — the
pipeline continues gracefully without Slack data.
"""

import logging
from backend.vectorstore.chroma_manager import get_slack_retriever

logger = logging.getLogger(__name__)


def search(query: str) -> list[dict]:
    """
    Search Slack messages semantically matching *query* from the vector DB.

    Returns a list of dicts with keys:
      ``text``, ``channel``, ``username``, ``date``, ``permalink``
    """
    if not query:
        return []

    try:
        retriever = get_slack_retriever(k=10) # 10 results are plenty for context
        docs = retriever.invoke(query)
        
        parsed_results = []
        for doc in docs:
            # Reconstruct the expected format from the document metadata
            parsed_results.append({
                "text": doc.page_content,
                "channel": doc.metadata.get("channel", "unknown"),
                "username": doc.metadata.get("username", "unknown"),
                "date": doc.metadata.get("date", "unknown"),
                "permalink": doc.metadata.get("permalink", ""),
            })
            
        return parsed_results
    except Exception as exc:
        logger.warning("[SLACK_JIRA] Semantic Slack search failed: %s", exc)
        return []
