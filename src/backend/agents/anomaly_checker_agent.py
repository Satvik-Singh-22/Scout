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
anomaly_checker_agent.py

ELI5 (What does this file do?):
Imagine a cautious detective who is handed a list of possible crimes (hypotheses) by the 'anomaly_reasoner'.
This detective actually goes to the crime scene (the live database) to see if the crime really happened!
It runs the test queries the reasoner suggested. If a query fails because of a typo, 
this detective even knows how to fix the typo and try again. 
If the data proves the anomaly is real (like "Yes, errors ARE above 15%"), it sounds the alarm!
"""

from sqlalchemy import text
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from backend.agents.anomaly_reasoner_agent import AnomalyReasonerOutput, AnomalyHypothesis
from backend.db.session import get_sync_session
from backend.agents.llm import get_llm


# ── SQL Fixer Schema ──────────────────────────────────────────────────────────

class SQLFixOutput(BaseModel):
    fixed_sql: str = Field(description="The corrected PostgreSQL SELECT query")


# ── Prompts ───────────────────────────────────────────────────────────────────

FIX_SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL expert. A verification query for an anomaly check failed.
Fix the SQL query so it is valid PostgreSQL and returns exactly 1 row with 1 column named 'metric_value'.

Rules:
- Return ONLY a JSON object.
- Only use SELECT.
- Focus on fixing the reported error while preserving the original logic.
"""),
    ("human", """Failed SQL: {failed_sql}
Error Message: {error_message}
Expected Metric: {metric_label}

Return the fixed SQL in JSON format: {{"fixed_sql": "..."}}""")
])


# ── SQL safety ────────────────────────────────────────────────────────────────

FORBIDDEN = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER",
             "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]


def _is_safe_sql(sql: str) -> tuple[bool, str]:
    upper = sql.upper().strip()
    for kw in FORBIDDEN:
        # Use word boundary check or split
        if kw in upper.split():
            return False, f"Forbidden keyword: {kw}"
    if not upper.startswith("SELECT"):
        return False, "Must be a SELECT statement"
    if "METRIC_VALUE" not in upper:
        return False, "Query must return a column named metric_value"
    return True, ""


# ── Condition evaluator ───────────────────────────────────────────────────────

def _evaluate_condition(condition: str, metric_value: float) -> bool:
    """
    Safely evaluates a condition string like 'metric_value > 0.15'.
    Only allows comparisons — no arbitrary code execution.
    """
    try:
        # Whitelist: only allow these characters in the condition
        allowed_chars = set("metric_value <>=!.0123456789 ")
        if not all(c in allowed_chars for c in condition.replace("metric_value", "")):
            return False
        # Use a safe dict for eval
        return bool(eval(condition, {"__builtins__": {}}, {"metric_value": metric_value}))
    except Exception:
        return False


# ── SQL Fixer ─────────────────────────────────────────────────────────────────

def _fix_sql(failed_sql: str, error_message: str, metric_label: str) -> str | None:
    """Uses LLM to attempt a single fix of a failed verification SQL."""
    llm = get_llm(temperature=0, json_mode=True)
    parser = JsonOutputParser(pydantic_object=SQLFixOutput)
    chain = FIX_SQL_PROMPT | llm | parser

    try:
        print(f"[anomaly_checker] Attempting to fix SQL due to error: {error_message[:100]}")
        res = chain.invoke({
            "failed_sql": failed_sql,
            "error_message": error_message,
            "metric_label": metric_label
        })
        return res.get("fixed_sql") if isinstance(res, dict) else res.fixed_sql
    except Exception as e:
        print(f"[anomaly_checker] SQL Fixer failed: {e}")
        return None


# ── Main agent function ───────────────────────────────────────────────────────

def anomaly_checker_agent(
    reasoner_output: AnomalyReasonerOutput,
    team_id: str,
) -> list[dict]:
    """
    Verifies each hypothesis from anomaly_reasoner_agent.
    Returns only confirmed alerts as dicts matching the Alert model schema.
    """
    if not reasoner_output or not reasoner_output.hypotheses:
        return []

    confirmed_alerts = []

    for hypothesis in reasoner_output.hypotheses:
        sql = hypothesis.verification_sql
        metric_value = None
        attempts = 0
        max_attempts = 2

        while attempts < max_attempts:
            attempts += 1
            
            # 1. Safety check
            is_safe, reason = _is_safe_sql(sql)
            if not is_safe:
                print(f"[anomaly_checker] Blocked unsafe SQL (attempt {attempts}): {reason}")
                break

            # 2. Execute
            try:
                with get_sync_session() as session:
                    result = session.execute(text(sql)).fetchone()
                    if result:
                        row_dict = dict(result._mapping)
                        val = row_dict.get("metric_value")
                        if val is not None:
                            metric_value = float(val)
                            break # Success!
                    else:
                        print(f"[anomaly_checker] Query returned no rows: {hypothesis.title}")
                        break
            except Exception as e:
                print(f"[anomaly_checker] Execution error (attempt {attempts}): {str(e)[:200]}")
                if attempts < max_attempts:
                    # Attempt to fix it
                    fixed = _fix_sql(sql, str(e), hypothesis.metric_label)
                    if fixed:
                        sql = fixed
                        continue
                break

        # 3. If we got a metric value, evaluate condition
        if metric_value is not None:
            confirmed = _evaluate_condition(hypothesis.condition, metric_value)
            print(
                f"[anomaly_checker] '{hypothesis.title}': "
                f"metric_value={metric_value}, condition='{hypothesis.condition}', "
                f"confirmed={confirmed}"
            )

            if confirmed:
                confirmed_alerts.append({
                    "team_id": team_id,
                    "alert_config_id": None,
                    "title": hypothesis.title,
                    "description": (
                        f"{hypothesis.description} "
                        f"Current {hypothesis.metric_label}: {round(metric_value, 4)}. "
                        f"Condition breached: {hypothesis.condition}."
                    ),
                    "severity": hypothesis.severity,
                    "data_snapshot": {
                        "metric_label": hypothesis.metric_label,
                        "metric_value": metric_value,
                        "condition": hypothesis.condition,
                        "verification_sql": sql,
                        "source": "scheduled_query_anomaly_check",
                    }
                })
    print("[DEBUG] ANOMALY CHECKER confirmed_alerts: ", confirmed_alerts)
    return confirmed_alerts
