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
Embedding Reranker — Semantic Re-Scoring for Retrieved Results

Takes raw keyword-matched results from Slack / Jira and reranks them
by cosine similarity against the user query using the same
``all-MiniLM-L6-v2`` model already loaded by the main backend
(via ``chroma_manager.py``).

This bridges the gap between keyword retrieval and semantic relevance
without requiring an ingestion-time embedding pipeline.

The model is loaded lazily on first use to avoid import-time failures
when the HuggingFace cache isn't writable.
"""

import logging
from typing import Optional

from backend.agents.slack_jira.config import MAX_CHUNK_CHARS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded model singleton
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    """
    Lazy-load the SentenceTransformer model on first call.

    Falls back to a lightweight numpy cosine-sim if the model can't be
    loaded (e.g. offline environment, read-only cache).
    """
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("[SLACK_JIRA] Reranker model loaded successfully")
    except Exception as exc:
        logger.warning("[SLACK_JIRA] Could not load SentenceTransformer: %s", exc)
        _model = None

    return _model


def rerank(
    query: str,
    results: list[dict],
    text_key: str,
    top_n: int = 5,
) -> list[dict]:
    """
    Re-score *results* by cosine similarity to *query* and return the
    top-*top_n*.

    Parameters
    ----------
    query : str
        The user's (possibly rewritten) search query.
    results : list[dict]
        Raw results from Slack or Jira, each containing a text field.
    text_key : str
        The dict key within each result that holds the text to embed
        (``"text"`` for Slack, ``"description"`` for Jira).
    top_n : int
        How many results to keep after reranking.

    Returns
    -------
    list[dict]
        The *top_n* most semantically relevant results.
    """
    if not results:
        return []

    model = _get_model()

    # If the model isn't available, just return the first top_n (original order)
    if model is None:
        logger.info("[SLACK_JIRA] Reranker unavailable — returning results in original order")
        return results[:top_n]

    try:
        from sentence_transformers import util

        query_emb = model.encode(query, convert_to_tensor=True)
        texts = [r.get(text_key, "")[:MAX_CHUNK_CHARS] for r in results]
        result_embs = model.encode(texts, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, result_embs)[0]
        ranked = sorted(zip(scores, results), key=lambda x: float(x[0]), reverse=True)
        return [r for _, r in ranked[:top_n]]
    except Exception as exc:
        logger.warning("[SLACK_JIRA] Reranker failed: %s — returning raw results", exc)
        return results[:top_n]
