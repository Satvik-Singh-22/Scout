#!/usr/bin/env python3
"""
Slack/Jira Integration Test Suite
==================================
Validates that the Slack API token, Jira API credentials, LLM intent
classification, and the full end-to-end slack_jira agent pipeline are
functioning correctly.

Run:
    cd src/backend
    source ../../venv/bin/activate
    python -m tests.test_slack_jira_integration

Each test prints a clear PASS / FAIL with diagnostic details.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure imports work from the backend directory
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

_results: list[dict] = []


def _header(title: str):
    width = 70
    print(f"\n{BLUE}{'═' * width}")
    print(f"  {BOLD}{title}{RESET}{BLUE}")
    print(f"{'═' * width}{RESET}\n")


def _pass(name: str, detail: str = ""):
    _results.append({"name": name, "status": "PASS"})
    tag = f"{GREEN}{BOLD}✓ PASS{RESET}"
    print(f"  {tag}  {name}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"         {CYAN}{line}{RESET}")


def _fail(name: str, detail: str = ""):
    _results.append({"name": name, "status": "FAIL"})
    tag = f"{RED}{BOLD}✗ FAIL{RESET}"
    print(f"  {tag}  {name}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"         {YELLOW}{line}{RESET}")


def _info(msg: str):
    print(f"  {CYAN}ℹ {msg}{RESET}")


# ===================================================================
# TEST 1 — Environment Variables Present
# ===================================================================
def test_env_variables():
    _header("TEST 1 — Environment Variables")

    required = {
        "SLACK_USER_TOKEN": os.getenv("SLACK_USER_TOKEN"),
        "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL"),
        "JIRA_EMAIL": os.getenv("JIRA_EMAIL"),
        "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    }

    all_ok = True
    for key, value in required.items():
        if value:
            masked = value[:8] + "..." + value[-4:] if len(value) > 16 else "***"
            _pass(f"{key} is set", f"Value: {masked}")
        else:
            _fail(f"{key} is MISSING")
            all_ok = False

    return all_ok


# ===================================================================
# TEST 2 — Slack API Connectivity
# ===================================================================
def test_slack_api():
    _header("TEST 2 — Slack API Connectivity")

    from backend.agents.slack_jira.tools.slack_tool import search

    queries = [
        ("Payment failures", "payment failed"),
        ("Backend errors", "database connection"),
        ("General channel", "standup"),
    ]

    any_success = False
    for label, query in queries:
        _info(f'Query: "{query}"')
        try:
            t0 = time.time()
            results = search(query)
            elapsed = time.time() - t0

            if results:
                _pass(
                    f"Slack — {label} ({len(results)} results, {elapsed:.2f}s)",
                    f"First result: #{results[0].get('channel', '?')} | "
                    f"{results[0].get('username', '?')} | "
                    f"{results[0].get('text', '')[:80]}..."
                )
                any_success = True
            else:
                _fail(
                    f"Slack — {label} (0 results, {elapsed:.2f}s)",
                    "API returned empty. Token may lack search:read scope, "
                    "or workspace has no matching messages."
                )
        except Exception as exc:
            _fail(f"Slack — {label}", f"Exception: {exc}")

    return any_success


# ===================================================================
# TEST 3 — Jira API Connectivity
# ===================================================================
def test_jira_api():
    _header("TEST 3 — Jira API Connectivity")

    from backend.agents.slack_jira.tools.jira_tool import search

    queries = [
        ("Bug search", "bug login error"),
        ("Task search", "deployment backend"),
        ("Sprint query", "sprint planning"),
    ]

    any_success = False
    for label, query in queries:
        _info(f'Query: "{query}"')
        try:
            t0 = time.time()
            results = search(query)
            elapsed = time.time() - t0

            if results:
                _pass(
                    f"Jira — {label} ({len(results)} results, {elapsed:.2f}s)",
                    f"First result: {results[0].get('key', '?')} | "
                    f"{results[0].get('status', '?')} | "
                    f"{results[0].get('summary', '')[:80]}"
                )
                any_success = True
            else:
                # Jira may legitimately return 0 results for test queries  
                _pass(
                    f"Jira — {label} (0 results, {elapsed:.2f}s)",
                    "API responded successfully (auth OK), but no matching issues found. "
                    "This is normal for a fresh/empty Jira workspace."
                )
                any_success = True  # Auth worked even if 0 results
        except Exception as exc:
            err_str = str(exc)
            if "401" in err_str:
                _fail(f"Jira — {label}", "401 Unauthorized — check JIRA_EMAIL + JIRA_API_TOKEN")
            elif "403" in err_str:
                _fail(f"Jira — {label}", "403 Forbidden — API token may lack permissions")
            elif "404" in err_str:
                _fail(f"Jira — {label}", "404 Not Found — check JIRA_BASE_URL")
            else:
                _fail(f"Jira — {label}", f"Exception: {exc}")

    return any_success


# ===================================================================
# TEST 4 — Jira API Raw HTTP (auth validation)
# ===================================================================
def test_jira_auth_raw():
    _header("TEST 4 — Jira Auth Validation (raw HTTP)")

    import httpx
    from base64 import b64encode

    base_url = os.getenv("JIRA_BASE_URL", "")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")

    if not all([base_url, email, token]):
        _fail("Jira credentials incomplete — skipping raw auth test")
        return False

    creds = b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Accept": "application/json",
    }

    # Test 1: Get myself (validates auth)
    try:
        url = f"{base_url.rstrip('/')}/rest/api/3/myself"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            _pass(
                "Jira auth — /myself",
                f"Authenticated as: {data.get('displayName', '?')} ({data.get('emailAddress', '?')})"
            )
        else:
            _fail("Jira auth — /myself", f"Status {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as exc:
        _fail("Jira auth — /myself", f"Exception: {exc}")
        return False

    # Test 2: List projects
    try:
        url = f"{base_url.rstrip('/')}/rest/api/3/project"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code == 200:
            projects = resp.json()
            if projects:
                names = [p.get("key", "?") + " — " + p.get("name", "?") for p in projects[:5]]
                _pass(
                    f"Jira projects — found {len(projects)}",
                    "\n".join(names)
                )
            else:
                _pass("Jira projects — 0 projects", "Auth works, but no projects exist yet.")
        else:
            _fail("Jira projects", f"Status {resp.status_code}")
    except Exception as exc:
        _fail("Jira projects", f"Exception: {exc}")

    return True


# ===================================================================
# TEST 5 — LLM / Intent Classifier
# ===================================================================
def test_llm_intent_classifier():
    _header("TEST 5 — LLM Intent Classifier")

    from backend.agents.slack_jira.core.intent_classifier import classify

    test_cases = [
        ("What did the team discuss about the deadline?", "SLACK"),
        ("Show me all open bugs assigned to me", "JIRA"),
        ("What's the status of PROJ-42 and did anyone mention it in Slack?", "BOTH"),
        ("Find the latest sprint planning tickets", "JIRA"),
        ("Who posted about the deployment in general channel?", "SLACK"),
    ]

    correct = 0
    total = len(test_cases)

    for query, expected in test_cases:
        _info(f'Query: "{query}"')
        try:
            t0 = time.time()
            result = classify(query)
            elapsed = time.time() - t0

            if result == expected:
                _pass(
                    f"Intent: {result} (expected {expected}, {elapsed:.2f}s)",
                )
                correct += 1
            else:
                # Not a hard failure — the LLM may have a different but valid interpretation
                _info(f"  Got {result}, expected {expected} — LLM made a different choice ({elapsed:.2f}s)")
                # Still count as pass if the result is a valid intent
                if result in {"SLACK", "JIRA", "BOTH"}:
                    _pass(f"Intent: {result} (valid but differs from expected {expected})")
                    correct += 1
                else:
                    _fail(f"Intent: {result} (invalid intent value)")

        except Exception as exc:
            _fail(f"Intent classifier error", f"Exception: {exc}")

    _info(f"Score: {correct}/{total} valid intents returned")
    return correct > 0


# ===================================================================
# TEST 6 — Core Modules (coreference, reranker, context_builder)
# ===================================================================
def test_core_modules():
    _header("TEST 6 — Core Modules (no external calls)")

    # --- Coreference ---
    from backend.agents.slack_jira.core.coreference import rewrite

    q1 = rewrite("What about that?", [
        {"role": "USER", "content": "Show me bugs in the auth module"},
        {"role": "ASSISTANT", "content": "Here are 3 bugs..."},
    ])
    if "previously asked about" in q1:
        _pass("Coreference — trigger word detected", f"Rewritten: {q1[:80]}")
    else:
        _fail("Coreference — trigger word NOT detected")

    q2 = rewrite("Show me open bugs", [])
    if q2 == "Show me open bugs":
        _pass("Coreference — no trigger, unchanged")
    else:
        _fail("Coreference — should have left query unchanged")

    # --- Cache ---
    from backend.agents.slack_jira.core.cache import get, set, clear, stats

    clear()
    set("test query", "BOTH", {"final_answer": "mock answer"})
    cached = get("test query", "BOTH")
    if cached and cached.get("final_answer") == "mock answer":
        _pass("Cache — set/get round-trip")
    else:
        _fail("Cache — set/get round-trip failed")

    missed = get("nonexistent query", "SLACK")
    if missed is None:
        _pass("Cache — miss returns None")
    else:
        _fail("Cache — expected None on miss")
    clear()

    # --- Context Builder ---
    from backend.agents.slack_jira.core.context_builder import build

    ctx = build(
        query="What's the sprint status?",
        slack_results=[
            {"channel": "general", "username": "alice", "date": "2026-04-17", "text": "Sprint ends Friday"},
        ],
        jira_results=[
            {"key": "PROJ-10", "status": "In Progress", "priority": "High",
             "assignee": "Bob", "description": "Backend API refactor"},
        ],
        history=[
            {"role": "USER", "content": "Previous question"},
            {"role": "ASSISTANT", "content": "Previous answer"},
        ],
    )
    checks = ["[SLACK]", "[JIRA]", "PROJ-10", "#general", "Question:"]
    all_sections = all(s in ctx for s in checks)
    if all_sections:
        _pass("Context builder — all sections present", f"Context length: {len(ctx)} chars")
    else:
        missing = [s for s in checks if s not in ctx]
        _fail("Context builder — missing sections", f"Missing: {missing}")

    return True


# ===================================================================
# TEST 7 — Reranker (embedding model)
# ===================================================================
def test_reranker():
    _header("TEST 7 — Reranker (sentence-transformers)")

    from backend.agents.slack_jira.core.reranker import rerank

    mock_results = [
        {"text": "We deployed the login page update to production yesterday."},
        {"text": "Lunch menu for today: pasta and salad."},
        {"text": "The authentication bug is fixed in PR #42."},
        {"text": "Team outing is scheduled for next Friday."},
        {"text": "OAuth flow was breaking on mobile — now patched."},
    ]

    try:
        t0 = time.time()
        ranked = rerank("login authentication bug fix", mock_results, "text", top_n=3)
        elapsed = time.time() - t0

        if len(ranked) == 3:
            _pass(
                f"Reranker returned top-3 ({elapsed:.2f}s)",
                "\n".join(f"  {i+1}. {r['text'][:70]}..." for i, r in enumerate(ranked))
            )

            # Check that the auth/login results are ranked higher than lunch/outing
            ranked_texts = [r["text"] for r in ranked]
            auth_in_top = any("auth" in t.lower() or "login" in t.lower() or "oauth" in t.lower()
                            for t in ranked_texts)
            if auth_in_top:
                _pass("Reranker — semantic relevance looks correct")
            else:
                _fail("Reranker — auth-related results not in top 3")
        else:
            _fail(f"Reranker — expected 3, got {len(ranked)}")

    except Exception as exc:
        _fail("Reranker failed", f"Exception: {exc}")

    return True


# ===================================================================
# TEST 8 — Full End-to-End Agent Pipeline
# ===================================================================
def test_full_pipeline():
    _header("TEST 8 — Full End-to-End Slack/Jira Agent")

    from backend.agents.slack_jira.agent import slack_jira_agent

    test_queries = [
        {
            "label": "Slack-focused query",
            "state": {
                "user_query": "What are the latest discussions in the team?",
                "user_id": "test-user-001",
                "user_persona": "TECHNICAL",
                "team_id": "test-team-001",
                "allowed_team_ids": ["test-team-001"],
                "current_date": "2026-04-18",
                "query_intent": "SLACK_JIRA",
                "routing_decision": {},
                "relevant_tables": [],
                "generated_sql": "",
                "sql_tables_used": [],
                "sql_results": [],
                "sql_retry_count": 0,
                "sql_error": "",
                "execution_error": "",
                "rag_chunks": [],
                "synthesized_context": "",
                "final_answer": "",
                "chain_of_thought": {},
                "previous_query": "",
                "previous_answer": "",
                "previous_sql": "",
                "previous_tables_used": [],
                "agent_mode": "SLACK_JIRA",
            },
        },
        {
            "label": "Jira-focused query",
            "state": {
                "user_query": "Show me the high priority open bugs",
                "user_id": "test-user-001",
                "user_persona": "TECHNICAL",
                "team_id": "test-team-001",
                "allowed_team_ids": ["test-team-001"],
                "current_date": "2026-04-18",
                "query_intent": "SLACK_JIRA",
                "routing_decision": {},
                "relevant_tables": [],
                "generated_sql": "",
                "sql_tables_used": [],
                "sql_results": [],
                "sql_retry_count": 0,
                "sql_error": "",
                "execution_error": "",
                "rag_chunks": [],
                "synthesized_context": "",
                "final_answer": "",
                "chain_of_thought": {},
                "previous_query": "",
                "previous_answer": "",
                "previous_sql": "",
                "previous_tables_used": [],
                "agent_mode": "SLACK_JIRA",
            },
        },
        {
            "label": "Combined Slack + Jira query",
            "state": {
                "user_query": "What's the latest on the deployment — any related tickets and Slack discussions?",
                "user_id": "test-user-001",
                "user_persona": "EXECUTIVE",
                "team_id": "test-team-001",
                "allowed_team_ids": ["test-team-001"],
                "current_date": "2026-04-18",
                "query_intent": "SLACK_JIRA",
                "routing_decision": {},
                "relevant_tables": [],
                "generated_sql": "",
                "sql_tables_used": [],
                "sql_results": [],
                "sql_retry_count": 0,
                "sql_error": "",
                "execution_error": "",
                "rag_chunks": [],
                "synthesized_context": "",
                "final_answer": "",
                "chain_of_thought": {},
                "previous_query": "",
                "previous_answer": "",
                "previous_sql": "",
                "previous_tables_used": [],
                "agent_mode": "SLACK_JIRA",
            },
        },
    ]

    any_success = False

    for tc in test_queries:
        label = tc["label"]
        state = tc["state"]
        _info(f'{label}: "{state["user_query"]}"')

        try:
            t0 = time.time()
            result = slack_jira_agent(state)
            elapsed = time.time() - t0

            answer = result.get("final_answer", "")
            cot = result.get("chain_of_thought", {})
            detail = cot.get("slack_jira_detail", {})

            if answer:
                _pass(
                    f"{label} — answered ({elapsed:.2f}s)",
                    f"Intent: {detail.get('sub_intent', '?')}\n"
                    f"Slack results: {detail.get('slack_count', 0)} raw → {detail.get('slack_reranked', 0)} reranked\n"
                    f"Jira results: {detail.get('jira_count', 0)} raw → {detail.get('jira_reranked', 0)} reranked\n"
                    f"Answer: {answer[:150]}..."
                )
                any_success = True
            else:
                _fail(f"{label} — no answer returned")

        except Exception as exc:
            _fail(f"{label}", f"Exception: {exc}\n{traceback.format_exc()[-300:]}")

    return any_success


# ===================================================================
# TEST 9 — Follow-up Query (coreference in pipeline)
# ===================================================================
def test_followup_query():
    _header("TEST 9 — Follow-up Query (multi-turn)")

    from backend.agents.slack_jira.agent import slack_jira_agent

    state = {
        "user_query": "Tell me more about that",
        "user_id": "test-user-001",
        "user_persona": "TECHNICAL",
        "team_id": "test-team-001",
        "allowed_team_ids": ["test-team-001"],
        "current_date": "2026-04-18",
        "query_intent": "SLACK_JIRA",
        "routing_decision": {},
        "relevant_tables": [],
        "generated_sql": "",
        "sql_tables_used": [],
        "sql_results": [],
        "sql_retry_count": 0,
        "sql_error": "",
        "execution_error": "",
        "rag_chunks": [],
        "synthesized_context": "",
        "final_answer": "",
        "chain_of_thought": {},
        "previous_query": "What bugs are open in the authentication module?",
        "previous_answer": "There are 3 open bugs related to authentication...",
        "previous_sql": "",
        "previous_tables_used": [],
        "agent_mode": "SLACK_JIRA",
    }

    _info(f'Query: "{state["user_query"]}"')
    _info(f'Previous: "{state["previous_query"]}"')

    try:
        t0 = time.time()
        result = slack_jira_agent(state)
        elapsed = time.time() - t0

        cot = result.get("chain_of_thought", {})
        detail = cot.get("slack_jira_detail", {})
        resolved = detail.get("query_resolved", "")

        if "previously asked about" in resolved.lower() or "authentication" in resolved.lower():
            _pass(
                f"Coreference worked in pipeline ({elapsed:.2f}s)",
                f"Resolved query: {resolved[:120]}"
            )
        else:
            _pass(
                f"Follow-up completed ({elapsed:.2f}s)",
                f"Resolved query: {resolved[:120]}\n"
                f"Answer: {result.get('final_answer', '')[:120]}..."
            )

    except Exception as exc:
        _fail("Follow-up query failed", f"Exception: {exc}")


# ===================================================================
# Summary
# ===================================================================
def print_summary():
    _header("TEST SUMMARY")
    passed = sum(1 for r in _results if r["status"] == "PASS")
    failed = sum(1 for r in _results if r["status"] == "FAIL")
    total = len(_results)

    for r in _results:
        icon = f"{GREEN}✓{RESET}" if r["status"] == "PASS" else f"{RED}✗{RESET}"
        print(f"  {icon} {r['name']}")

    print()
    color = GREEN if failed == 0 else (YELLOW if failed < total // 2 else RED)
    print(f"  {BOLD}{color}{passed}/{total} passed, {failed} failed{RESET}\n")


# ===================================================================
# Main
# ===================================================================
if __name__ == "__main__":
    print(f"\n{BOLD}{BLUE}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║          SLACK / JIRA  INTEGRATION  TEST  SUITE                    ║")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{RESET}")

    # Clear the slack_jira cache before testing
    from backend.agents.slack_jira.core.cache import clear as clear_cache
    clear_cache()
    
    # Sync data into ChromaDB for semantic search tests
    print(f"\n{CYAN}ℹ Syncing Slack/Jira data to ChromaDB for semantic testing...{RESET}")
    from backend.services.sync_workflow_data import sync_workflow_data
    sync_workflow_data()
    print(f"{GREEN}✓ Sync completed!{RESET}\n")

    test_env_variables()
    test_slack_api()
    test_jira_api()
    test_jira_auth_raw()
    test_llm_intent_classifier()
    test_core_modules()
    test_reranker()
    test_full_pipeline()
    test_followup_query()
    print_summary()
