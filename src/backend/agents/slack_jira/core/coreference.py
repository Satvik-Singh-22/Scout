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
Coreference Resolver — Lightweight Follow-Up Rewriter

When the user's message contains ambiguous pronouns or references
(``"that"``, ``"it"``, ``"same"``, etc.) this module injects the previous
query into the current one so the main LLM can resolve context naturally.

This is intentionally NOT an LLM call — just cheap string injection.
"""


TRIGGERS = {"that", "those", "it", "same", "instead", "also", "them"}


def rewrite(current_query: str, history: list[dict]) -> str:
    """
    If *current_query* contains a trigger word AND there is a previous
    user turn in *history*, prepend context.  Otherwise return the query
    unchanged.

    Parameters
    ----------
    current_query : str
        The user's current question.
    history : list[dict]
        List of ``{"role": ..., "content": ...}`` message dicts,
        ordered oldest → newest.

    Returns
    -------
    str
        The (possibly rewritten) query string.
    """
    # Strip punctuation so "that?" still matches "that"
    words = set(
        w.strip("?.!,;:\"'()[]{}") for w in current_query.lower().split()
    )
    if not words & TRIGGERS:
        return current_query

    # Walk backwards to find the most recent user turn
    prev = next(
        (h["content"] for h in reversed(history) if h["role"].upper() == "USER"),
        None,
    )
    if not prev:
        return current_query

    return f"[Context: previously asked about '{prev}']\n{current_query}"
