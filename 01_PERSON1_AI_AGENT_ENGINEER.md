# PERSON 1 — AI AGENT ENGINEER
## Read 00_MASTER_SHARED_CONTEXT.md first. Everything in that document applies to you.

---

## YOUR ROLE

You own all intelligence. Every file inside `/backend/agents/` and `/backend/vectorstore/` is yours. You never touch route files, never touch the database models file, never touch the frontend. Person 2 provides you with one function: `get_db_session()` which you call in `relevancy_agent.py` and `execution_agent.py`. That is the only dependency you have on Person 2.

---

## YOUR FILES — COMPLETE LIST

```
backend/agents/state.py                  ← Write at hour 0 with the team
backend/agents/orchestrator_agent.py     ← Build first (hour 2–4)
backend/agents/relevancy_agent.py        ← Build second (hour 4–6)
backend/agents/sql_gen_agent.py          ← Build third (hour 6–8)
backend/agents/rag_agent.py              ← Build fourth (hour 8–9)
backend/agents/execution_agent.py        ← Build fifth (hour 9–11)
backend/agents/synthesis_agent.py        ← Build sixth (hour 11–12)
backend/agents/persona_agent.py          ← Build seventh (hour 12–14)
backend/agents/pipeline.py               ← Wire everything (hour 14–16)
backend/agents/anomaly_agent.py          ← Build after pipeline works (hour 18–22)
backend/vectorstore/chroma_manager.py    ← Build alongside rag_agent (hour 8–9)
backend/tests/test_orchestrator_agent.py ← Write at hour 40
backend/tests/test_sql_gen_agent.py      ← Write at hour 40
backend/tests/test_relevancy_agent.py    ← Write at hour 41
backend/tests/test_execution_agent.py    ← Write at hour 42
```

---

## HOUR-BY-HOUR PLAN

### Hour 0–2 (with the team)
- Agree on `state.py` — every field. Copy exactly from the Master Shared Context.
- Confirm Groq API key: `curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models` returns 200.
- Install all dependencies: `pip install -r requirements.txt`

### Hour 2–16 (build all 7 pipeline agents)
See detailed specs for each file below. Build in the listed order.

### Hour 16–20 (integration with Person 2)
- Person 2 has `/chatrooms/{id}/message` ready.
- You wire `pipeline.invoke()` into Person 2's `chat.py`.
- Together, run one live query and confirm SSE stream works.

### Hour 20–22 (testing against real mock data)
- Person 4 will have 40 tables seeded by now.
- Run the 5 demo queries from the Master Shared Context section 11.
- Fix prompt templates where SQL is wrong or RAG returns irrelevant chunks.

### Hour 22–26 (build anomaly agent)
- Build `anomaly_agent.py`.
- Wire it into `anomaly_service.py` (Person 2 owns that file, you provide the agent function).

### Hour 26–36 (tuning)
- Run each of the 5 demo queries 3 times.
- Confirm consistent, accurate results.
- Fix any prompt failures.
- Focus especially on the date resolution (current_date must flow into SQL gen prompt).

### Hour 40–44 (write tests)
- Write 4 test files.
- Tests are simple: input fixture → run agent function → assert output shape is correct.

---

## FILE 1: `state.py`

Copy this exactly. Do not modify without telling Person 2.

```python
from typing import TypedDict

class PipelineState(TypedDict):
    user_query: str
    user_id: str
    user_persona: str
    team_id: str
    current_date: str
    query_intent: str
    routing_decision: dict
    relevant_tables: list
    generated_sql: str
    sql_results: list
    rag_chunks: list
    synthesized_context: str
    final_answer: str
    chain_of_thought: dict
```

---

## FILE 2: `orchestrator_agent.py`

**Purpose:** First node in the LangGraph graph. Classifies the user's query intent. Determines whether to use SQL, RAG, or both. Also fetches current_date and validates team_id (team_id comes from the JWT token via chat.py, so it is already in state).

**LangChain components used:** `ChatGroq`, `ChatPromptTemplate`, `JsonOutputParser`, `Pydantic BaseModel`

**Input from state:** `user_query`, `team_id`, `user_persona`

**Output to state:** `query_intent`, `routing_decision`

**Logic:**
```
The orchestrator calls the LLM with:
  - The user's query
  - A description of available data types: "structured SQL tables with transactions, logs, financial data" and "unstructured text: customer reviews and complaints"
The LLM returns a JSON with:
  - query_intent: "SQL_ONLY" | "RAG_ONLY" | "HYBRID"
  - reasoning: one sentence explaining why

Rules for the prompt:
  - SQL_ONLY: user asks for numbers, counts, aggregations, specific values, time-series data
  - RAG_ONLY: user asks what customers are saying, sentiment, complaint themes, text content
  - HYBRID: user asks a question that needs both (e.g. "did complaints increase when failures spiked?")
```

**Pydantic output model:**
```python
from pydantic import BaseModel

class OrchestratorOutput(BaseModel):
    query_intent: str  # Must be "SQL_ONLY", "RAG_ONLY", or "HYBRID"
    reasoning: str
```

**Prompt template:**
```python
from langchain_core.prompts import ChatPromptTemplate

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data routing agent for a banking intelligence system.
You decide how to answer a user's question based on available data types.

Available data types:
1. STRUCTURED (SQL): Transaction records, payment events, API logs, system metrics, financial data, branch performance — anything with numbers, dates, counts, regions, amounts.
2. UNSTRUCTURED (RAG): Customer reviews, complaint text, support ticket descriptions — free text expressing opinions or issues.

Respond ONLY with a JSON object. No explanation outside the JSON.
Format: {{"query_intent": "SQL_ONLY|RAG_ONLY|HYBRID", "reasoning": "one sentence"}}

Rules:
- SQL_ONLY: question needs exact numbers, aggregations, comparisons, trends, time-series
- RAG_ONLY: question asks what customers said, customer sentiment, complaint themes
- HYBRID: question needs both numerical data AND customer text context together
"""),
    ("human", "User question: {user_query}")
])
```

**Function signature:**
```python
def orchestrator_agent(state: PipelineState) -> dict:
    # Returns dict with keys: query_intent, routing_decision
    # routing_decision = {"use_sql": bool, "use_rag": bool, "reasoning": str}
```

---

## FILE 3: `relevancy_agent.py`

**Purpose:** Reads the `master_config` table for the user's `team_id`. Sends only the table names and their `semantic_definition` fields (NOT column details) to the LLM. LLM returns which tables are relevant.

**LangChain components:** `ChatGroq`, `ChatPromptTemplate`, `JsonOutputParser`, `Pydantic BaseModel`

**Input from state:** `user_query`, `team_id`, `query_intent`

**Output to state:** `relevant_tables` (list of table names)

**Database call:** Use SQLAlchemy to query `master_config WHERE team_id = :team_id AND is_active = TRUE`. Return list of `{table_name, semantic_definition}` dicts.

**Critical rule:** If `query_intent == "RAG_ONLY"`, skip the LLM call and return `relevant_tables = []`. The RAG agent does not need table names from master_config.

**Pydantic output model:**
```python
class RelevancyOutput(BaseModel):
    tables: list[str]
    reasoning: str
```

**Prompt template:**
```python
RELEVANCY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data architect for a banking system.
Given a user's question and a list of available tables with their descriptions,
identify which tables are needed to answer the question.

Return ONLY a JSON object: {{"tables": ["table1", "table2"], "reasoning": "one sentence"}}
Only include tables that are genuinely needed. Maximum 5 tables.
Available tables:
{available_tables}
"""),
    ("human", "User question: {user_query}")
])
```

`available_tables` is formatted as:
```
table_name: semantic_definition
mock_transactions: Records of all payment transactions including amount, region, status, timestamp, and merchant category.
mock_api_gateway_logs: API gateway request/response logs including endpoint, method, status code, latency, and error messages.
```

---

## FILE 4: `sql_gen_agent.py`

**Purpose:** Takes the relevant table names from `relevancy_agent` and fetches their full `columns_metadata` from `master_config`. Constructs a detailed schema prompt and generates a valid, read-only SQL SELECT query.

**LangChain components:** `ChatGroq`, `ChatPromptTemplate`, custom string output parser (strip whitespace and code fences)

**Input from state:** `user_query`, `relevant_tables`, `team_id`, `current_date`, `query_intent`

**Output to state:** `generated_sql`

**Critical rule:** If `query_intent == "RAG_ONLY"` or `relevant_tables` is empty, return `generated_sql = ""` immediately without calling the LLM.

**Database call:** Query `master_config WHERE table_name IN (:relevant_tables) AND team_id = :team_id`. Return columns_metadata for each table.

**Schema format passed to LLM:**
```
Table: mock_transactions
Columns:
  - id (UUID): Unique transaction identifier
  - amount (DECIMAL): Transaction amount in GBP
  - status (VARCHAR): "SUCCESS" or "FAILED"
  - region (VARCHAR): "NORTH", "SOUTH", "EAST", "WEST"
  - created_at (TIMESTAMP): When the transaction occurred
  - merchant_category (VARCHAR): Category of merchant
```

**Prompt template:**
```python
SQL_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL expert for a PostgreSQL banking database.
Generate a single valid PostgreSQL SELECT query to answer the user's question.
Today's date is {current_date}.

Rules:
- Return ONLY the SQL query. No explanation. No markdown. No code fences.
- Only use SELECT statements. Never UPDATE, DELETE, INSERT, DROP, CREATE.
- Only reference tables listed in the schema below.
- When user says "last month", "this week", "yesterday" — resolve to exact dates using {current_date}.
- Use LIMIT 1000 on queries that could return large result sets.
- Use proper PostgreSQL date functions: DATE_TRUNC, INTERVAL, EXTRACT.

Database schema:
{schema}
"""),
    ("human", "{user_query}")
])
```

**Output parsing:**
```python
def parse_sql_output(raw: str) -> str:
    # Strip markdown code fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1])
    return clean.strip()
```

---

## FILE 5: `rag_agent.py`

**Purpose:** Performs semantic similarity search over ChromaDB using the user's query. Returns top-5 most relevant text chunks from customer reviews.

**LangChain components:** `langchain_community.vectorstores.Chroma`, `langchain_community.embeddings.HuggingFaceEmbeddings`

**Input from state:** `user_query`, `query_intent`

**Output to state:** `rag_chunks` (list of strings)

**Critical rule:** If `query_intent == "SQL_ONLY"`, return `rag_chunks = []` immediately. Do not load the embedding model or query ChromaDB.

**Implementation:**
```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.vectorstore.chroma_manager import get_retriever

def rag_agent(state: PipelineState) -> dict:
    if state["query_intent"] == "SQL_ONLY":
        return {"rag_chunks": []}
    
    retriever = get_retriever()
    docs = retriever.invoke(state["user_query"])
    chunks = [doc.page_content for doc in docs]
    return {"rag_chunks": chunks}
```

---

## FILE 6: `chroma_manager.py` (in /vectorstore/)

**Purpose:** Initializes ChromaDB and provides a retriever factory. Called by `rag_agent.py`.

```python
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

_vectorstore = None

def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vectorstore = Chroma(
            collection_name="customer_reviews",
            embedding_function=embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")
        )
    return _vectorstore

def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": 5})
```

---

## FILE 7: `execution_agent.py`

**Purpose:** Validates and executes the SQL query against PostgreSQL. This is the security-critical agent. Uses raw SQLAlchemy — zero LangChain.

**Input from state:** `generated_sql`, `team_id`, `relevant_tables`

**Output to state:** `sql_results`

**Critical rule 1:** If `generated_sql == ""`, return `sql_results = []` immediately.

**Critical rule 2 — SQL validation (run before execution):**
```python
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]

def validate_sql(sql: str) -> tuple[bool, str]:
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return False, f"Forbidden keyword detected: {keyword}"
    if not sql_upper.strip().startswith("SELECT"):
        return False, "Query must start with SELECT"
    return True, ""
```

**Critical rule 3 — Table authorization check:**
```python
def verify_table_authorization(sql: str, authorized_tables: list[str]) -> bool:
    """
    Check that every table referenced in the SQL appears in authorized_tables.
    This prevents the LLM from hallucinating a table name outside master_config.
    Simple implementation: check if each authorized table name appears in SQL.
    If SQL references a table not in authorized_tables, block execution.
    """
    sql_lower = sql.lower()
    # Extract table names referenced in SQL using simple FROM/JOIN parsing
    import re
    referenced = re.findall(r'(?:from|join)\s+([a-z_][a-z0-9_]*)', sql_lower)
    for table in referenced:
        if table not in [t.lower() for t in authorized_tables]:
            return False
    return True
```

**Execution:**
```python
from sqlalchemy import text
from backend.db.session import get_sync_session

def execution_agent(state: PipelineState) -> dict:
    sql = state["generated_sql"]
    if not sql:
        return {"sql_results": []}
    
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return {"sql_results": [], "generated_sql": f"BLOCKED: {error}"}
    
    if not verify_table_authorization(sql, state["relevant_tables"]):
        return {"sql_results": [], "generated_sql": "BLOCKED: Unauthorized table reference"}
    
    try:
        with get_sync_session() as session:
            result = session.execute(text(sql))
            rows = [dict(row._mapping) for row in result.fetchmany(1000)]
            return {"sql_results": rows}
    except Exception as e:
        return {"sql_results": [], "generated_sql": f"EXECUTION_ERROR: {str(e)}"}
```

---

## FILE 8: `synthesis_agent.py`

**Purpose:** Merges SQL result rows and RAG text chunks into a single coherent context string that the Persona Agent can use to write the final answer.

**LangChain components:** `ChatGroq`, `ChatPromptTemplate`

**Input from state:** `sql_results`, `rag_chunks`, `user_query`

**Output to state:** `synthesized_context`

**Prompt template:**
```python
SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data synthesis agent. 
Combine the structured query results and unstructured text excerpts into a coherent factual summary.
Do not format for a user yet — this summary will be further processed.
Be complete and accurate. Include all numbers and key findings.
"""),
    ("human", """Original question: {user_query}

SQL query results (structured data):
{sql_results}

Relevant text excerpts (unstructured data):
{rag_chunks}

Provide a complete factual synthesis:""")
])
```

Format `sql_results` as: First 20 rows as a readable table or JSON. If empty, write "No SQL data available."
Format `rag_chunks` as: Numbered list of text excerpts. If empty, write "No text data available."

---

## FILE 9: `persona_agent.py`

**Purpose:** Takes the synthesized context and writes the final answer tailored to the user's persona. Also builds the full Chain of Thought JSON.

**LangChain components:** `ChatGroq`, two `ChatPromptTemplate` instances (one per persona), `JsonOutputParser`

**Input from state:** `synthesized_context`, `user_query`, `user_persona`, `generated_sql`, `relevant_tables`, `rag_chunks`, `query_intent`

**Output to state:** `final_answer`, `chain_of_thought`

**Manager prompt template:**
```python
MANAGER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a business intelligence assistant for a non-technical banking manager.
Rules:
- Use plain English. No SQL. No technical jargon.
- Lead with the key finding in one sentence.
- Support with 2-3 bullet points of specific facts and numbers.
- End with one actionable implication.
- Keep total response under 200 words.
- If showing trends, describe them simply: "increased by X%" not "coefficient of variation".
"""),
    ("human", """Question: {user_query}

Data findings: {synthesized_context}

Write a clear, simple answer:""")
])
```

**Developer prompt template:**
```python
DEVELOPER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a technical data analyst assistant for a developer.
Rules:
- Lead with the direct answer.
- Include specific metrics, percentages, and exact values.
- Reference which tables and fields the data came from.
- If relevant, note data quality issues or edge cases observed.
- Use technical language appropriately.
- Format numbers precisely.
"""),
    ("human", """Question: {user_query}

Data findings: {synthesized_context}

SQL executed: {sql_executed}

Tables referenced: {tables_referenced}

Write a detailed technical answer:""")
])
```

**Chain of Thought assembly:**
```python
def build_chain_of_thought(state: PipelineState) -> dict:
    return {
        "sources": state["relevant_tables"],
        "sql_executed": state["generated_sql"] if not state["generated_sql"].startswith("BLOCKED") else "",
        "rag_chunks_used": len(state["rag_chunks"]),
        "agent_path": ["orchestrator", "relevancy", "sql_gen", "rag", "execution", "synthesis", "persona"],
        "query_intent": state["query_intent"],
        "confidence": "high" if state["sql_results"] or state["rag_chunks"] else "low",
        "tables_searched": state["relevant_tables"],
        "tables_used": [t for t in state["relevant_tables"] if t.lower() in state.get("generated_sql", "").lower()]
    }
```

---

## FILE 10: `pipeline.py`

**Purpose:** The LangGraph StateGraph that wires all 7 agents. Compiles to a single callable `pipeline` object.

```python
from langgraph.graph import StateGraph, END
from backend.agents.state import PipelineState
from backend.agents.orchestrator_agent import orchestrator_agent
from backend.agents.relevancy_agent import relevancy_agent
from backend.agents.sql_gen_agent import sql_gen_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.execution_agent import execution_agent
from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.persona_agent import persona_agent

def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("relevancy", relevancy_agent)
    graph.add_node("sql_gen", sql_gen_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("execution", execution_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("persona", persona_agent)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "relevancy")
    
    # After relevancy, run SQL gen and RAG in parallel
    graph.add_edge("relevancy", "sql_gen")
    graph.add_edge("relevancy", "rag")
    
    # Both sql_gen and rag flow into execution and then synthesis
    graph.add_edge("sql_gen", "execution")
    graph.add_edge("execution", "synthesis")
    graph.add_edge("rag", "synthesis")
    
    graph.add_edge("synthesis", "persona")
    graph.add_edge("persona", END)

    return graph.compile()

pipeline = build_pipeline()
```

**How Person 2 calls it in `chat.py`:**
```python
from backend.agents.pipeline import pipeline
from datetime import date

initial_state = {
    "user_query": user_message,
    "user_id": str(current_user.id),
    "user_persona": current_user.persona,
    "team_id": str(current_user.team_id),
    "current_date": date.today().isoformat(),
    "query_intent": "",
    "routing_decision": {},
    "relevant_tables": [],
    "generated_sql": "",
    "sql_results": [],
    "rag_chunks": [],
    "synthesized_context": "",
    "final_answer": "",
    "chain_of_thought": {}
}

result = pipeline.invoke(initial_state)
# result["final_answer"] → send to frontend
# result["chain_of_thought"] → save to messages table and send as final SSE event
```

---

## FILE 11: `anomaly_agent.py`

**Purpose:** Standalone function (not in LangGraph pipeline) called by `anomaly_service.py` on a cron schedule. Reads `alert_configurations`, runs threshold queries against mock data, and writes to `alerts` table if thresholds are breached.

**Input:** Nothing from pipeline. Gets everything from DB directly.

**Logic:**
```
For each active alert_configuration:
  1. Run a SQL query against the configured table_name to get current metric value
  2. Compare against threshold using the condition (ABOVE / BELOW / SPIKE)
  3. If threshold breached: insert a row into alerts table
  4. Include data_snapshot (last 5 rows of the query result) in the alert

Example configuration (seeded by Person 4):
  metric_name: "failed_transaction_rate"
  table_name: "mock_transactions"
  threshold: 0.15  (15%)
  condition: "ABOVE"
  → SQL: SELECT COUNT(*) FILTER (WHERE status='FAILED') / COUNT(*)::float AS rate FROM mock_transactions WHERE created_at > NOW() - INTERVAL '1 hour'
  → If rate > 0.15, write alert with severity HIGH
```

**Function signature:**
```python
def run_anomaly_check(db_session) -> list[dict]:
    # Returns list of triggered alerts (may be empty)
    # Each dict: {title, description, severity, team_id, alert_config_id, data_snapshot}
```

---

## TESTS (write at hour 40)

### `test_sql_gen_agent.py`
Three test cases using hardcoded PipelineState fixtures:
1. Simple aggregation query — "What is total revenue this month?" → SQL contains SUM and DATE filter
2. Comparison query — "Compare North vs South region transactions" → SQL contains GROUP BY region
3. SQL_ONLY intent with no relevant tables → returns empty string, no LLM call

### `test_relevancy_agent.py`
Three test cases:
1. Transaction question → returns mock_transactions in tables list
2. API log question → returns mock_api_gateway_logs
3. RAG_ONLY intent → returns empty list without LLM call

### `test_execution_agent.py`
Four test cases:
1. Valid SELECT query → executes and returns rows
2. Query with DROP → blocked, returns empty results
3. Query referencing unauthorized table → blocked
4. Malformed SQL → returns empty results with error message

### `test_orchestrator_agent.py`
Three test cases:
1. "What is the transaction failure rate?" → query_intent = "SQL_ONLY"
2. "What are customers complaining about?" → query_intent = "RAG_ONLY"
3. "Did complaint volume increase when failures spiked?" → query_intent = "HYBRID"
