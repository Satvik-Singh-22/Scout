"""
test_chat_workflow.py
=====================
Standalone integration test for the Banquoite agent pipeline.

Mirrors exactly what `backend/api/chat.py` does in its `generate()` closure:
  1. Build initial_state using the frozen PipelineState schema
  2. Call pipeline.invoke(initial_state)
  3. Validate key state fields at each logical stage
  4. Simulate the SSE word-streaming that chat.py does

Run from the project root:
    python -m backend.tests.test_chat_workflow

Or directly (adds project root to path automatically):
    python backend/tests/test_chat_workflow.py

Requirements: .env must be present at backend/.env with DATABASE_URL and GROQ_API_KEY set.
"""

import os
import sys
import json
import time
import textwrap
from datetime import date
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is on the path regardless of how this is invoked
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env before importing anything from backend
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, "backend", ".env"))

# ---------------------------------------------------------------------------
# Colour helpers (no extra deps)
# ---------------------------------------------------------------------------
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
DIM     = "\033[2m"


def hdr(text: str, colour: str = CYAN) -> None:
    width = 80
    print(f"\n{colour}{BOLD}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{RESET}")


def sub(text: str, colour: str = YELLOW) -> None:
    print(f"\n{colour}{BOLD}── {text} ──{RESET}")


def ok(label: str) -> None:
    print(f"  {GREEN}✓  {label}{RESET}")


def fail(label: str) -> None:
    print(f"  {RED}✗  {label}{RESET}")


def info(label: str, value: Any = "") -> None:
    val_str = str(value)
    if len(val_str) > 120:
        val_str = val_str[:117] + "..."
    print(f"  {DIM}{label}:{RESET} {val_str}")


# ---------------------------------------------------------------------------
# Demo personas / users — mirrors seed_governance.py demo accounts
# ---------------------------------------------------------------------------
# These team UUIDs must match what was seeded by seed_master_config.py.
# We read a few from the test_pipeline.py that's already in the repo.
TEAM_A_ID = "19429a9e-efdf-4b4b-8839-593f0a965bf4"  # Payments
TEAM_B_ID = "304f82e2-851b-4975-9475-ce29e56cba2c"  # Operations
TEAM_C_ID = "f83c7f6d-00c2-4053-89ef-151a8d13f93c"  # Risk
TEAM_D_ID = "a628ecc9-6c10-43c5-98a4-45868c78cacf"  # Customer
TEAM_E_ID = "364aad12-2bac-4b9e-8a51-317e7eb96ddd"  # Finance

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------
TEST_CHATROOM_ID = "259e8113-8484-4e0e-8f01-f807e895b535"

DEMO_USERS = {
    "analyst_a": {
        "user_id":        "aaaa0000-0000-0000-0000-000000000001",
        "user_persona":   "EXECUTIVE",
        "team_id":        TEAM_A_ID,
        "allowed_team_ids": [TEAM_A_ID],          # ANALYST — own team only
    },
    "analyst_b": {
        "user_id":        "bbbb0000-0000-0000-0000-000000000002",
        "user_persona":   "TECHNICAL",
        "team_id":        TEAM_B_ID,
        "allowed_team_ids": [TEAM_B_ID],
    },
    "enterprise": {
        "user_id":        "eeee0000-0000-0000-0000-000000000003",
        "user_persona":   "TECHNICAL",
        "team_id":        TEAM_A_ID,
        "allowed_team_ids": [TEAM_A_ID, TEAM_B_ID],  # Cross-team access
    },
}


# ---------------------------------------------------------------------------
# Test scenarios — the 5 demo queries from Master Context §12
# ---------------------------------------------------------------------------
TEST_SCENARIOS = [
    # {
    #     "id":        "UC1",
    #     "desc":      "Use Case 1 — Understand what changed (EXECUTIVE, Team A)",
    #     "user":      "analyst_a",
    #     "query":     "Why did transaction failures spike last Tuesday?",
    #     "expect_intent": "SQL_ONLY",
    #     "expect_tables_like": ["mock_transactions", "mock_failed_transactions",
    #                            "mock_payment_events"],  # at least one
    #     "expect_sql_keywords": ["SELECT", "failed", "transaction"],
    # },
    # {
    #     "id":        "UC2",
    #     "desc":      "Use Case 2 — Compare regions (TECHNICAL, Team A)",
    #     "user":      "analyst_a",
    #     "query":     "Compare successful vs failed payments in the North vs South region this month",
    #     "expect_intent": "SQL_ONLY",
    #     "expect_tables_like": ["mock_transactions"],
    #     "expect_sql_keywords": ["SELECT", "region", "status"],
    # },
    # {
    #     "id":        "UC3",
    #     "desc":      "Use Case 3 — Breakdown by merchant category (EXECUTIVE, Team A)",
    #     "user":      "analyst_a",
    #     "query":     "Show me the breakdown of total transaction volume by merchant category this quarter",
    #     "expect_intent": "SQL_ONLY",
    #     "expect_tables_like": ["mock_transactions", "mock_merchant_categories"],
    #     "expect_sql_keywords": ["SELECT", "merchant"],
    # },
    # {
    #     "id":        "UC4",
    #     "desc":      "Use Case 4 — Cross-team: system health + payments (Enterprise Analyst)",
    #     "user":      "enterprise",
    #     "query":     "Give me a summary of system health and payment performance for this week",
    #     "expect_intent": "SQL_ONLY",
    #     "expect_tables_like": ["mock_transactions", "mock_api_gateway_logs"],
    #     "expect_sql_keywords": ["SELECT"],
    # },
    # {
    #     "id":        "UC6",
    #     "desc":      "Use Case 6 — Follow-up: 'Break that down by merchant'",
    #     "user":      "analyst_a",
    #     "query":     "Break that down by merchant category",
    #     "previous_query": "Why did transaction failures spike last Tuesday?",
    #     "previous_answer": "There were 45 failures related to recurring payments yesterday...",
    #     "previous_sql": "SELECT count(*) FROM mock_transactions WHERE status = 'failed' AND date_trunc('day', created_at) = '2025-01-14'",
    #     "previous_tables_used": ["mock_transactions"],
    #     "expect_intent": "SQL_ONLY",
    #     "expect_tables_like": ["mock_transactions", "mock_merchant_categories"],
    #     "expect_sql_keywords": ["SELECT", "merchant", "failed", "GROUP BY"],
    # },
    {
        "id":        "UC7",
        "desc":      "Use Case 7 — GENERAL: system capabilities question",
        "user":      "analyst_a",
        "query":     "What can you do?",
        "expect_intent": "GENERAL",
        "expect_tables_like": [],
        "expect_sql_keywords": [],
    },
    {
        "id":        "UC8",
        "desc":      "Use Case 8 — SCHEMA_LOOKUP: what tables exist for payments",
        "user":      "analyst_a",
        "query":     "What tables do you have about payments?",
        "expect_intent": "SCHEMA_LOOKUP",
        "expect_tables_like": [],   # schema agent populates relevant_tables, not via relevancy
        "expect_sql_keywords": [],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_initial_state(user_key: str, scenario: dict) -> dict:
    """
    Replicates exactly what chat.py's generate() closure builds.
    This is the frozen PipelineState definition from the Master Context.
    """
    u = DEMO_USERS[user_key]
    return {
        "user_query":       scenario["query"],
        "user_id":          u["user_id"],
        "user_persona":     u["user_persona"],
        "team_id":          u["team_id"],
        "allowed_team_ids": u["allowed_team_ids"],
        "current_date":     date.today().isoformat(),
        # --- fields the pipeline fills in ---
        "query_intent":        "",
        "routing_decision":    {},
        "relevant_tables":     [],
        "generated_sql":       "",
        "sql_results":         [],
        "rag_chunks":          [],
        "synthesized_context": "",
        "final_answer":        "",
        "chain_of_thought":    {},
        "sql_tables_used":     [],
        "sql_retry_count":     0,
        "sql_error":           "",
        # --- multi-turn context ---
        "previous_query":       scenario.get("previous_query", ""),
        "previous_answer":      scenario.get("previous_answer", ""),
        "previous_sql":         scenario.get("previous_sql", ""),
        "previous_tables_used": scenario.get("previous_tables_used", []),
    }


def simulate_sse_stream(final_answer: str) -> None:
    """Simulates the SSE word-by-word streaming from chat.py."""
    words = final_answer.split(" ")
    print(f"\n  {DIM}[SSE stream simulation]{RESET}")
    sys.stdout.write("  ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        # Emit an SSE event (just print here instead of yield)
        _event = json.dumps({"type": "chunk", "content": chunk})
        sys.stdout.write(word + " ")
        sys.stdout.flush()
        time.sleep(0.005)  # tiny delay so output is visible but fast
    print()   # newline after streaming


def validate_result(scenario: dict, result: dict) -> tuple[int, int]:
    """
    Runs assertions on the pipeline result state.
    Returns (passed, total) counts.
    """
    passed = 0
    total  = 0

    sub("Validation checks")

    # 1. final_answer is non-empty
    total += 1
    if result.get("final_answer", "").strip():
        ok("final_answer is non-empty")
        passed += 1
    else:
        fail("final_answer is EMPTY — pipeline did not produce an answer")

    # 2. query_intent is one of the three valid values
    total += 1
    intent = result.get("query_intent", "")
    if intent in {"SQL_ONLY", "RAG_ONLY", "HYBRID", "GENERAL", "SCHEMA_LOOKUP"}:
        ok(f"query_intent is valid: '{intent}'")
        passed += 1
    else:
        fail(f"query_intent is invalid or empty: '{intent}'")

    # 3. Expected intent (if specified)
    expected_intent = scenario.get("expect_intent")
    if expected_intent:
        total += 1
        # For UC5 we accept HYBRID too
        if scenario["id"] == "UC5":
            if intent in {"RAG_ONLY", "HYBRID"}:
                ok(f"Intent matches expected (RAG_ONLY or HYBRID): '{intent}'")
                passed += 1
            else:
                fail(f"Expected RAG_ONLY or HYBRID, got '{intent}'")
        else:
            if intent == expected_intent:
                ok(f"Intent matches expected: '{intent}'")
                passed += 1
            else:
                fail(f"Expected '{expected_intent}', got '{intent}'")

    # 4. For SQL queries — at least one relevant table returned
    if scenario.get("expect_tables_like"):
        total += 1
        relevant = result.get("relevant_tables", [])
        matched = any(t in relevant for t in scenario["expect_tables_like"])
        if matched:
            ok(f"relevant_tables contains at least one expected table: {relevant}")
            passed += 1
        else:
            fail(f"relevant_tables {relevant} did not contain any of "
                 f"{scenario['expect_tables_like']}")

    # 5. For SQL queries — SQL was generated and contains expected keywords
    if scenario.get("expect_sql_keywords"):
        sql = result.get("generated_sql", "")
        total += 1
        if sql and not sql.startswith("BLOCKED") and not sql.startswith("EXECUTION_ERROR"):
            ok(f"generated_sql is present and not blocked")
            passed += 1
        else:
            fail(f"generated_sql missing or blocked: '{sql[:80]}'")

        total += 1
        sql_upper = sql.upper()
        kw_found = [kw for kw in scenario["expect_sql_keywords"] if kw.upper() in sql_upper]
        if len(kw_found) == len(scenario["expect_sql_keywords"]):
            ok(f"SQL contains expected keywords: {kw_found}")
            passed += 1
        else:
            missing = [kw for kw in scenario["expect_sql_keywords"] if kw.upper() not in sql_upper]
            fail(f"SQL missing keywords: {missing}")

    # 6. chain_of_thought is present and has required keys
    total += 1
    cot = result.get("chain_of_thought", {})
    required_cot_keys = {"agent_path", "query_intent", "confidence", "tables_used"}
    missing_keys = required_cot_keys - set(cot.keys())
    if not missing_keys:
        ok("chain_of_thought has all required keys")
        passed += 1
    else:
        fail(f"chain_of_thought missing keys: {missing_keys}")

    # 7. sql_results are rows (list) if SQL was executed
    if result.get("generated_sql") and not (
        result["generated_sql"].startswith("BLOCKED") or
        result["generated_sql"].startswith("EXECUTION_ERROR")
    ):
        total += 1
        sql_results = result.get("sql_results", None)
        if isinstance(sql_results, list):
            ok(f"sql_results is a list ({len(sql_results)} rows)")
            passed += 1
        else:
            fail(f"sql_results is not a list: {type(sql_results)}")

    return passed, total


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_tests() -> None:
    hdr("SCOUT — Chat Workflow Integration Test", MAGENTA)
    print(f"  Mirrors the logic in {BOLD}backend/api/chat.py ›› generate(){RESET}")
    print(f"  Testing {len(TEST_SCENARIOS)} demo scenarios against the live pipeline.\n")

    # Import the pipeline (validates that it can be imported without the HTTP layer)
    try:
        from backend.agents.pipeline import pipeline
        ok("Pipeline imported successfully")
    except Exception as exc:
        print(f"{RED}Cannot import pipeline: {exc}{RESET}")
        raise

    total_passed = 0
    total_checks = 0
    results_summary = []

    for scenario in TEST_SCENARIOS:
        hdr(f"{scenario['id']} — {scenario['desc']}", CYAN)

        user_cfg = DEMO_USERS[scenario["user"]]
        info("User profile", scenario["user"])
        info("Persona",      user_cfg["user_persona"])
        info("Team ID",      user_cfg["team_id"][:8] + "…")
        info("Allowed teams", len(user_cfg["allowed_team_ids"]))
        info("Query",        scenario["query"])
        if scenario.get("previous_query"):
            info("Prev Query", scenario["previous_query"])

        initial_state = build_initial_state(scenario["user"], scenario)

        sub("Running pipeline.invoke()")
        t0 = time.time()
        try:
            result_state = pipeline.invoke(initial_state)
            elapsed = time.time() - t0
            ok(f"Pipeline completed in {elapsed:.2f}s")
        except Exception as exc:
            elapsed = time.time() - t0
            fail(f"Pipeline raised an exception after {elapsed:.2f}s: {exc}")
            results_summary.append({"id": scenario["id"], "passed": 0, "total": 1,
                                     "error": str(exc)})
            continue

        # Intermediate state printout
        sub("Pipeline state after invoke()")
        info("query_intent",     result_state.get("query_intent"))
        info("relevant_tables",  result_state.get("relevant_tables"))
        generated_sql = result_state.get("generated_sql", "")
        if generated_sql:
            info("generated_sql",
                 generated_sql[:200].replace("\n", " "))
        info("sql_results rows", len(result_state.get("sql_results", [])))
        info("rag_chunks count", len(result_state.get("rag_chunks", [])))
        info("synthesized_ctx",
             (result_state.get("synthesized_context") or "")[:120])

        # Simulate the SSE stream (what chat.py yields word-by-word)
        final_answer = result_state.get("final_answer", "")
        if final_answer:
            simulate_sse_stream(final_answer)

        # Print the SSE "done" event (what chat.py sends at the end)
        cot = result_state.get("chain_of_thought", {})
        done_event = json.dumps({"type": "done", "chain_of_thought": cot}, indent=2)
        sub("SSE Done event (chain_of_thought payload)")
        # Pretty-print first 600 chars to avoid flooding
        print(textwrap.indent(done_event[:600] + ("…" if len(done_event) > 600 else ""), "  "))

        # Run validations
        passed, total = validate_result(scenario, result_state)
        total_passed += passed
        total_checks += total

        badge = f"{GREEN}PASS{RESET}" if passed == total else f"{YELLOW}PARTIAL{RESET}"
        if passed == 0:
            badge = f"{RED}FAIL{RESET}"
        print(f"\n  Result: {badge}  ({passed}/{total} checks passed)")
        results_summary.append({"id": scenario["id"], "passed": passed, "total": total})

    # ---------------------------------------------------------------------------
    # Summary table
    # ---------------------------------------------------------------------------
    hdr("TEST SUMMARY", MAGENTA)
    print(f"  {'Scenario':<8}  {'Checks':<16}  {'Status'}")
    print(f"  {'─'*8}  {'─'*16}  {'─'*10}")
    all_pass = True
    for r in results_summary:
        p, t = r["passed"], r["total"]
        if p == t:
            status = f"{GREEN}PASS{RESET}"
        elif p > 0:
            status = f"{YELLOW}PARTIAL{RESET}"
            all_pass = False
        else:
            status = f"{RED}FAIL{RESET}"
            all_pass = False
        err = f"  ← {r['error']}" if "error" in r else ""
        print(f"  {r['id']:<8}  {p}/{t} checks passed  {status}{err}")

    print(f"\n  Grand total: {total_passed}/{total_checks} checks passed")

    if all_pass:
        print(f"\n{GREEN}{BOLD}  ✓ All scenarios PASSED. Pipeline workflow is operating correctly.{RESET}\n")
    else:
        print(f"\n{YELLOW}{BOLD}  ⚠  Some scenarios did not pass all checks — review output above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
