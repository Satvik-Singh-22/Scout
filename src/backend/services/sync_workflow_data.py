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

import logging
import httpx
from datetime import datetime, timezone, timedelta
from base64 import b64encode
from langchain_core.documents import Document

from backend.agents.slack_jira.config import (
    SLACK_USER_TOKEN,
    JIRA_BASE_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    MAX_CHUNK_CHARS,
)
from backend.vectorstore.chroma_manager import get_slack_vectorstore, get_jira_vectorstore

logger = logging.getLogger(__name__)

SLACK_SEARCH_URL = "https://slack.com/api/search.messages"

def sync_workflow_data():
    """Run the synchronization for Slack and Jira into ChromaDB."""
    logger.info("Starting workflow data sync to ChromaDB for the last 1 day.")
    _sync_slack()
    _sync_jira()
    logger.info("Workflow data sync complete.")


def _sync_slack():
    if not SLACK_USER_TOKEN:
        logger.warning("SLACK_USER_TOKEN not set. Skipping Slack sync.")
        return

    vectorstore = get_slack_vectorstore()
    
    # We query for messages from yesterday onwards.
    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    query = f"after:{yesterday_str}"

    params = {
        "query": query,
        "count": 100,  # Fetch up to 100 recent messages
        "sort": "timestamp",
    }
    headers = {"Authorization": f"Bearer {SLACK_USER_TOKEN}"}

    docs = []
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(SLACK_SEARCH_URL, params=params, headers=headers)
        
        data = response.json()
        if not data.get("ok"):
            logger.error(f"Slack sync failed: {data.get('error')}")
            return
            
        messages = data.get("messages", {}).get("matches", [])
        
        for msg in messages:
            ts = msg.get("ts", "")
            try:
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
                readable_date = dt.strftime("%Y-%m-%d %H:%M UTC")
            except (ValueError, TypeError, OSError):
                readable_date = ts

            text = (msg.get("text", "") or "")[:MAX_CHUNK_CHARS]
            
            # Use permalink as the document ID
            doc_id = msg.get("permalink", str(ts))

            metadata = {
                "id": doc_id,
                "channel": msg.get("channel", {}).get("name", "unknown"),
                "username": msg.get("username", "unknown"),
                "date": readable_date,
                "permalink": msg.get("permalink", ""),
            }

            # Embed the text content
            docs.append(Document(page_content=text, metadata=metadata, id=doc_id))
            
        if docs:
            # We use ids to prevent duplicating existing documents that are re-fetched.
            ids = [d.metadata["id"] for d in docs]
            vectorstore.add_documents(documents=docs, ids=ids)
            logger.info(f"Synced {len(docs)} Slack messages to ChromaDB.")
        else:
            logger.info("No new Slack messages found.")

    except Exception as e:
        logger.error(f"Error during Slack sync: {e}")


def _sync_jira():
    if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        logger.warning("Jira credentials missing. Skipping Jira sync.")
        return

    vectorstore = get_jira_vectorstore()
    
    # Query for tickets updated in the last 1 day
    jql = 'updated >= -1d ORDER BY updated DESC'

    url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/3/search/jql"
    creds = b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Accept": "application/json",
    }
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status,priority,assignee,description,updated",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params, headers=headers)
        
        response.raise_for_status()
        issues = response.json().get("issues", [])
        
        docs = []
        for issue in issues:
            fields = issue.get("fields", {})
            description_raw = fields.get("description")
            
            if isinstance(description_raw, dict):
                description = _adf_to_text(description_raw)
            elif isinstance(description_raw, str):
                description = description_raw
            else:
                description = ""

            assignee_obj = fields.get("assignee") or {}
            status_obj = fields.get("status") or {}
            priority_obj = fields.get("priority") or {}

            key = issue.get("key", "???")
            summary = fields.get("summary", "")
            
            # Combine summary and description for the embedded search space
            content = f"Title/Summary: {summary}\n\nDescription: {description}"
            content = content[:MAX_CHUNK_CHARS]
            
            metadata = {
                "id": key,
                "key": key,
                "summary": summary,
                "status": status_obj.get("name", "unknown"),
                "priority": priority_obj.get("name", ""),
                "assignee": assignee_obj.get("displayName", "unassigned"),
                "description": description[:300], # Keep description shorter in metadata
                "updated": fields.get("updated", ""),
            }

            docs.append(Document(page_content=content, metadata=metadata, id=key))
            
        if docs:
            ids = [d.metadata["id"] for d in docs]
            vectorstore.add_documents(documents=docs, ids=ids)
            logger.info(f"Synced {len(docs)} Jira tickets to ChromaDB.")
        else:
            logger.info("No Jira tickets found for sync.")

    except Exception as e:
        logger.error(f"Error during Jira sync: {e}")

def _adf_to_text(adf: dict) -> str:
    """Atlassian Document Format → plain text converter."""
    parts = []
    def _walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []):
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return " ".join(parts)
