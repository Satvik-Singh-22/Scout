# BANQUOITE — MASTER SHARED CONTEXT (FINAL)
## Read this before reading your individual plan. Every team member and every AI receives this document.
## This is the single source of truth. If anything conflicts with an older document, THIS FILE WINS.

---

## 1. PROJECT IDENTITY

- **Product name:** Banquoite
- **Hackathon:** NatWest Group — "Talk to Data: Seamless Self-Service Intelligence"
- **License:** Apache 2.0
- **All commits:** Must be signed with `git commit -s` (DCO sign-off)
- **Single email:** Agree on one email address at hour 0. All team members use this for commits.
- **Repo:** Private on GitHub during hackathon
- **Goal:** Fully working, deployed product at hour 48

---

## 2. WHAT WE ARE BUILDING — ONE PARAGRAPH

Banquoite is an enterprise AI portal for NatWest banking teams. It lets any user — regardless of technical skill — ask natural language questions about segregated enterprise data and receive instant, trustworthy answers. A non-technical Manager gets a simplified English answer with charts. A Developer gets SQL, table references, and technical context. Every answer shows exactly which data sources were used, what SQL was executed, and how the AI reasoned — this is the Chain of Thought transparency layer. Data Owners control which of their tables the AI is allowed to access through a self-service onboarding flow. A Platform Admin sits above all teams and governs which tables each team can access. An Enterprise Analyst can query across multiple teams' data simultaneously. The system also proactively monitors data for anomalies and allows users to schedule recurring reports delivered to their dashboard or email.

---

## 3. THE THREE PILLARS (NatWest judging criteria)

1. **Clarity** — Answers simple enough for non-experts. Manager persona enforces this.
2. **Trust** — Chain of Thought shows every source, table, and SQL used. Data Owner controls access. Platform Admin governs the entire estate.
3. **Speed** — Near-instant responses. LangGraph runs SQL generation and RAG retrieval in parallel.

---

## 4. FULL TECH STACK

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) | Fast to build, server components reduce boilerplate |
| Styling | Tailwind CSS + shadcn/ui | Pre-built components, no custom CSS time cost |
| Charts | Recharts | React-native, simple API, sufficient for hackathon |
| Backend | Python 3.11 + FastAPI | Async, fast to write, auto OpenAPI docs |
| Agent Orchestration | LangGraph 0.2.x | Stateful multi-agent graph, parallel branches, typed state |
| LLM Client | langchain-groq (ChatGroq) | Handles retries, streaming, rate limits automatically |
| Prompt Templates | langchain-core ChatPromptTemplate | Reusable, testable, iterable without touching agent logic |
| Output Parsing | langchain-core JsonOutputParser + Pydantic | Typed structured output, catches malformed LLM responses |
| Vector Store | langchain-community Chroma + ChromaDB | Local, no setup, file-based persistence |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | Local, free, Apache 2.0, 384-dim, fast on CPU |
| Document Loading | langchain-community CSVLoader + RecursiveCharacterTextSplitter | One-time ingestion of customer reviews |
| Chat History | langchain-community SQLChatMessageHistory | Persists conversation context to PostgreSQL automatically |
| ORM | SQLAlchemy 2.0 | Industry standard, async support |
| Migrations | Alembic | Works with SQLAlchemy |
| Background Jobs | APScheduler | Runs scheduled queries and anomaly detection on cron |
| Primary Database | PostgreSQL on Neon.tech (free tier) | Serverless, no credit card, instant setup |
| LLM | Groq API — llama-3.1-70b-versatile | Free tier: 14,400 req/day, fastest inference publicly available |
| Email | Resend Python SDK | 3,000 free emails/month, 2-minute setup |
| Deployment — Frontend | Vercel (free) | One-click Next.js deploy |
| Deployment — Backend | Render.com or Railway.app (free tier) | FastAPI container deploy |

**Packages — backend requirements.txt:**
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
apscheduler==3.10.4
langchain-core==0.3.0
langchain-groq==0.2.0
langchain-community==0.3.0
langchain-chroma==0.1.4
langgraph==0.2.0
sentence-transformers==2.7.0
chromadb==0.5.3
resend==2.0.0
faker==24.0.0
pydantic==2.7.0
python-dotenv==1.0.1
```

**Packages — frontend package.json dependencies:**
```json
{
  "next": "14.2.3",
  "react": "18.3.1",
  "react-dom": "18.3.1",
  "tailwindcss": "3.4.3",
  "recharts": "2.12.5",
  "lucide-react": "0.378.0",
  "js-cookie": "3.0.5",
  "eventsource-parser": "1.1.2"
}
```

---

## 5. COMPLETE DATABASE SCHEMA

All tables live in the same PostgreSQL database on Neon.tech.

### Core Application Tables

```sql
-- Teams table (create first — users references it)
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Users table
-- role column has 4 valid values:
--   DATA_OWNER    → can register tables via onboarding wizard
--   ANALYST       → can query their own team's data only
--   PLATFORM_ADMIN → can see all 40 tables, assign tables to teams, grant cross-team access
--   ENTERPRISE_ANALYST → can query across 2+ teams' data simultaneously
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  persona VARCHAR(20) NOT NULL CHECK (persona IN ('MANAGER', 'DEVELOPER')),
  role VARCHAR(20) NOT NULL DEFAULT 'ANALYST' CHECK (role IN ('DATA_OWNER', 'ANALYST', 'PLATFORM_ADMIN', 'ENTERPRISE_ANALYST')),
  team_id UUID REFERENCES teams(id),  -- organisational team (can be NULL for PLATFORM_ADMIN)
  created_at TIMESTAMP DEFAULT NOW()
);

-- Cross-team access map — PLATFORM_ADMIN inserts rows here to grant ENTERPRISE_ANALYST access
-- For a normal ANALYST: one row exists (their own team)
-- For ENTERPRISE_ANALYST: two or more rows exist (multiple teams)
-- PLATFORM_ADMIN has no rows here — they use admin endpoints directly
CREATE TABLE user_team_access (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  team_id UUID NOT NULL REFERENCES teams(id),
  granted_by UUID REFERENCES users(id),  -- the PLATFORM_ADMIN who granted it
  granted_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, team_id)
);

-- Database connections registered by Data Owners
CREATE TABLE database_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  name VARCHAR(255) NOT NULL,
  connection_string_enc TEXT NOT NULL,
  db_type VARCHAR(20) NOT NULL CHECK (db_type IN ('POSTGRES', 'MYSQL')),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Master Config — the security boundary. AI only reads tables registered here.
-- team_id here means "which team OWNS and can use this table"
CREATE TABLE master_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  db_connection_id UUID NOT NULL REFERENCES database_connections(id),
  team_id UUID NOT NULL REFERENCES teams(id),
  table_name VARCHAR(255) NOT NULL,
  semantic_definition TEXT NOT NULL,
  columns_metadata JSONB NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Chatrooms — one per user, isolated
CREATE TABLE chatrooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Messages — stores full chat history including Chain of Thought
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chatroom_id UUID NOT NULL REFERENCES chatrooms(id),
  role VARCHAR(20) NOT NULL CHECK (role IN ('USER', 'ASSISTANT')),
  content TEXT NOT NULL,
  chain_of_thought JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled queries
CREATE TABLE scheduled_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  query_text TEXT NOT NULL,
  cron_expression VARCHAR(100) NOT NULL,
  delivery VARCHAR(20) NOT NULL CHECK (delivery IN ('EMAIL', 'DASHBOARD')),
  delivery_email VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  last_run_at TIMESTAMP,
  next_run_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Results of scheduled query runs
CREATE TABLE scheduled_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scheduled_query_id UUID NOT NULL REFERENCES scheduled_queries(id),
  result_data JSONB NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
  executed_at TIMESTAMP DEFAULT NOW()
);

-- Alert threshold definitions — seeded for demo
CREATE TABLE alert_configurations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  metric_name VARCHAR(255) NOT NULL,
  table_name VARCHAR(255) NOT NULL,
  threshold FLOAT NOT NULL,
  condition VARCHAR(20) NOT NULL CHECK (condition IN ('ABOVE', 'BELOW', 'SPIKE')),
  is_active BOOLEAN DEFAULT TRUE
);

-- Triggered alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  alert_config_id UUID REFERENCES alert_configurations(id),
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  severity VARCHAR(20) NOT NULL CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW')),
  data_snapshot JSONB,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard cards — persistent scheduled report outputs visible to Manager
CREATE TABLE dashboard_cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  query_result JSONB NOT NULL,
  chart_type VARCHAR(20) NOT NULL CHECK (chart_type IN ('BAR', 'LINE', 'PIE', 'TABLE')),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Total: 12 core application tables (including the new `user_team_access` table).

### Mock Enterprise Data Tables (40 tables total)

All mock tables use prefix `mock_`. These are seeded by Person 4 before the demo.
They represent data owned by 5 teams: Payments (A), Operations (B), Risk (C), Customer (D), Finance (E).

**Transactional domain — owned by Team A "Payments" (12 tables):**
- `mock_transactions` (250,000 rows)
- `mock_failed_transactions`
- `mock_payment_events`
- `mock_refunds`
- `mock_chargebacks`
- `mock_transaction_fees`
- `mock_fx_conversions`
- `mock_batch_payments`
- `mock_recurring_payments`
- `mock_payment_methods`
- `mock_merchant_categories`
- `mock_transaction_limits`

**System/Operations domain — owned by Team B "Operations" (10 tables):**
- `mock_api_gateway_logs` (100,000 rows)
- `mock_tyk_gateway_events`
- `mock_login_events`
- `mock_system_health_metrics`
- `mock_service_latency_logs`
- `mock_error_logs`
- `mock_deployment_events`
- `mock_audit_trail`
- `mock_session_events`
- `mock_notification_delivery_logs`

**Risk domain — owned by Team C "Risk" (6 tables):**
- `mock_kyc_records`
- `mock_customer_complaints`
- `mock_customer_support_tickets`
- `mock_customer_churn_events`
- `mock_fraud_cases`
- `mock_compliance_flags`

**Customer domain — owned by Team D "Customer" (6 tables):**
- `mock_customers` (50,000 rows)
- `mock_customer_accounts`
- `mock_customer_segments`
- `mock_customer_onboarding`
- `mock_customer_feedback`
- `mock_customer_lifetime_value`

**Finance domain — owned by Team E "Finance" (6 tables):**
- `mock_products`
- `mock_loan_applications`
- `mock_revenue_monthly`
- `mock_cost_centres`
- `mock_branch_performance`
- `mock_regulatory_reports`

---

## 6. THE ROLE HIERARCHY — COMPLETE DEFINITION

This is the governance model. All four team members must understand this deeply.

```
PLATFORM_ADMIN
│  • Has no team_id (NULL) — belongs to no single team
│  • Sees ALL 40 mock_ tables in the admin panel
│  • Assigns tables to teams (writes master_config rows)
│  • Grants cross-team access to ENTERPRISE_ANALYSTs (writes user_team_access rows)
│  • Uses /admin/* endpoints exclusively
│  • Cannot use the chatroom (no data scope — prevents confusion)
│
├── DATA_OWNER (one per team)
│      • Belongs to a single team (team_id is set)
│      • Can access /config/* endpoints to register DB connections and tables
│      • Can edit semantic definitions for their team's tables
│      • Can toggle their team's tables on/off in master_config
│
├── ENTERPRISE_ANALYST
│      • Has a home team_id (organisational affiliation)
│      • Has 2+ rows in user_team_access (one per team they can query)
│      • The pipeline fetches allowed_team_ids from user_team_access
│      • Can query across ALL their assigned teams simultaneously in one chat message
│      • Cannot see tables not explicitly granted by PLATFORM_ADMIN
│
└── ANALYST (default role)
       • Has a home team_id
       • Has exactly 1 row in user_team_access (their own team) — seeded at registration
       • Can only query their own team's assigned tables
       • Completely isolated from other teams' data
```

### Demo Scenario for Governance (3-beat sequence for presentation):
**Beat 1 — Isolation (ANALYST):**
Log in as Team A analyst. Ask "What is total payment volume this week?" → AI uses only Team A's payment tables.

**Beat 2 — Cross-domain synthesis (ENTERPRISE_ANALYST):**
Log in as Enterprise Analyst (has access to Team A Payments + Team B Operations). Ask "Did the spike in API errors last Tuesday cause the increase in payment failures?" → pipeline fetches tables from BOTH teams, SQL joins across domains, single synthesized answer.

**Beat 3 — Governance control (PLATFORM_ADMIN):**
Log in as Platform Admin. Revoke Team B access from the Enterprise Analyst. Log back in as Enterprise Analyst, run the same query → answer now only reflects Team A's data. Boundary enforced in real time.

---

## 7. PIPELINE STATE — FROZEN DEFINITION

**Every AI and every team member must use this exact definition. Do not add or remove fields without a team decision.**

```python
# backend/agents/state.py
from typing import TypedDict, List

class PipelineState(TypedDict):
    user_query: str           # The raw question from the user
    user_id: str              # UUID of the user (from JWT)
    user_persona: str         # "MANAGER" or "DEVELOPER"
    team_id: str              # User's home team UUID (organisational affiliation)
    allowed_team_ids: List[str]  # List of team UUIDs this user's pipeline can access
                                  # For ANALYST: [team_id] — one item
                                  # For ENTERPRISE_ANALYST: [team_a_id, team_b_id, ...]
    current_date: str         # ISO date string e.g. "2025-01-15"
    query_intent: str         # "SQL_ONLY" | "RAG_ONLY" | "HYBRID"
    routing_decision: dict    # {"use_sql": bool, "use_rag": bool, "reasoning": str}
    relevant_tables: list     # List of table name strings selected by relevancy agent
    generated_sql: str        # The SQL string from sql_gen agent
    sql_results: list         # List of row dicts from execution agent
    rag_chunks: list          # List of text chunk strings from rag agent
    synthesized_context: str  # Combined narrative from synthesis agent
    final_answer: str         # Final user-facing answer from persona agent
    chain_of_thought: dict    # Full CoT JSON built by persona agent
```

**KEY CHANGE from previous version:** `allowed_team_ids` (List[str]) is NEW. This replaces the single-team logic. Person 2 populates it in chat.py by querying `user_team_access`. Person 1 uses it in `relevancy_agent.py`.

---

## 8. COMPLETE API CONTRACTS

### Authentication

```
POST /auth/register
Body: { email, password, name, persona: "MANAGER"|"DEVELOPER", role: "DATA_OWNER"|"ANALYST"|"ENTERPRISE_ANALYST", team_name: str }
Note: PLATFORM_ADMIN accounts are seeded directly — not created via register endpoint.
Response: { access_token: str, token_type: "bearer", user: { id, email, name, persona, role } }

POST /auth/login
Body: { email, password }
Response: { access_token: str, token_type: "bearer", user: { id, email, name, persona, role } }
```

### Chat

```
GET /chatrooms
Auth: Bearer token
Response: [{ id, name, created_at, last_message_preview }]

POST /chatrooms
Auth: Bearer token
Body: { name: str }
Response: { id, name, created_at }

GET /chatrooms/{chatroom_id}/messages
Auth: Bearer token
Response: [{ id, role, content, chain_of_thought, created_at }]

POST /chatrooms/{chatroom_id}/message
Auth: Bearer token
Body: { query: str }
Response: text/event-stream
  Events:
    data: {"type": "chunk", "content": "word "}
    data: {"type": "done", "chain_of_thought": { sources, sql_executed, rag_chunks_used, agent_path, query_intent, confidence, tables_searched, tables_used }}
    data: {"type": "error", "message": "error string"}
```

### Config (Data Owner only)

```
POST /config/connections
Auth: Bearer token (role=DATA_OWNER required)
Body: { name, db_type: "POSTGRES"|"MYSQL", connection_string }
Response: { id, name, db_type, created_at }

GET /config/scan/{connection_id}
Auth: Bearer token (role=DATA_OWNER required)
Response: [{ table_name, column_count }]

POST /config/tables
Auth: Bearer token (role=DATA_OWNER required)
Body: { db_connection_id, table_name, semantic_definition, columns_metadata: [{ name, type, description }] }
Response: { id, table_name, is_active, created_at }

GET /config/tables
Auth: Bearer token
Response: [{ id, table_name, semantic_definition, columns_metadata, is_active }]

PATCH /config/tables/{id}
Auth: Bearer token (role=DATA_OWNER required)
Body: { is_active?: bool, semantic_definition?: str }
Response: { id, table_name, is_active, semantic_definition }
```

### Admin (Platform Admin only)

```
GET /admin/tables
Auth: Bearer token (role=PLATFORM_ADMIN required)
Response: [{ table_name, column_count, team_assignments: [{ team_id, team_name, is_active }] }]
Description: Returns ALL mock_ tables in the database with their current team assignments.

GET /admin/teams
Auth: Bearer token (role=PLATFORM_ADMIN required)
Response: [{ id, name, table_count, member_count }]

POST /admin/assign
Auth: Bearer token (role=PLATFORM_ADMIN required)
Body: { team_id: str, table_assignments: [{ table_name, semantic_definition, columns_metadata }] }
Response: { assigned_count: int, team_id: str }
Description: Creates master_config rows for the given team. Uses a hardcoded db_connection_id for demo.

PATCH /admin/revoke/{master_config_id}
Auth: Bearer token (role=PLATFORM_ADMIN required)
Response: { id, is_active: false }
Description: Sets is_active=FALSE on a master_config row, immediately removing it from the pipeline.

GET /admin/users
Auth: Bearer token (role=PLATFORM_ADMIN required)
Response: [{ id, name, email, role, team_id, team_name, accessible_teams: [{ team_id, team_name }] }]

POST /admin/users/{user_id}/access
Auth: Bearer token (role=PLATFORM_ADMIN required)
Body: { team_ids: [str] }  -- full replacement of access list
Response: { user_id, accessible_teams: [{ team_id, team_name }] }
Description: Replaces all user_team_access rows for this user. Used to grant/revoke cross-team access.
```

### Scheduled Queries

```
GET /scheduled
Auth: Bearer token
Response: [{ id, query_text, cron_expression, delivery, is_active, last_run_at, next_run_at }]

POST /scheduled
Auth: Bearer token
Body: { query_text, cron_expression, delivery: "EMAIL"|"DASHBOARD", delivery_email?: str }
Response: { id, query_text, cron_expression, delivery, is_active, next_run_at }

PATCH /scheduled/{id}
Auth: Bearer token
Body: { is_active: bool }
Response: { id, is_active }

GET /scheduled/{id}/history
Auth: Bearer token
Response: [{ id, status, result_data, executed_at }]
```

### Alerts

```
GET /alerts
Auth: Bearer token
Response: [{ id, title, description, severity, data_snapshot, is_read, created_at }]

PATCH /alerts/{id}/read
Auth: Bearer token
Response: { id, is_read: true }
```

### Dashboard Cards

```
GET /dashboard/cards
Auth: Bearer token
Response: [{ id, title, query_result, chart_type, created_at }]
```

### Users

```
GET /users/me
Auth: Bearer token
Response: { id, email, name, persona, role, team_id, accessible_teams: [{ team_id, team_name }] }

PATCH /users/me
Body: { persona?: "MANAGER"|"DEVELOPER", name?: str }
Auth: Bearer token
Response: { id, email, name, persona }
```

---

## 9. ENVIRONMENT VARIABLES (.env.example)

Every team member uses this. Never commit actual values.

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# Groq LLM
GROQ_API_KEY=gsk_...

# Email
RESEND_API_KEY=re_...

# Auth
JWT_SECRET=your-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ChromaDB
CHROMA_PERSIST_PATH=./chroma_data

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Banquoite
```

---

## 10. FOLDER STRUCTURE — COMPLETE (FINAL)

```
/
├── backend/
│   ├── agents/
│   │   ├── state.py                    ← UPDATED: added allowed_team_ids field
│   │   ├── orchestrator_agent.py
│   │   ├── relevancy_agent.py          ← UPDATED: uses allowed_team_ids (IN query)
│   │   ├── sql_gen_agent.py
│   │   ├── rag_agent.py
│   │   ├── execution_agent.py
│   │   ├── synthesis_agent.py
│   │   ├── persona_agent.py
│   │   ├── pipeline.py
│   │   └── anomaly_agent.py
│   ├── api/
│   │   ├── auth.py                     ← UPDATED: 4 roles, require_platform_admin guard
│   │   ├── chat.py                     ← UPDATED: populates allowed_team_ids from user_team_access
│   │   ├── config.py
│   │   ├── admin.py                    ← NEW: /admin/* endpoints
│   │   ├── scheduled.py
│   │   ├── alerts.py
│   │   ├── dashboard.py
│   │   └── users.py
│   ├── db/
│   │   ├── models.py                   ← UPDATED: UserTeamAccess model, 4 roles
│   │   ├── session.py
│   │   └── migrations/
│   ├── services/
│   │   ├── scheduler_service.py
│   │   ├── anomaly_service.py
│   │   └── notification_service.py
│   ├── vectorstore/
│   │   ├── chroma_manager.py
│   │   └── ingest.py
│   ├── mock_data/
│   │   ├── generate_transactions.py
│   │   ├── generate_customers.py
│   │   ├── generate_system_logs.py
│   │   ├── generate_products_finance.py
│   │   ├── generate_geography.py
│   │   ├── seed_alerts.py
│   │   ├── seed_master_config.py       ← UPDATED: seeds 5 teams, assigns tables per team
│   │   └── seed_governance.py          ← NEW: seeds PLATFORM_ADMIN + ENTERPRISE_ANALYST demo users
│   ├── tests/
│   │   ├── test_orchestrator_agent.py
│   │   ├── test_sql_gen_agent.py
│   │   ├── test_relevancy_agent.py
│   │   └── test_execution_agent.py
│   ├── main.py                         ← UPDATED: includes admin.router
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (portal)/
│   │   │   ├── chat/page.tsx
│   │   │   ├── chat/[chatroom_id]/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── onboarding/page.tsx
│   │   │   ├── alerts/page.tsx
│   │   │   ├── scheduled/page.tsx
│   │   │   ├── scheduled/[id]/history/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   └── admin/page.tsx          ← NEW: PLATFORM_ADMIN governance UI
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── Chatroom.tsx
│   │   ├── ChainOfThought.tsx
│   │   ├── ManagerDashboard.tsx
│   │   ├── DeveloperView.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── AlertCenter.tsx
│   │   ├── ScheduledQueryForm.tsx
│   │   ├── OnboardingFlow.tsx
│   │   ├── DashboardCard.tsx
│   │   └── AdminGovernancePanel.tsx    ← NEW: table assignment + cross-team access UI
│   ├── lib/
│   │   └── api-client.ts               ← UPDATED: admin types + functions
│   ├── package.json
│   └── .env.local.example
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## 11. DEPENDENCY CHAIN — MUST READ

**Hour 0–2 (all four together — do not split until these are done):**
1. Create GitHub repo (private). Set single email for commits.
2. Write and commit `state.py` — every field including `allowed_team_ids`. Frozen after this.
3. Write and commit API contracts (copy from section 8 above into a shared doc).
4. Person 2 writes `models.py` including `UserTeamAccess`. Person 4 runs Neon DB setup and Alembic migration.
5. All confirm: Neon DB reachable, Groq API key working, Vercel + Render accounts ready.

**After hour 2 — parallel tracks:**
- Person 1: builds agents. Uses `allowed_team_ids` (list) in relevancy agent. Build against test fixtures.
- Person 2: builds all routes including `admin.py`. Returns mock responses where pipeline not ready.
- Person 3: uses MSW to mock all API calls including new `/admin/*` endpoints.
- Person 4: runs data generation, seeds 5 teams, seeds governance demo users.

**Integration checkpoint — hour 16:**
- Person 1: `pipeline.invoke()` returning real answer on a test query with `allowed_team_ids` populated.
- Person 2: `/chatrooms/{id}/message` endpoint populating `allowed_team_ids` from `user_team_access` table.
- First live end-to-end query must succeed by hour 20.

**Integration checkpoint — hour 24:**
- Person 3 removes MSW mocks. Connects to live backend.
- Streaming answer must appear in browser.
- Admin page must render tables list from `/admin/tables`.

**Integration checkpoint — hour 32:**
- All pages functional against deployed backend.
- Governance demo (3-beat sequence) must work end-to-end.

**Code freeze — hour 44:**
- No new features. Bug fixes only.
- All four rehearse demo twice including 3-beat governance sequence.

---

## 12. DEMO SCENARIOS — ALIGNED TO ALL 4 NATWEST USE CASES

**Use Case 1 — Understand what changed:**
"Why did transaction failures spike last Tuesday?" — Manager persona, Team A analyst.
Expected: Simplified explanation identifying the spike period + region, bar chart, CoT shows SQL + table sources.

**Use Case 2 — Compare:**
"Compare successful vs failed payments in the North vs South region this month" — Developer persona.
Expected: SQL with GROUP BY region and status, date resolved to current month.

**Use Case 3 — Breakdown (decomposition):**
"Show me the breakdown of total transaction volume by merchant category this quarter" — Manager persona.
Expected: Pie or bar chart showing each category's share.

**Use Case 4 — Summarize:**
"Give me a summary of system health and payment performance for this week" — Enterprise Analyst persona (has access to Team A Payments + Team B Operations).
Expected: Multi-metric summary drawing from BOTH teams' tables simultaneously.

**Use Case 5 (bonus — hybrid/RAG):**
"What are customers saying about payment failures?" — Hybrid query. Expects RAG (customer reviews) + SQL (failure counts) synthesized together.

**Use Case 6 (bonus — governance demo):**
3-beat sequence described in Section 6 above. PLATFORM_ADMIN assigns/revokes tables live. Enterprise Analyst queries before and after. Results change in real time.

Person 1 must confirm Use Cases 1–5 work reliably before hour 44.

---

## 13. THE 5 DEMO TEAMS — FIXED ASSIGNMENT

These teams are seeded by Person 4's `seed_master_config.py`. The names and data domains are fixed.

| Team Name | Tables Assigned | Demo Role |
|---|---|---|
| Team A — Payments | All 12 `mock_transactions*` tables | Standard team demo |
| Team B — Operations | All 10 `mock_api_gateway_logs*` / system tables | Cross-team demo partner |
| Team C — Risk | 6 risk tables (kyc, fraud, compliance) | Isolated team |
| Team D — Customer | 6 customer tables | Isolated team |
| Team E — Finance | 6 finance tables | Isolated team |

**Demo users seeded by `seed_governance.py`:**
- `admin@banquoite.dev` / `Admin1234!` → role=PLATFORM_ADMIN, team_id=NULL
- `enterprise@banquoite.dev` / `Enterprise1234!` → role=ENTERPRISE_ANALYST, home team=Team A, user_team_access rows for Team A + Team B
- `analyst.a@banquoite.dev` / `Analyst1234!` → role=ANALYST, team=Team A
- `analyst.b@banquoite.dev` / `Analyst1234!` → role=ANALYST, team=Team B
- `owner.a@banquoite.dev` / `Owner1234!` → role=DATA_OWNER, team=Team A

---

## 14. COMPLIANCE CHECKLIST (Person 4 verifies at hour 44)

- [ ] `README.md` complete
- [ ] `LICENSE` file contains Apache 2.0 text
- [ ] `.env.example` has all variables, no values, with description comments
- [ ] No hardcoded secrets anywhere (`grep -r "gsk_" .` returns nothing)
- [ ] All commits signed with `-s` flag
- [ ] `requirements.txt` and `package.json` present and functional
- [ ] Features labeled partial in README: alert config UI, semantic caching, multi-DB encryption
- [ ] `tests/` folder has minimum 4 test files
- [ ] Repo is private on GitHub
- [ ] `seed_governance.py` has been run and demo users exist in DB
- [ ] All 5 demo queries verified working
- [ ] Governance 3-beat demo sequence verified working
