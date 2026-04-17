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
query_cache.py — In-Memory LRU + TTL Exact-Match SQL Cache

ELI5 (What does this file do?):
Before calling the expensive AI (Groq) to generate SQL, we first check this "notebook" to see
if we've already answered this exact question recently. If yes, we return the saved answer instantly —
no AI call needed. The notebook has a max size (500 entries) and a 24-hour expiry so it never
grows stale. When full, it throws out the least-recently-used entry first (LRU eviction).

Design notes:
- Exact-match ONLY (MD5 hash of normalised query). Intentionally NOT semantic similarity.
  This prevents returning "last week" SQL when the user asks for "this week" — temporal
  precision must be preserved.
- Uses OrderedDict for O(1) LRU eviction without any additional data structures.
- No external dependencies — only hashlib, time, and collections from the Python stdlib.
- Thread-safe for CPython (GIL protects dict operations), but not for truly concurrent
  multi-threaded access. For the current single-process Uvicorn deploy this is sufficient.
"""

import hashlib
import time
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS: int = 86400   # 24 hours
CACHE_MAX_SIZE: int = 500

# ---------------------------------------------------------------------------
# Cache storage — OrderedDict preserves insertion order for LRU eviction
# ---------------------------------------------------------------------------
_cache: OrderedDict = OrderedDict()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(query: str) -> str:
    """
    Normalise a raw query string for consistent cache key generation.

    Steps:
      1. Strip leading/trailing whitespace
      2. Convert to lowercase
      3. Collapse multiple internal spaces into a single space
    """
    stripped = query.strip()
    lowered = stripped.lower()
    collapsed = " ".join(lowered.split())
    return collapsed


def _hash_query(normalized_query: str) -> str:
    """Return the MD5 hex digest of a normalised query string."""
    return hashlib.md5(normalized_query.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_cached_sql(query: str) -> "str | None":
    """
    Look up a previously generated SQL string for the given natural-language query.

    Returns the cached SQL string if a fresh (< 24h old) exact match exists,
    or None if the cache misses or the entry has expired.

    Args:
        query: The raw natural-language query string (not normalised yet).

    Returns:
        Cached SQL string, or None on a miss/expiry.
    """
    normalized = _normalize(query)
    hash_key = _hash_query(normalized)

    if hash_key not in _cache:
        return None

    entry = _cache[hash_key]

    # TTL check — evict expired entries
    if time.time() - entry["timestamp"] > CACHE_TTL_SECONDS:
        del _cache[hash_key]
        return None

    # Cache HIT — move to end to mark as most-recently-used
    _cache.move_to_end(hash_key)
    return entry["sql"]


def set_cached_sql(query: str, sql: str) -> None:
    """
    Store a generated SQL string in the cache, keyed by the normalised query.

    Applies LRU eviction if the cache is at capacity before inserting a new entry.
    The operation is idempotent — calling with the same query updates the timestamp.

    Args:
        query: The raw natural-language query string.
        sql:   The generated SQL string to cache.
    """
    normalized = _normalize(query)
    hash_key = _hash_query(normalized)

    # LRU eviction: only evict if this is a genuinely new key and we're at capacity
    if hash_key not in _cache and len(_cache) >= CACHE_MAX_SIZE:
        # Remove the oldest (leftmost) entry
        _cache.popitem(last=False)

    _cache[hash_key] = {
        "sql": sql,
        "timestamp": time.time(),
        "original_query": query,   # stored verbatim for debugging/introspection
    }
    # Move to end — marks as most-recently-used
    _cache.move_to_end(hash_key)


def clear_cache() -> None:
    """
    Evict all entries from the cache.

    Useful for testing and manual resets. After calling this, the next query
    will always result in a cache miss and trigger a fresh Groq API call.
    """
    _cache.clear()


def get_cache_stats() -> dict:
    """
    Return current cache observability metrics.

    Returns:
        dict with keys:
          - size:        number of entries currently in the cache
          - max_size:    configured maximum capacity (CACHE_MAX_SIZE)
          - ttl_seconds: configured TTL in seconds (CACHE_TTL_SECONDS)
    """
    return {
        "size": len(_cache),
        "max_size": CACHE_MAX_SIZE,
        "ttl_seconds": CACHE_TTL_SECONDS,
    }
