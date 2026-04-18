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
Context Builder — Formats Prompt Context for Final LLM Generation

Assembles a flat, labeled text block from:
  - Previous conversation context
  - Slack search results (if any)
  - Jira search results (if any)
  - The current question

Keeps the combined block under ~600 tokens by enforcing character
limits on each section.
"""

from backend.agents.slack_jira.config import MAX_HISTORY_CHARS, MAX_CHUNK_CHARS


def build(
    query: str,
    slack_results: list[dict],
    jira_results: list[dict],
    history: list[dict],
) -> str:
    """
    Build a structured prompt context string for the final LLM call.

    Parameters
    ----------
    query : str
        The user's (possibly rewritten) query.
    slack_results : list[dict]
        Reranked Slack messages. Expected keys: ``channel``, ``username``,
        ``date``, ``text``.
    jira_results : list[dict]
        Reranked Jira issues. Expected keys: ``key``, ``status``,
        ``priority``, ``assignee``, ``description``.
    history : list[dict]
        Previous conversation turns as ``{"role": ..., "content": ...}``.

    Returns
    -------
    str
        Formatted context string ready for LLM system/user prompt injection.
    """
    sections: list[str] = []

    # --- Previous context ---------------------------------------------------
    prev_ctx = _build_history_block(history)
    if prev_ctx:
        sections.append(prev_ctx)

    # --- Slack section -------------------------------------------------------
    if slack_results:
        lines = ["[SLACK]"]
        for i, item in enumerate(slack_results, 1):
            channel = item.get("channel", "unknown")
            author = item.get("username", "unknown")
            date = item.get("date", "")
            text = (item.get("text", "") or "")[:MAX_CHUNK_CHARS]
            lines.append(f"{i}. #{channel} | {author} | {date}")
            lines.append(f'   "{text}"')
        sections.append("\n".join(lines))

    # --- Jira section -------------------------------------------------------
    if jira_results:
        lines = ["[JIRA]"]
        for i, item in enumerate(jira_results, 1):
            key = item.get("key", "???")
            status = item.get("status", "unknown")
            priority = item.get("priority", "")
            assignee = item.get("assignee", "unassigned")
            desc = (item.get("description", "") or "")[:MAX_CHUNK_CHARS]
            lines.append(f"{i}. {key} | {status} | {priority} | {assignee}")
            lines.append(f'   "{desc}"')
        sections.append("\n".join(lines))

    # --- Question -----------------------------------------------------------
    sections.append(
        f"Question: {query}\n"
        "Answer based only on the context above. Be concise."
    )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_history_block(history: list[dict]) -> str:
    """
    Extract the last user+assistant pair and format under [PREVIOUS CONTEXT].
    Truncates the assistant turn first if over ``MAX_HISTORY_CHARS``.
    """
    if not history:
        return ""

    last_user = ""
    last_assistant = ""

    # Walk backwards to find the most recent complete turn
    for i in range(len(history) - 1, 0, -1):
        if (
            history[i - 1].get("role", "").upper() == "USER"
            and history[i].get("role", "").upper() == "ASSISTANT"
        ):
            last_user = history[i - 1].get("content", "")
            last_assistant = history[i].get("content", "")
            break

    if not last_user:
        return ""

    # Budget: truncate assistant first
    budget = MAX_HISTORY_CHARS
    if len(last_user) + len(last_assistant) > budget:
        remaining = max(0, budget - len(last_user))
        last_assistant = last_assistant[:remaining] + "…"

    return (
        "[PREVIOUS CONTEXT]\n"
        f"User: {last_user}\n"
        f"Assistant: {last_assistant}"
    )
