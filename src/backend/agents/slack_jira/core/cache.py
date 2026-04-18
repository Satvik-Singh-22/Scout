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
Slack/Jira Cache — MD5 + LRU + Intent-Aware TTL

Similar in spirit to the main ``query_cache.py`` (exact-match, not
semantic) but with **dual TTLs**: Slack results expire faster (30 min)
because conversations are near-real-time, while Jira results last 2 h.

Cache keys are the MD5 of ``normalised_query + intent``.
"""

import hashlib
import time
from collections import OrderedDict

from backend.agents.slack_jira.config import (
    CACHE_MAX_SIZE,
    CACHE_TTL_SLACK,
    CACHE_TTL_JIRA,
    CACHE_TTL_BOTH,
)

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
_cache: OrderedDict = OrderedDict()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ttl_for_intent(intent: str) -> int:
    """Return the appropriate TTL in seconds for a given intent."""
    return {
        "SLACK": CACHE_TTL_SLACK,
        "JIRA": CACHE_TTL_JIRA,
        "BOTH": CACHE_TTL_BOTH,
    }.get(intent, CACHE_TTL_BOTH)


def _make_key(query: str, intent: str) -> str:
    raw = f"{query.strip().lower()}::{intent.upper()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get(query: str, intent: str) -> dict | None:
    """
    Look up a cached response.

    Returns the full cached result dict on a fresh hit, or ``None``
    on miss / expiry.
    """
    key = _make_key(query, intent)
    if key not in _cache:
        return None

    entry = _cache[key]
    ttl = _ttl_for_intent(entry.get("intent", intent))

    if time.time() - entry["timestamp"] > ttl:
        del _cache[key]
        return None

    _cache.move_to_end(key)
    return entry["result"]


def set(query: str, intent: str, result: dict) -> None:
    """
    Store a result in the cache, applying LRU eviction when full.
    """
    key = _make_key(query, intent)

    if key not in _cache and len(_cache) >= CACHE_MAX_SIZE:
        _cache.popitem(last=False)

    _cache[key] = {
        "result": result,
        "intent": intent.upper(),
        "timestamp": time.time(),
        "original_query": query,
    }
    _cache.move_to_end(key)


def clear() -> None:
    """Evict all entries."""
    _cache.clear()


def stats() -> dict:
    """Cache observability metrics."""
    return {
        "size": len(_cache),
        "max_size": CACHE_MAX_SIZE,
        "ttl_slack": CACHE_TTL_SLACK,
        "ttl_jira": CACHE_TTL_JIRA,
    }
