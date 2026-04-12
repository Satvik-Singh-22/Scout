<div align="center">

<img src="src/frontend/app/icon.svg" alt="Scout Logo" width="80" height="80"/>

# 🔍 SCOUT
### *Intelligent Self-Service Data Intelligence for the Enterprise*

**Ask a question in plain English. Get a trusted, boardroom-ready answer — in seconds.**

---

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-FF6B6B?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

*Built for the **NatWest Group Hackathon** — "Talk to Data: Seamless Self-Service Intelligence"*

</div>

---

## 🚀 Live Demo

**Website:** [www.teamscout.xyz](https://www.teamscout.xyz)

Try out the platform yourself using the following demo credentials:

| Role | Email | Password |
|---|---|---|
| **Platform Admin** | `admin@scout.dev` | `Admin1234!` |
| **Employee (Analyst)** | `aayush@gmail.com` | `12345678` |

---

## 🌟 What Is Scout?

Every day, banking teams sit on mountains of data they cannot reach. Analysts wait days for reports. Executives scan through dashboards they don't understand. Critical anomalies go undetected until it's too late.

**Scout changes all of that.**

Scout is a production-grade, enterprise AI data intelligence platform that lets **any employee — regardless of technical skill** — ask questions about complex banking data in plain English and receive instant, trustworthy, auditable answers. A non-technical Head of Payments gets a clean executive summary with a chart. A data engineer gets the exact SQL query, the table references, and full technical context.

Every answer comes with a transparent **Chain of Thought** — showing exactly what data was accessed, what SQL was run, and how the AI reasoned. No black boxes. No unanswered questions. Complete auditability at every step.

> *"What was our payment failure rate last Tuesday, and did the API gateway spike cause it?"*
> Scout asks no follow-up questions. It just answers — correctly, in seconds, with a chart.

---

## 🎯 The Problem We Solve

In a modern bank, data is siloed across teams, roles and systems. The status quo looks like this:

| The Old Way | The Scout Way |
|---|---|
| Analyst tickets that take days to resolve | Self-service answers in under 10 seconds |
| Dashboards only technical staff can read | Plain English summaries for every persona |
| No visibility into *how* an answer was computed | Full Chain of Thought with every response |
| Any user can query any table — no guardrails | Fine-grained, team-level governance enforced by the AI |
| Anomalies discovered only after the fact | Proactive background monitoring every 15 minutes |
| Recurring reports require manual effort | Cron-scheduled queries delivered to email or dashboard |

---

## ✅ Features (Implemented & Working)

### 🤖 Agentic AI Pipeline (LangGraph)
A fully operational 9-node LangGraph pipeline powers every query. When a question arrives, the pipeline:
1. **Orchestrates** — classifies intent (`SQL_ONLY`, `RAG_ONLY`, `HYBRID`, `GENERAL`, `SCHEMA_LOOKUP`)
2. **Filters for Relevancy** — identifies the exact tables needed from the user's permitted scope
3. **Generates SQL** — writes a secure PostgreSQL `SELECT` query with date resolution, aggregations, and LIMIT guards
4. **Runs in Parallel** — SQL generation and RAG retrieval execute simultaneously via LangGraph parallel branches
5. **Executes Safely** — read-only execution agent; `DROP`, `DELETE`, `UPDATE`, `INSERT` are structurally impossible
6. **Retries on Error** — if SQL fails, the retry agent reads the error message and self-corrects (one automatic retry)
7. **Synthesises** — merges structured SQL results with unstructured RAG context into a coherent narrative
8. **Adapts to Persona** — the persona agent tailors the final answer for `EXECUTIVE` (plain English, bullets, chart) or `TECHNICAL` (exact metrics, SQL, table references) users
9. **Builds Chain of Thought** — records every source touched, every table queried, confidence level, and agent path traversed

### 💬 Multi-Persona Chat Interface
- Users select their communication style: **EXECUTIVE** (non-technical, summary-first) or **TECHNICAL** (precise, data-rich)
- Multiple named chatrooms per user — persistent history with full conversation context passed to the AI
- Streaming responses via Server-Sent Events — the answer types in real time as it is generated
- Chain of Thought panel rendered alongside every AI response — collapsible, showing sources, SQL, RAG chunks used, query intent and confidence

### 📊 RAG over Unstructured Data (ChromaDB)
- Customer feedback, complaints, and support tickets are ingested into ChromaDB via sentence-transformers (`all-MiniLM-L6-v2`, local, Apache 2.0)
- Hybrid queries (`HYBRID` intent) automatically combine SQL numerical results with RAG text context in a single synthesised answer
- Example: *"What are customers saying about our payment failures?"* → SQL returns failure counts, RAG returns verbatim customer complaints, Persona agent merges both into one coherent answer

### 🔐 Four-Tier Governance Model (Fully Enforced)
Scout implements a role hierarchy that mirrors real enterprise governance structures:

```
PLATFORM_ADMIN
 └── Sees all 40 data tables across all teams
 └── Assigns tables to teams (writes boundary into master_config)
 └── Grants cross-team access to Enterprise Analysts in real time
     └── DATA_OWNER (per team)
         └── Registers database connections and tables
         └── Edits semantic definitions for their tables
         └── Can toggle any of their team's tables active/inactive
             └── ENTERPRISE_ANALYST
                 └── Queries across multiple teams simultaneously
                 └── Data scope enforced at pipeline level via user_team_access table
                     └── ANALYST (default)
                         └── Isolated to their own team's permitted tables
                         └── Cannot access any other team's data — enforced per query
```

Access revocation takes effect on the **next query** — no restart required.

### 🛡️ Platform Admin Governance Console
- Visual table assignment UI: drag-and-drop style panel showing all 40 mock enterprise tables and available teams
- Assign or revoke tables from teams in a single click
- AI-generated semantic definitions: when a Platform Admin assigns a table, the system automatically calls the LLM to generate a professional, accurate description of the table's business purpose based on its column schema
- User access management: view all users, their roles, and which teams they can query — update cross-team access live

### 📅 Scheduled Queries (CRON-Based)
- Users define natural language queries to run on a schedule using standard CRON expressions
- Delivery option: **Dashboard** (creates a persistent card visible on login) or **Email** (HTML formatted report sent via Gmail OAuth2)
- Alert conditions: schedule a query with an optional English-language alert condition (e.g., *"alert me if failed transactions exceed 1000"*) — the LLM evaluates the result against the condition after every run and sends an email if triggered
- Background job runs every 1 minute and claims due queries atomically to prevent duplicate execution

### 🔔 Anomaly Detection (Query-Coupled, Intelligent)

Scout's anomaly detection does not run on a fixed global timer. Instead, it activates **automatically and exclusively when a scheduled query successfully executes** — meaning it is always working with fresh, real query output, never stale aggregate snapshots.

The detection is powered by a dedicated **two-agent pipeline** that runs immediately after every successful scheduled query:

1. **Anomaly Reasoner Agent** — receives the scheduled query text, the relevant tables identified during pipeline execution, and the live SQL results. It reasons over these inputs and predicts *what anomalies could plausibly exist* in this output — for example, an unexpected spike in failure counts, a sudden drop in transaction volume, or an unusual concentration in a single region.

2. **Anomaly Checker Agent** — receives the Reasoner's predictions alongside the actual query output. It evaluates whether the predicted anomalies are genuinely present in the data, filtering out false positives. Only confirmed anomalies produce a trigger.

3. **Alert Generation** — for each confirmed anomaly, a structured `Alert` record is persisted to the database (severity: `HIGH`, `MEDIUM`, or `LOW`) and an email notification is immediately dispatched to the relevant user.

This design ensures Scout's anomaly intelligence is always contextually grounded in the query being run — not a generic threshold check against the entire dataset.

### 🧾 Data Owner Onboarding Wizard
- Guided multi-step UI for Data Owners to register database connections (`POSTGRES` / `MYSQL`) and scan available tables
- Column-level metadata registration with semantic descriptions
- Toggle tables active/inactive to include or exclude them from the AI pipeline in real time

### 📈 Executive Dashboard
- Persistent dashboard cards populated from scheduled query results
- Chart rendering with auto-inferred chart type (`BAR`, `PIE`, `TABLE`) — inferred from query result shape, no manual configuration
- Cards persist across sessions and are visible to the user on every login

### 🔑 Authentication & JWT Security
- Registration and login with bcrypt-hashed passwords
- JWT tokens (HS256, configurable expiry) for stateless auth
- Role-based route guards: `PLATFORM_ADMIN`, `DATA_OWNER`, `ENTERPRISE_ANALYST`, `ANALYST`
- Platform Admin accounts are seeded directly — never creatable via the public registration endpoint

### 📬 Email Notifications (Google OAuth2 )
- Scheduled report emails with formatted HTML output
- Threshold breach alert emails to all team members
- Inline anomaly alert emails dispatched per detection event

---

## 🏗️ Architecture

### High-Level System Design (HLD)

<p align="center">
  <img src="docs/HLD.png" alt="High-Level System Design Diagram" width="100%"/>
</p>

### How the Governance Boundary Works

The `master_config` table is the security boundary of the entire system. The AI pipeline **can only see tables whose rows exist and are `is_active = TRUE` in this table**. When a Platform Admin revokes a table, the pipeline's next invocation will not find that table in its scope and will not generate SQL against it — no code change required, no restart, no cache invalidation.

---

## 🛠️ Tech Stack

| Layer | Technology | Why We Chose It |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) | Server components, file-based routing, production-grade SSR |
| **Styling** | Tailwind CSS + shadcn/ui | Rapid, consistent design system with accessible components |
| **Charts** | Recharts | React-native charting, zero config for bar/line/pie |
| **Backend** | Python 3.11 + FastAPI | Async-first, automatic OpenAPI docs, Pydantic validation |
| **Agent Orchestration** | LangGraph | Stateful multi-agent graph with typed state, parallel branches, conditional routing |
| **LLM** | Groq API — Llama 3.1 70B | Fastest publicly available inference; free tier sufficient for demo volumes |
| **LLM Client** | langchain-groq | Handles retries, streaming, rate limits automatically |
| **Prompt Management** | langchain-core ChatPromptTemplate | Reusable, testable, separated from agent logic |
| **Output Parsing** | langchain-core JsonOutputParser + Pydantic | Typed structured output; catches malformed LLM responses gracefully |
| **Vector Store** | ChromaDB + langchain-chroma | File-based, no infrastructure, persistent across restarts |
| **Embeddings** | sentence-transformers all-MiniLM-L6-v2 | Local, free, Apache 2.0, CPU-efficient, 384-dim |
| **ORM** | SQLAlchemy 2.0 (async + sync) | Industry standard; async for API handlers, sync for pipeline agents |
| **Migrations** | Alembic | Works seamlessly with SQLAlchemy models |
| **Background Jobs** | APScheduler (AsyncIOScheduler) | In-process scheduler; no Redis or Celery required for hackathon scope |
| **Database** | PostgreSQL on Neon.tech | Serverless PostgreSQL; instant setup, no credit card required |
| **Email** | Gmail API (Google OAuth2) | Secure OAuth2 authentication; reliable HTML delivery via Gmail SMTP |
| **Deployment — Frontend** | Vercel | One-click Next.js deployment; automatic preview builds |
| **Deployment — Backend** | Render.com | FastAPI container deploy; free tier sufficient for demo |

---

## ⚡ Install & Run

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- A **PostgreSQL** database (we recommend [Neon.tech](https://neon.tech) — free, no credit card)
- **Groq API Keys** — one or more (free at [console.groq.com](https://console.groq.com))

---

### 1. Clone the Repository

```bash
git clone https://github.com/Aayushgupta2005/Scout.git
cd Scout
```

---

### 2. Backend Setup

```bash
# Step into the backend directory
cd src/backend

# Create and activate a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
```

Now open `.env` and fill in your values:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3   # Comma-separated pool of Groq API keys
GROQ_API_KEY=gsk_key
JWT_SECRET=your-minimum-32-character-secret-key
GMAIL_API_KEY=your_gmail_api_key_here       # Optional — for email delivery via Gmail
CHROMA_PERSIST_PATH=./chroma_data
```

```bash

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive API documentation: `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
# Open a new terminal and navigate to the frontend
cd src/frontend

# Install Node.js dependencies
npm install

# Configure the API URL
# Create .env.local with:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the development server
npm run dev
```

The application will be available at `http://localhost:3000`.

---

### 4. Seed Demo Data (Recommended for First Run)

Seed the 5 enterprise teams and demo users to explore the governance features:

```bash
# From src/backend (with venv active):
python scripts/seed_governance.py
```

This creates the following demo accounts:

| Email | Password | Role | Capabilities |
|---|---|---|---|
| `admin@scout.dev` | `Admin1234!` | Platform Admin | Full governance console, all 40 tables |
| `analyst.a@scout.dev` | `Analyst1234!` | Analyst | Team A (Payments) only |
| `owner.a@scout.dev` | `Owner1234!` | Data Owner | Team A table management |

---

## 💡 Usage Examples

### Example 1 — Ask a Business Question (Executive Persona)

Log in as `analyst.a@scout.dev`. Open Chat. Ask:

> *"Why did payment failures spike last Tuesday?"*

Scout will:
- Classify intent as `SQL_ONLY`
- Identify relevant tables: `mock_failed_transactions`, `mock_payment_events`
- Generate and execute a time-series SQL query grouped by error type and region
- Render a line chart
- Return a plain-English executive summary: *"Payment failures increased 34% on Tuesday 8th April, concentrated in the North region between 14:00–17:00, driven by a surge in gateway timeout errors."*

**Chain of Thought panel shows:**
```json
{
  "query_intent": "SQL_ONLY",
  "tables_searched": ["mock_failed_transactions", "mock_payment_events"],
  "sql_executed": "SELECT DATE_TRUNC('hour', created_at) AS hour, COUNT(*) AS failures...",
  "confidence": "high"
}
```


### Example 2 — Governance Demo (3-Beat Sequence)

**Beat 1:** Log in as `admin@scout.dev` → Admin Console → Assign `mock_api_gateway_logs` to Team B. Grant an Enterprise Analyst access to Team B.

**Beat 2:** Log in as the Enterprise Analyst → ask *"What is the API error rate this week?"* → Scout answers using Team B's data ✅

**Beat 3:** Log back in as admin → Revoke Team B access from the Enterprise Analyst. Log in as Enterprise Analyst → ask the same question → Scout now answers only from Team A data. The governance boundary is enforced in real time ✅


### Example 3 — Hybrid RAG Query

Ask:

> *"What are customers saying about payment failures, and how many failures occurred this month?"*

Scout will run SQL for the failure count **and** retrieve complaint text from ChromaDB in parallel, then synthesise:

> *"This month recorded 2,847 payment failures (+18% vs last month). Customer feedback consistently highlights frustration with timeout errors during peak hours, particularly on weekend evenings. Three recurring themes: slow error recovery, lack of real-time status updates, and unhelpful error messages."*

---

## ⚠️ Limitations (Honest Assessment)

In the spirit of full transparency:

| Feature | Status |
|---|---|
| MYSQL database connections | **Defined in schema** — `db_type` accepts `MYSQL` but the pipeline currently executes against PostgreSQL only |
| Semantic caching of repeated queries | **Not implemented** — every query invokes the full LangGraph pipeline; response caching would reduce LLM costs in production |
| Vector store ingestion UI | **Not implemented** — ChromaDB is pre-populated via a script (`vectorstore/ingest.py`); Data Owners cannot upload documents through the UI |
| Fine-grained column-level access control | **Not implemented** — governance operates at the table level; column-level restrictions are not enforced |

---

## 🚀 Future Scope

These are genuine next steps we would build with additional time:

- **Ollama Integration (Local LLM)** — For enterprises with strict data residency requirements, replacing Groq with a locally hosted Llama model via Ollama. Zero data leaves the corporate network. Ideal for regulated financial institutions. The architecture already abstracts the LLM provider via `get_llm()` — swapping providers requires minimal code change.
- **Docker & Docker Compose** — A single `docker compose up` to spin up all services (FastAPI, Next.js, PostgreSQL, ChromaDB) for seamless local development and production deployment.
- **Jira & Notion Connector** — Allow employees to query their project management data. *"How many tickets were opened related to payment errors last sprint?"* — all from the same Scout chat interface.
- **Microsoft Teams / Slack Bot** — Deploy Scout as a conversational bot inside existing communication tools so employees can query data without leaving the tools they already use.
- **Column-Level Access Control** — Extend the governance model to restrict access at the column level, enabling fine-grained PII protection.
- **Semantic Query Caching** — Cache frequent query results to reduce LLM calls and latency.
- **Audit Dashboard** — A dedicated view for Platform Admins showing all AI query logs, generated SQL, data sources accessed, and user activity — full regulatory auditability in a UI.

---

## 📁 Project Structure

```
Scout/
├── src/
│   ├── backend/
│   │   ├── agents/               # All LangGraph agent nodes
│   │   │   ├── pipeline.py       # Graph assembly and edge routing
│   │   │   ├── orchestrator_agent.py
│   │   │   ├── relevancy_agent.py
│   │   │   ├── sql_gen_agent.py  # SQL generation + automatic retry
│   │   │   ├── rag_agent.py
│   │   │   ├── execution_agent.py
│   │   │   ├── synthesis_agent.py
│   │   │   ├── persona_agent.py  # EXECUTIVE / TECHNICAL formatting
│   │   │   ├── anomaly_checker_agent.py
│   │   │   ├── anomaly_reasoner_agent.py
│   │   │   ├── general_agent.py
│   │   │   ├── schema_agent.py
│   │   │   ├── llm.py            # LLM key pool + provider abstraction
│   │   │   └── state.py          # Typed PipelineState definition
│   │   ├── api/                  # FastAPI route handlers
│   │   │   ├── auth.py
│   │   │   ├── chat.py           # SSE streaming + pipeline invocation
│   │   │   ├── admin.py          # Governance endpoints (Platform Admin)
│   │   │   ├── config.py         # Data Owner table registration
│   │   │   ├── scheduled.py      # CRON query management
│   │   │   ├── alerts.py
│   │   │   ├── dashboard.py
│   │   │   └── users.py
│   │   ├── db/
│   │   │   ├── models.py         # SQLAlchemy ORM models
│   │   │   └── session.py        # Async + sync session factories
│   │   ├── services/
│   │   │   ├── scheduler_service.py  # APScheduler + job logic
│   │   │   ├── anomaly_service.py    # Threshold breach detection
│   │   │   └── notification_service.py  # Gmail OAuth2 email dispatch
│   │   ├── vectorstore/
│   │   │   └── ingest.py         # ChromaDB ingestion script
│   │   ├── scripts/              # Data seeding scripts
│   │   ├── tests/                # Pytest unit tests (4 agent tests)
│   │   └── main.py               # FastAPI app entry point + lifespan
│   │
│   └── frontend/
│       ├── app/
│       │   ├── (auth)/           # Login + Register pages
│       │   └── (portal)/         # All authenticated pages
│       │       ├── chat/         # Chat list + individual chatroom
│       │       ├── dashboard/    # Executive dashboard cards
│       │       ├── scheduled/    # CRON query management
│       │       ├── alerts/       # Alert notification centre
│       │       ├── admin/        # Platform Admin governance console
│       │       ├── onboarding/   # Data Owner table wizard
│       │       └── profile/      # User settings
│       ├── components/           # Reusable UI components
│       │   ├── Chatroom.tsx
│       │   ├── ChainOfThought.tsx
│       │   ├── AdminGovernancePanel.tsx
│       │   ├── ChartRenderer.tsx
│       │   ├── ScheduledQueryForm.tsx
│       │   ├── AlertCenter.tsx
│       │   └── OnboardingFlow.tsx
│       └── lib/
│           └── api-client.ts     # Typed API client for all endpoints
│
├── docs/                         # Architecture & design diagrams
│   ├── HLD.png                   # High-Level Design diagram
│   ├── System Architecture.png
│   ├── Data Flow.png
│   ├── DATABASE ERD.png
│   ├── API ENDPOINT MAP.png
│   ├── LANGGRAPH AGENT PIPELINE.png
│   ├── ROLE & GOVERNANCE MODEL.png
│   ├── DEPLOYMENT ARCHITECTURE.png
│   ├── DEVELOPMENT TIMELINE.png
│   ├── SEQUENCE DIAGRAM — CHAT QUERY END-TO-END.png
│   └── SEQUENCE DIAGRAM — GOVERNANCE 3-BEAT DEMO.png
├── chroma_data/                  # Persisted ChromaDB vector embeddings
├── requirements.txt
└── README.md
```

---

## 🔒 Security & Compliance Posture

Scout was designed with the NatWest security mindset from day one:

| Concern | How Scout Addresses It |
|---|---|
| **SQL Injection** | AI agents only produce `SELECT` queries. Injected DDL/DML is structurally blocked by prompt constraints and output validation |
| **Data Scope Enforcement** | The `master_config` and `user_team_access` tables form a hard database-level boundary. AI agents receive only schema — never raw data — from tables outside the user's permitted scope |
| **Credential Security** | All secrets managed via environment variables. No values are committed to source control. `.env.example` provided with placeholder descriptions |
| **Authentication** | JWT with bcrypt password hashing. Role checked on every protected endpoint via FastAPI dependency injection |
| **Audit Trail** | Every AI interaction — including the full Chain of Thought JSON, generated SQL, RAG chunks used, tables accessed, and confidence level — is persisted to the `messages` table for complete auditability |
| **Read-Only Execution** | The `execution_agent` runs SQL through a read-only connection scope. Structural guardrails in both the prompt and the execution layer |

---

## 🧪 Running Tests

```bash
# From src/backend (with venv active):
pytest tests/ -v
```

Tests cover:
- **Agent Tests** — orchestrator agent intent classification, SQL generation correctness, relevancy filtering, and execution agent read-only enforcement
- **API Tests** — endpoint validation for authentication, chatroom CRUD, admin governance operations, scheduled query management, alert retrieval, and dashboard card listing

---

## 📄 API Reference

Full interactive documentation is available at `http://localhost:8000/docs` when running locally.

Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT |
| `GET` | `/chatrooms` | List user's chatrooms |
| `POST` | `/chatrooms/{id}/message` | Send a message — returns SSE stream |
| `GET` | `/admin/tables` | Platform Admin: all tables with assignments |
| `POST` | `/admin/assign` | Platform Admin: assign tables to a team |
| `PATCH` | `/admin/revoke/{id}` | Platform Admin: revoke table access |
| `POST` | `/admin/users/{id}/access` | Platform Admin: set cross-team access |
| `GET` | `/scheduled` | List scheduled queries |
| `POST` | `/scheduled` | Create a new scheduled query |
| `GET` | `/alerts` | List team alerts |
| `GET` | `/dashboard/cards` | List dashboard cards |
| `GET` | `/health` | Service health check |
| `GET` | `/health/llm` | LLM key pool status |

---

## 👥 Team

Built with intensity and conviction by **Aayush Gupta & Team** for the **NatWest Group Hackathon**.

---

## 📜 Licence

Distributed under the **Apache 2.0 License**. See `LICENSE` for full terms.

---

<div align="center">

*Scout — Because your data deserves to be heard.*

**[NatWest Hackathon 2026]**

</div>
