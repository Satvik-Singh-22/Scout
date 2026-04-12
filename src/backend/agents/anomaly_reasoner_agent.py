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
anomaly_reasoner_agent.py

ELI5 (What does this file do?):
Imagine a highly suspicious auditor looking over the results of a normal report. 
When a user asks for a regular chart, this agent peeks at the same data and asks, 
"Wait, could something be going horribly wrong here behind the scenes?"
It brainstorms up to 2 "Hypotheses" (like, "What if the failure rate is secretly spiking?"). 
It then writes down the exact math test (a SQL query and a condition) needed to prove 
if that bad thing is actually happening. It doesn't run the test; it just builds the theory!
"""

import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy import text

from backend.agents.llm import get_llm
from backend.db.session import get_sync_session


# ── Output schema ────────────────────────────────────────────────────────────

class AnomalyHypothesis(BaseModel):
    title: str = Field(description="Short label e.g. 'Elevated failure rate in SOUTH region'")
    description: str = Field(description="Plain-English explanation of what this anomaly would mean")
    verification_sql: str = Field(description="A valid PostgreSQL SELECT that returns 1 row with 1 column named 'metric_value'")
    condition: str = Field(description="Python-evaluable condition string using 'metric_value' e.g. 'metric_value > 0.15'")
    severity: str = Field(description="Severity: HIGH, MEDIUM, or LOW")
    metric_label: str = Field(description="Human-readable label for the metric e.g. 'failure rate'")


class AnomalyReasonerOutput(BaseModel):
    hypotheses: list[AnomalyHypothesis] = Field(description="List of at most 2 anomaly hypotheses")
    reasoning: str = Field(description="Brief explanation of why these hypotheses were chosen")


# ── Prompt ───────────────────────────────────────────────────────────────────

ANOMALY_REASONER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data anomaly analyst for a banking intelligence system.

Your job is to look at a user's data query, the tables it touches, and a sample of 
the results — then reason about what REAL anomalies could be lurking in this data.

You must return AT MOST 2 anomaly hypotheses. Choose the most impactful ones.
For each hypothesis you must write a PostgreSQL SELECT query that:
  - Returns exactly ONE row with ONE column named 'metric_value'
  - Uses only the tables listed in the schema below
  - Is a read-only SELECT
  - Resolves relative dates using the current date: {current_date}

Available table schemas:
{table_schemas}

Rules for choosing anomalies:
- Focus on anomalies a banking EXECUTIVE would care about: failure rates, spikes, 
  unusual volumes, threshold breaches, sudden drops
- Phrase the condition as a simple comparison: metric_value > X or metric_value < X
- Set the threshold based on what is realistic for banking data
  (e.g. failure rate > 0.15 is HIGH, latency P95 > 2000 is MEDIUM)
- Do NOT invent table or column names not in the schema

Respond ONLY with a JSON object. No explanation outside the JSON.
"""),
    ("human", """User query: {user_query}

Tables involved: {relevant_tables}

Sample of query results (first 10 rows):
{result_sample}

Identify at most 2 anomaly hypotheses:""")
])


# ── Schema fetcher ────────────────────────────────────────────────────────────

def _fetch_table_schemas(table_names: list[str], team_id: str) -> str:
    """
    Fetches columns_metadata from master_config for the given tables.
    Returns a formatted string suitable for injection into the prompt.
    """
    if not table_names:
        return "No table schemas available."

    schemas = []
    try:
        with get_sync_session() as session:
            for table_name in table_names[:2]:  # cap at 2 tables
                result = session.execute(
                    text("""
                        SELECT table_name, semantic_definition, columns_metadata
                        FROM master_config
                        WHERE table_name = :table_name
                        AND team_id = :team_id
                        AND is_active = TRUE
                        LIMIT 1
                    """),
                    {"table_name": table_name, "team_id": team_id}
                ).fetchone()

                if not result:
                    continue

                # Handle row mapping
                row = dict(result._mapping)
                cols = row["columns_metadata"]
                if isinstance(cols, str):
                    cols = json.loads(cols)

                col_lines = "\n".join(
                    f"  - {c['name']} ({c['type']}): {c.get('description', '')}"
                    for c in cols
                )
                schemas.append(
                    f"Table: {row['table_name']}\n"
                    f"Description: {row['semantic_definition']}\n"
                    f"Columns:\n{col_lines}"
                )
    except Exception as e:
        print(f"[anomaly_reasoner_agent] Error fetching schemas: {e}")
        return "Error fetching table schemas."

    return "\n\n".join(schemas) if schemas else "No schemas found."


# ── Main agent function ───────────────────────────────────────────────────────

def anomaly_reasoner_agent(
    user_query: str,
    relevant_tables: list[str],
    sql_results: list[dict],
    team_id: str,
    current_date: str,
) -> AnomalyReasonerOutput | None:
    """
    Reasons about potential anomalies given the query context.
    Returns an AnomalyReasonerOutput or None if reasoning fails.

    Called by scheduler_service.py after pipeline.invoke() completes.
    """
    if not relevant_tables or not sql_results:
        return None

    # Fetch full schemas for the relevant tables
    table_schemas = _fetch_table_schemas(relevant_tables, team_id)

    # Sample the results — first 10 rows, serialised as readable text
    sample = sql_results[:10]
    result_sample = json.dumps(sample, default=str, indent=2)

    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=AnomalyReasonerOutput)
    chain = ANOMALY_REASONER_PROMPT | llm | parser

    try:
        raw = chain.invoke({
            "user_query": user_query,
            "relevant_tables": ", ".join(relevant_tables[:2]),
            "result_sample": result_sample,
            "table_schemas": table_schemas,
            "current_date": current_date,
        })

        if isinstance(raw, dict):
            # The parser should have handled this, but just in case
            hypotheses = [AnomalyHypothesis(**h) for h in raw.get("hypotheses", [])[:2]]
            return AnomalyReasonerOutput(
                hypotheses=hypotheses,
                reasoning=raw.get("reasoning", "")
            )
        print("[DEBUG] ANOMALY REASONER Output: ", raw)
        return raw

    except Exception as e:
        print(f"[anomaly_reasoner_agent] Failed: {e}")
        return None
