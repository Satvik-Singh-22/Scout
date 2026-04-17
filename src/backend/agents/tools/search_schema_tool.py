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
search_schema_tool.py — Pinecone-backed schema retrieval tool

ELI5 (What does this file do?):
Instead of dumping all 40 table descriptions into every AI prompt (which wastes tokens),
this tool lets the AI *ask* for exactly the tables it needs, by keyword.
It searches a Pinecone vector database and returns only the 3-5 most relevant
schema definitions — cutting context window usage by ~90%.

The sentence-transformers model is loaded ONCE at module load time (module-level singleton)
so repeated tool calls within a server process do not reload it from disk each time.
"""

import os
import logging
import functools
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton: load the embedding model exactly once per process.
# Using functools.lru_cache on a getter so the model is instantiated on first
# call and reused on every subsequent call within the same process lifetime.
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _get_embed_model():
    """
    Load and cache the sentence-transformers model.
    Called at most once per process — subsequent calls return the cached model.
    """
    from sentence_transformers import SentenceTransformer
    logger.info("[search_schema] Loading sentence-transformers model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("[search_schema] Model loaded and cached.")
    return model


# Similarity threshold: keep moderately close matches to avoid false negatives.
_SIMILARITY_THRESHOLD = 0.1
# Maximum number of candidate results fetched from Pinecone before threshold filtering.
_TOP_K = 5


@tool
def search_schema(search_keyword: str) -> dict:
    """
    Search the Pinecone vector database for table schemas relevant to a given keyword or phrase.

    Use this tool BEFORE generating any SQL query. Pass the core subject of the user's question
    (e.g. "transaction failure rate", "customer complaints", "API error spike") as the
    search_keyword. The tool returns the semantic definitions of the 3-5 most relevant tables,
    which you should use to determine which tables and columns to reference in your SQL.

    If no relevant schemas are found, returns a clear string indicating that no matches were found
    — in which case you should inform the user that no relevant data tables are configured.

    Args:
        search_keyword: A short phrase (1-5 words) describing the data concept the user is asking about.

    Returns:
        Dict with:
          - schema_string: formatted schema text
          - table_names: list of matched table names
    """
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "").strip()
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "").strip()

    if not pinecone_api_key or not pinecone_index_name:
        logger.error("[search_schema] PINECONE_API_KEY or PINECONE_INDEX_NAME not configured.")
        return {"schema_string": "", "table_names": []}

    try:
        from pinecone import Pinecone
    except ImportError:
        logger.error("[search_schema] pinecone-client package is not installed.")
        return {"schema_string": "", "table_names": []}

    try:
        # Retrieve the cached embedding model
        embed_model = _get_embed_model()

        # Embed the search keyword into a vector
        embedding = embed_model.encode(search_keyword, convert_to_numpy=True).tolist()

        # Connect to Pinecone and query for top-k nearest neighbours
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_index_name)

        try:
            response = index.query(
                vector=embedding,
                top_k=_TOP_K,
                include_metadata=True,
            )
        except Exception as exc:
            logger.error("[search_schema] Pinecone query failed: %s", exc, exc_info=True)
            return {"schema_string": "", "table_names": []}

        # Filter matches below the similarity threshold
        matches = response.get("matches", [])
        relevant = [m for m in matches if m.get("score", 0.0) >= _SIMILARITY_THRESHOLD]

        if not relevant:
            logger.info(
                "[search_schema] No matches above threshold %.2f for keyword: '%s'",
                _SIMILARITY_THRESHOLD,
                search_keyword,
            )
            return {"schema_string": "", "table_names": []}

        # Build a formatted output string from surviving matches
        parts = []
        table_names = []
        seen_tables = set()
        for i, match in enumerate(relevant, start=1):
            meta = match.get("metadata", {})
            table_name = meta.get("table_name", "unknown")
            semantic_def = meta.get("semantic_definition", "No description available.")
            score = match.get("score", 0.0)
            parts.append(
                f"[{i}] Table: {table_name} (relevance: {score:.2f})\n"
                f"     Description: {semantic_def}"
            )
            table_key = str(table_name).strip().lower()
            if table_key and table_key not in seen_tables:
                seen_tables.add(table_key)
                table_names.append(str(table_name).strip())

        result_str = "\n---\n".join(parts)
        logger.info(
            "[search_schema] Returning %d relevant schema(s) for keyword: '%s'",
            len(relevant),
            search_keyword,
        )
        return {
            "schema_string": result_str,
            "table_names": table_names,
        }

    except Exception as exc:
        logger.error("[search_schema] Error during schema search: %s", exc, exc_info=True)
        return {"schema_string": "", "table_names": []}
