<!--
Copyright 2026 The SCOUT Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

<div align="center">

<img src="src/frontend/app/icon.svg" alt="Scout Logo" width="80" height="80"/>

# SCOUT
### *Smart Data Conversational & Operational Understanding Tool*

**Ask a question in plain English. Get a trusted, decision-ready answer — in seconds.**

---

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-FF6B6B?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

*Talk to Data: Seamless Self-Service Intelligence*

</div>

---

## Live Demo

**Website:** [www.teamscout.xyz](https://www.teamscout.xyz)

Try out the platform yourself using the following demo credentials:

| Role | Email | Password |
|---|---|---|
| **Platform Admin** | `admin@scout.dev` | `Admin1234!` |
| **Employee (Analyst)** | `aayush@gmail.com` | `12345678` |

---

## What Is Scout?

Every day, banking teams sit on mountains of data they cannot reach. Analysts wait days for reports. Executives scan through dashboards they don't understand. Critical anomalies go undetected until it's too late.

**Scout changes all of that.**

Scout is a production-grade, enterprise AI data intelligence platform that lets **any employee — regardless of technical skill** — ask questions about complex banking data in plain English and receive instant, trustworthy, auditable answers. A non-technical Head of Payments gets a clean executive summary with a chart. A data engineer gets the exact SQL query, the table references, and full technical context.

Every answer comes with a transparent **Chain of Thought** — showing exactly what data was accessed, what SQL was run, and how the AI reasoned. No black boxes. No unanswered questions. Complete auditability at every step.

> *"What was our payment failure rate last Tuesday, and did the API gateway spike cause it?"*
> Scout asks no follow-up questions. It just answers — correctly, in seconds, with a chart.

---

## The Problem We Solve

In a modern bank, data is siloed across teams, roles and systems. The status looks like this:

| <span style="color: #ef4444; font-weight: 600;">The Old Way</span> | <span style="color: #22c55e; font-weight: 600;">The Scout Way</span> |
|---|---|
| Days of waiting for analysts | Answers in seconds, on your own |
| Hard-to-read dashboards for technical users | Plain English insights for everyone |
| No clarity on how answers are generated | Complete transparency with every answer |
| Unrestricted data access, no control | Secure, team-level governance by design |
| Issues discovered too late | Proactive monitoring in real time |
| Manual effort for recurring reports | Automated reports, delivered on schedule |
| Missed anomalies and delayed responses | Real-time anomaly detection & **Alerting** |

---

<p align="center">
  <img src="assets/features-previews.png" alt="Scout Features Overview" width="100%"/>
</p>

### Functional Requirements

#### Multi-Persona Chat Interface
- Users can choose their preferred communication style: **EXECUTIVE** (concise, business-friendly summaries) or **TECHNICAL** (detailed, data-rich responses)
- Multiple named chatrooms per user with persistent history and full conversational context
- Real-time streaming responses via Server-Sent Events — answers are generated live as you type
- A transparent **Chain of Thought** panel accompanies every response, showing sources, SQL queries, retrieved context, intent classification, and confidence levels

---

#### Scheduled Queries (CRON-Based)
- Define natural language queries and schedule them using standard CRON expressions
- Flexible delivery options:
  - **Dashboard** — persistent cards visible on login  
  - **Email** — professionally formatted HTML reports via Gmail OAuth2  
- Intelligent alert conditions (e.g., *"alert me if failed transactions exceed 1000"*) evaluated automatically after each run
- Background scheduler executes every minute, ensuring reliable and duplicate-free job processing

---

#### Anomaly Detection & **Alerting** (Query-Coupled Intelligence)

Scout’s anomaly detection is not based on static intervals. Instead, it is **tightly coupled with scheduled query execution**, ensuring all analysis is performed on fresh, real-time data.

A dedicated two-agent pipeline powers this system:

1. **Anomaly Reasoner Agent**  
   Analyzes the query context, relevant tables, and live SQL results to identify potential anomalies — such as spikes in failures, drops in volume, or unusual data distributions.

2. **Anomaly Checker Agent**  
   Validates the predicted anomalies against actual results, eliminating false positives and confirming only meaningful deviations.

3. **Alert Generation**  
   Confirmed anomalies generate structured `Alert` records (severity: `HIGH`, `MEDIUM`, `LOW`) and trigger immediate email notifications.

This design ensures anomaly detection remains **context-aware, precise, and actionable**, rather than relying on generic threshold-based monitoring.

---

#### Email Notifications (Google OAuth2)
- Automated delivery of scheduled reports in clean, HTML format
- Threshold-based alert emails sent to relevant stakeholders
- Real-time anomaly alerts triggered instantly upon detection

---

#### Executive Dashboard
- Persistent dashboard cards generated from scheduled query outputs
- Automatic chart type inference (`BAR`, `PIE`, `TABLE`) based on result structure — zero manual configuration required
- Cards persist across sessions, giving users a consistent and always-updated view of key metrics

---

#### Platform Admin — Central Governance & Control

The **Platform Admin** acts as the central authority for data governance, ensuring secure, structured, and compliant access across the organization.

- **Complete Data Visibility** — Unified access to all data tables across teams  
- **Dynamic Table Assignment** — Real-time assignment and revocation of tables, enforced via the `master_config` governance layer  
- **AI-Generated Semantic Definitions** — Automatic generation of business-friendly table descriptions using AI  
- **Visual Governance Interface** — Intuitive drag-and-drop UI for managing tables and teams  
- **One-Click Access Control** — Instant updates to data access with immediate system-wide enforcement  
- **User Access Management** — Centralized control over users, roles, and cross-team permissions with live updates  

---

#### Data Owner Onboarding Wizard
- Guided, step-by-step interface for registering database connections (`POSTGRES`) and scanning available tables
- Column-level metadata configuration with semantic descriptions
- Real-time table activation and deactivation for dynamic pipeline inclusion

---

### Non-Functional Requirements

---
#### Agentic AI Pipeline (LangGraph)

A production-grade **9-node LangGraph pipeline** orchestrates every query:

1. **Orchestration** — Classifies intent (`SQL_ONLY`, `RAG_ONLY`, `HYBRID`, `GENERAL`, `SCHEMA_LOOKUP`)  
2. **Relevancy Filtering** — Identifies only the necessary tables within the user’s access scope  
3. **SQL Generation** — Produces secure, optimized PostgreSQL `SELECT` queries  
4. **Parallel Execution** — Runs SQL and RAG retrieval simultaneously  
5. **Safe Execution** — Enforces strict read-only operations (`DROP`, `DELETE`, etc. are impossible)  
6. **Retry Mechanism** — Automatically corrects and retries failed queries once  
7. **Synthesis** — Combines structured and unstructured results into a coherent answer  
8. **Persona Adaptation** — Formats output for EXECUTIVE or TECHNICAL users  
9. **Chain of Thought Generation** — Logs full reasoning, sources, and execution path for transparency  

---

#### Authentication & JWT Security
- Secure registration and login with bcrypt-hashed passwords  
- Stateless authentication using JWT tokens (HS256, configurable expiry)  
- Role-based access control: `PLATFORM_ADMIN`, `DATA_OWNER`, `ENTERPRISE_ANALYST`, `ANALYST`  
- Platform Admin accounts are securely seeded and cannot be created via public endpoints  

---
## Architecture & System Design Diagrams

To ensure complete clarity, transparency, and production-readiness, Scout is supported by a comprehensive set of **system design and architecture diagrams**. These diagrams collectively capture every layer of the platform — from high-level system flow to deep internal pipelines and governance models.

Each diagram has been carefully designed to visually communicate how Scout operates end-to-end in a real-world enterprise environment.

### Included Diagrams

- **System Architecture** — End-to-end view of frontend, backend, agents, and data layers  
- **High-Level Design (HLD)** — Core system components and their interactions  
- **Data Flow** — Movement of data across the pipeline (SQL, RAG, synthesis)  
- **Database ERD** — Complete schema design with relationships and constraints  
- **API Endpoint Map** — All backend routes and their responsibilities  
- **LangGraph Agent Pipeline** — Detailed 9-node agent orchestration flow  
- **Role & Governance Model** — Access control, team boundaries, and permissions  
- **Deployment Architecture** — Infrastructure layout and service deployment strategy  
- **Development Timeline** — Build phases and implementation progression  
- **Sequence Diagram — Chat Query End-to-End** — Full lifecycle of a user query  
- **Sequence Diagram — Governance Demo** — Real-time access control enforcement flow  

These diagrams are located in the `/docs` directory and are intended to provide:

- **Instant understanding** for reviewers and judges  
- **Strong architectural credibility** for enterprise use  
- **Clear communication** of complex AI + data workflows  
- **Visual storytelling** of how Scout operates at scale  

> Together, these diagrams transform Scout from just a project into a **fully engineered, production-grade system**.

---

## Install & Run

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

## Usage Examples

### Example 1 — Ask a Business Question (Executive Persona)

Log in as `analyst.a@scout.dev`. Open Chat. Ask:

> *"Why did payment failures spike last Tuesday?"*

<br/>
<p align="center">
  <img src="assets/example-1.jpeg" alt="Example 1 - Business Question" width="100%"/>
</p>
<br/>

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

<p align="center">
  <img src="assets/example-2a.jpeg" alt="Example 2A - Admin Console" width="100%"/>
</p>

**Beat 2:** Log in as the Enterprise Analyst → ask *"What is the API error rate this week?"* → Scout answers using Team B's data 

**Beat 3:** Log back in as admin → Revoke Team B access from the Enterprise Analyst. Log in as Enterprise Analyst → ask the same question → Scout now answers only from Team A data. The governance boundary is enforced in real time 

<p align="center">
  <img src="assets/example-2b.jpeg" alt="Example 2B - Governance Boundary Enforced" width="100%"/>
</p>

## Future Scope

These are genuine next steps we would build with additional time:

- **Ollama Integration (Local LLM)** — For enterprises with strict data residency requirements, replacing Groq with a locally hosted Llama model via Ollama. Zero data leaves the corporate network. Ideal for regulated financial institutions. The architecture already abstracts the LLM provider via `get_llm()` — swapping providers requires minimal code change.
- **Docker & Docker Compose** — A single `docker compose up` to spin up all services (FastAPI, Next.js, PostgreSQL, ChromaDB) for seamless local development and production deployment.
- **Jira & Notion Connector** — Allow employees to query their project management data. *"How many tickets were opened related to payment errors last sprint?"* — all from the same Scout chat interface.
- **Microsoft Teams / Slack Bot** — Deploy Scout as a conversational bot inside existing communication tools so employees can query data without leaving the tools they already use.
- **Column-Level Access Control** — Extend the governance model to restrict access at the column level, enabling fine-grained PII protection.
- **Semantic Query Caching** — Cache frequent query results to reduce LLM calls and latency.
- **Audit Dashboard** — A dedicated view for Platform Admins showing all AI query logs, generated SQL, data sources accessed, and user activity — full regulatory auditability in a UI.

---

## Project Structure

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
│   ├── HLSD.png                  # High Level System Design diagram
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

## Security & Compliance Posture

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

## Running Tests

```bash
# From src/backend (with venv active):
pytest tests/ -v
```

Tests cover:
- **Agent Tests** — orchestrator agent intent classification, SQL generation correctness, relevancy filtering, and execution agent read-only enforcement
- **API Tests** — endpoint validation for authentication, chatroom CRUD, admin governance operations, scheduled query management, alert retrieval, and dashboard card listing

---

## API Reference

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
| `GET` | `/health/llm` | LLM key pool status |

---

## License

This project is licensed under the Apache License 2.0.
See the LICENSE file for details.

---

<div align="center">

*Scout — Because your data deserves to be heard.*

</div>
