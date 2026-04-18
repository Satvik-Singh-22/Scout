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
Slack/Jira Agent — Configuration Constants

All tuneable knobs in one place.  API tokens are pulled from environment
variables; everything else is a sensible default that can be overridden
via env vars if needed.
"""

import os

# ---------------------------------------------------------------------------
# API Credentials (set in .env — gracefully None when missing)
# ---------------------------------------------------------------------------
SLACK_USER_TOKEN: str | None = os.getenv("SLACK_USER_TOKEN")
JIRA_BASE_URL: str | None = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL: str | None = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN: str | None = os.getenv("JIRA_API_TOKEN")

# ---------------------------------------------------------------------------
# Cache TTLs (seconds)
# ---------------------------------------------------------------------------
CACHE_TTL_SLACK: int = 1800   # 30 min — Slack data is near-real-time
CACHE_TTL_JIRA: int = 7200    # 2 hours — Jira tickets change less frequently
CACHE_TTL_BOTH: int = 1800    # 30 min — Slack freshness drives the combined TTL
CACHE_MAX_SIZE: int = 200

# ---------------------------------------------------------------------------
# Retrieval tuning
# ---------------------------------------------------------------------------
RETRIEVE_COUNT: int = 15      # fetch this many raw results from each API
FINAL_COUNT: int = 5          # keep top-N after embedding rerank
MAX_CHUNK_CHARS: int = 300    # truncate individual result text to this length

# ---------------------------------------------------------------------------
# History / context limits
# ---------------------------------------------------------------------------
MAX_HISTORY_TURNS: int = 3
MAX_HISTORY_CHARS: int = 800
