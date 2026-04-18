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
Jira Search Tool — Queries Jira REST API via JQL

Uses Basic Auth (email + API token) against the configured
``JIRA_BASE_URL``.  Builds a safe JQL query by filtering stop-words
from the user's natural-language question and using ``text ~`` operators.

If credentials are missing the function returns ``[]`` — the pipeline
continues gracefully without Jira data.
"""

import logging
from backend.vectorstore.chroma_manager import get_jira_retriever

logger = logging.getLogger(__name__)


def search(query: str) -> list[dict]:
    """
    Search Jira tickets semantically matching *query* from the vector DB.

    Returns a list of dicts with keys:
      ``key``, ``summary``, ``status``, ``priority``, ``assignee``,
      ``description``, ``updated``
    """
    if not query:
        return []

    try:
        retriever = get_jira_retriever(k=10) # 10 tickets are plenty
        docs = retriever.invoke(query)
        
        parsed_results = []
        for doc in docs:
            # Reconstruct the expected format from the document metadata
            parsed_results.append({
                "key": doc.metadata.get("key", "???"),
                "summary": doc.metadata.get("summary", ""),
                "status": doc.metadata.get("status", "unknown"),
                "priority": doc.metadata.get("priority", "unknown"),
                "assignee": doc.metadata.get("assignee", "unassigned"),
                "description": doc.metadata.get("description", ""),
                "updated": doc.metadata.get("updated", ""),
            })
            
        return parsed_results
    except Exception as exc:
        logger.warning("[SLACK_JIRA] Semantic Jira search failed: %s", exc)
        return []
