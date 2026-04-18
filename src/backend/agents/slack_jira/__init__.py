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
Slack/Jira Agent — retrieves context from Slack conversations and Jira
tickets, reranks with embeddings, and generates answers.

Activated when the user toggles to "Slack/Jira" mode in the UI.
"""

from backend.agents.slack_jira.agent import slack_jira_agent  # noqa: F401
