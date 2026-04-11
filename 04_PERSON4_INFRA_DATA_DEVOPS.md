# PERSON 4 — INFRA, DATA & DEVOPS ENGINEER
## Read 00_MASTER_SHARED_CONTEXT.md first. Everything in that document applies to you.

---

## YOUR ROLE

You are the silent unlocker. Every other team member depends on things you do in the first 6 hours. You set up the database, run migrations, generate 1 million rows of mock data, seed ChromaDB, deploy both services, write the README, and ensure compliance. You never write agent logic, never write FastAPI routes, never write React components. You build the stage everyone else performs on.

---

## YOUR FILES — COMPLETE LIST

```
backend/mock_data/generate_transactions.py
backend/mock_data/generate_customers.py
backend/mock_data/generate_system_logs.py
backend/mock_data/generate_products_finance.py
backend/mock_data/generate_geography.py
backend/mock_data/seed_alerts.py
backend/mock_data/seed_master_config.py
backend/vectorstore/ingest.py
frontend/app/(portal)/onboarding/page.tsx    ← you build this page (Person 3 builds the component)
frontend/app/(portal)/alerts/page.tsx        ← you build this page
README.md
LICENSE
.gitignore
render.yaml (or railway.json)
```

---

## HOUR-BY-HOUR PLAN

### Hour 0–2 (with team)
1. Create GitHub repository (private). Name: `banquoite`
2. Agree on single commit email. All team members configure: `git config user.email "team@banquoite.dev"`
3. Create Neon.tech account. Create database named `banquoite_prod`.
4. Copy `DATABASE_URL` from Neon dashboard. Share with team.
5. Create Groq account at console.groq.com. Generate API key. Share securely (not in chat).
6. Create Vercel account. Connect GitHub repo.
7. Create Render.com or Railway.app account.
8. Wait for Person 2 to run Alembic migration. Verify all 11 core tables appear in Neon dashboard.

### Hour 2–8 (data generation — this is your most important block)
Run all 5 generation scripts. Each script creates tables AND inserts data using COPY for speed.
Run `seed_alerts.py` and `seed_master_config.py` at the end.
Target: 1,000,000 rows total across 40 tables.

### Hour 8–10 (ChromaDB ingestion)
Run `ingest.py` to embed customer reviews into ChromaDB.
Commit the `chroma_data/` folder if using Render (ephemeral filesystem).

### Hour 10–14 (deployment)
Deploy backend to Render/Railway. Configure all environment variables.
Deploy frontend to Vercel. Configure `NEXT_PUBLIC_API_URL`.
Confirm both health checks pass.

### Hour 14–24 (monitoring)
Watch backend logs. Fix any startup failures.
Confirm Person 2's routes return 200s.
Confirm Person 3's frontend loads on Vercel URL.

### Hour 24–32 (build your pages)
Build `app/(portal)/onboarding/page.tsx` (uses `OnboardingFlow` component from Person 3).
Build `app/(portal)/alerts/page.tsx` (uses `AlertCenter` component from Person 3).

### Hour 32–44 (compliance + README)
Write `README.md` (full spec below).
Add `LICENSE` file (Apache 2.0 text below).
Write `.gitignore`.
Run compliance audit.
DCO commit audit.

---

## DATA GENERATION — DETAILED SPECS

**CRITICAL RULE FOR ALL SCRIPTS:**
- Use `psycopg2` with `COPY FROM` (StringIO buffer) — NOT row-by-row INSERT.
- Row-by-row insert for 1M rows takes 2–3 hours. COPY takes 5–10 minutes.
- Each script creates its tables if they don't exist, then inserts data.
- Use `faker.Faker()` for realistic data.
- Use `random.seed(42)` at top of each script for reproducibility.

---

### Script 1: `generate_transactions.py`

**Target: ~500,000 rows across 12 tables**

**Primary table `mock_transactions` schema (250,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_transactions (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'GBP',
  status VARCHAR(20) NOT NULL,     -- 'SUCCESS' or 'FAILED'
  region VARCHAR(20) NOT NULL,     -- 'NORTH', 'SOUTH', 'EAST', 'WEST', 'LONDON'
  merchant_category VARCHAR(50),
  created_at TIMESTAMP NOT NULL,
  payment_method VARCHAR(20),      -- 'CARD', 'BANK_TRANSFER', 'DIRECT_DEBIT'
  error_code VARCHAR(50)           -- NULL for SUCCESS, code for FAILED
);
```

**Generation rules for mock_transactions:**
- 85% SUCCESS, 15% FAILED (overall)
- Create a "spike" period: 2 days ago, failure rate jumps to 35% between 14:00–16:00
- Regions: NORTH 25%, SOUTH 20%, EAST 20%, WEST 15%, LONDON 20%
- Amounts: normal distribution centered on £150, range £1–£50,000
- Dates: last 90 days, weighted toward recent dates
- error_code values: 'INSUFFICIENT_FUNDS', 'CARD_DECLINED', 'TIMEOUT', 'FRAUD_SUSPECTED', 'SYSTEM_ERROR'

**Other transaction tables (build with Faker, 10,000–50,000 rows each):**
- `mock_failed_transactions` — subset of failed transactions with additional failure_reason TEXT
- `mock_payment_events` — event log: payment lifecycle states (INITIATED → PROCESSING → COMPLETED/FAILED)
- `mock_refunds` — columns: transaction_id, refund_amount, reason, status, created_at
- `mock_chargebacks` — columns: transaction_id, chargeback_amount, dispute_reason, outcome, created_at
- `mock_transaction_fees` — columns: transaction_id, fee_amount, fee_type, waived
- `mock_fx_conversions` — columns: from_currency, to_currency, amount, converted_amount, rate, created_at
- `mock_batch_payments` — columns: batch_id, total_amount, transaction_count, status, scheduled_at, executed_at
- `mock_recurring_payments` — columns: customer_id, amount, frequency, next_run_at, status
- `mock_payment_methods` — columns: customer_id, method_type, last_four, is_default, created_at
- `mock_merchant_categories` — columns: category_code, category_name, avg_transaction_value, transaction_count
- `mock_transaction_limits` — columns: customer_id, daily_limit, monthly_limit, current_daily_used, current_monthly_used

---

### Script 2: `generate_customers.py`

**Target: ~150,000 rows across 8 tables**

**Primary table `mock_customers` schema (50,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_customers (
  id UUID PRIMARY KEY,
  full_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  region VARCHAR(20),
  customer_segment VARCHAR(20),    -- 'PREMIUM', 'STANDARD', 'BASIC'
  created_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);
```

**Other customer tables:**
- `mock_customer_accounts` — columns: customer_id, account_number, account_type (CURRENT/SAVINGS), balance, opened_at
- `mock_customer_segments` — columns: segment_name, avg_balance, avg_transactions_per_month, churn_rate
- `mock_kyc_records` — columns: customer_id, kyc_status (VERIFIED/PENDING/FAILED), verified_at, document_type
- `mock_customer_complaints` — columns: customer_id, complaint_text TEXT, category, status, created_at
- `mock_customer_support_tickets` — columns: customer_id, issue_description TEXT, priority, resolved_at, agent_id
- `mock_customer_churn_events` — columns: customer_id, churn_date, reason, predicted_at, model_confidence
- `mock_customer_onboarding` — columns: customer_id, step_name, completed_at, time_taken_seconds

---

### Script 3: `generate_system_logs.py`

**Target: ~300,000 rows across 10 tables**

**Primary table `mock_api_gateway_logs` schema (100,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_api_gateway_logs (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  endpoint VARCHAR(255) NOT NULL,
  method VARCHAR(10) NOT NULL,
  status_code INTEGER NOT NULL,
  response_time_ms INTEGER NOT NULL,
  error_message TEXT,
  region VARCHAR(20),
  service_name VARCHAR(50),
  request_id VARCHAR(100)
);
```

**Generation rules for mock_api_gateway_logs:**
- Endpoints: '/payments/process', '/accounts/balance', '/auth/login', '/transfers/initiate', '/cards/validate'
- Service names: 'payment-service', 'account-service', 'auth-service', 'notification-service'
- 95% status 200, 3% status 500, 1% status 429, 1% status 503
- Create a latency spike: same 2-day-ago period as transactions, P95 latency 2000ms+
- Normal response times: 50–300ms (normal distribution)

**Tyk gateway event table `mock_tyk_gateway_events` (50,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_tyk_gateway_events (
  id UUID PRIMARY KEY,
  event_type VARCHAR(50),          -- 'REQUEST', 'RESPONSE', 'ERROR', 'RATE_LIMIT'
  api_id VARCHAR(100),
  api_name VARCHAR(100),
  org_id VARCHAR(100),
  timestamp TIMESTAMP,
  latency_ms INTEGER,
  error_code VARCHAR(50)
);
```

**Other log tables (10,000–30,000 rows each):**
- `mock_login_events` — columns: user_id, timestamp, ip_address, success, failure_reason, device_type
- `mock_system_health_metrics` — columns: service_name, timestamp, cpu_usage_pct, memory_usage_pct, disk_usage_pct
- `mock_service_latency_logs` — columns: service_name, timestamp, p50_ms, p95_ms, p99_ms, request_count
- `mock_error_logs` — columns: service_name, timestamp, error_level, message TEXT, stack_trace TEXT
- `mock_deployment_events` — columns: service_name, version, deployed_at, deployed_by, status, rollback_at
- `mock_audit_trail` — columns: user_id, action, resource_type, resource_id, timestamp, ip_address
- `mock_session_events` — columns: session_id, user_id, event_type, timestamp, duration_seconds
- `mock_notification_delivery_logs` — columns: notification_id, channel, recipient, status, delivered_at, error_message

---

### Script 4: `generate_products_finance.py`

**Target: ~30,000 rows across 6 tables (smaller tables)**

- `mock_products` — columns: id, name, category, monthly_fee, interest_rate, min_balance, is_active (500 rows)
- `mock_loan_applications` — columns: customer_id, amount, purpose, status, applied_at, decision_at, rate (20,000 rows)
- `mock_credit_scores` — columns: customer_id, score, score_date, rating (EXCELLENT/GOOD/FAIR/POOR) (50,000 rows)
- `mock_investment_portfolios` — columns: customer_id, portfolio_value, asset_class, return_pct, updated_at (5,000 rows)
- `mock_insurance_policies` — columns: customer_id, policy_type, premium, coverage_amount, start_date, status (8,000 rows)
- `mock_savings_goals` — columns: customer_id, goal_name, target_amount, current_amount, deadline, status (10,000 rows)

---

### Script 5: `generate_geography.py`

**Target: ~5,000 rows across 4 tables (reference/lookup tables)**

- `mock_regions` — columns: id, region_name, region_code, population, gdp_billion, num_branches (5 rows: NORTH/SOUTH/EAST/WEST/LONDON)
- `mock_branches` — columns: id, branch_name, region, address, opened_at, is_active, num_staff (200 rows)
- `mock_atm_locations` — columns: id, branch_id, location_name, region, is_operational, last_maintenance (1,000 rows)
- `mock_branch_performance` — columns: branch_id, month, transaction_count, total_amount, customer_count, satisfaction_score (2,400 rows = 200 branches × 12 months)

---

### Script 6: `seed_alerts.py`

Seeds 2 `ALERT_CONFIGURATIONS` and 3 `ALERTS` directly for demo reliability.
The team UUID must match a seeded team. Create a demo team first.

```python
"""
This script seeds:
1. A demo team: "NatWest Operations"
2. Two alert configurations:
   - failed_transaction_rate > 0.15 (15%) → HIGH severity
   - api_p95_latency > 2000ms → MEDIUM severity
3. Three pre-triggered alerts (is_read=False) showing the system caught real problems
"""

DEMO_TEAM_ID = "11111111-1111-1111-1111-111111111111"  # Fixed UUID for demo
DEMO_TEAM_NAME = "NatWest Operations"

alert_1 = {
    "title": "Transaction Failure Rate Spike Detected",
    "description": "Failed transaction rate reached 23.4% in the past hour, significantly above the 15% threshold. The spike originated in the SOUTH region, affecting the /payments/process endpoint. Recommend immediate investigation.",
    "severity": "HIGH",
    "data_snapshot": {
        "current_rate": 0.234,
        "threshold": 0.15,
        "affected_region": "SOUTH",
        "affected_endpoint": "/payments/process",
        "time_window": "last 1 hour",
        "failed_count": 2847,
        "total_count": 12168
    }
}

alert_2 = {
    "title": "API Gateway Latency Elevated",
    "description": "P95 response time on payment-service has exceeded 2000ms threshold. Current P95: 2847ms. This may indicate downstream database contention or increased load.",
    "severity": "MEDIUM",
    "data_snapshot": {
        "service": "payment-service",
        "p95_ms": 2847,
        "threshold_ms": 2000,
        "p50_ms": 180,
        "measurement_window": "last 15 minutes"
    }
}

alert_3 = {
    "title": "Unusual Login Pattern Detected",
    "description": "138 failed login attempts from 12 distinct IP addresses in the EAST region over the past 30 minutes. This pattern is consistent with a credential stuffing attack.",
    "severity": "HIGH",
    "data_snapshot": {
        "failed_attempts": 138,
        "distinct_ips": 12,
        "region": "EAST",
        "window_minutes": 30,
        "most_targeted_accounts": 8
    }
}
```

---

### Script 7: `seed_master_config.py`

Seeds 8 entries in `master_config` table for the demo team. This is critical — without these entries, the Relevancy Agent cannot find any tables and every query returns empty.

```python
"""
Seeds master_config with 8 commonly-queried mock tables for the demo team.
Each entry has a semantic_definition and columns_metadata JSON.
"""

CONFIGS = [
    {
        "table_name": "mock_transactions",
        "semantic_definition": "All payment transactions processed by NatWest. Includes successful and failed payments with amounts, regions, merchant categories, and timestamps. Use this table to analyze transaction volumes, failure rates, revenue, and regional performance.",
        "columns_metadata": [
            {"name": "id", "type": "UUID", "description": "Unique transaction identifier"},
            {"name": "customer_id", "type": "UUID", "description": "Customer who made the payment"},
            {"name": "amount", "type": "DECIMAL", "description": "Transaction amount in GBP"},
            {"name": "currency", "type": "VARCHAR", "description": "Currency code, default GBP"},
            {"name": "status", "type": "VARCHAR", "description": "SUCCESS or FAILED"},
            {"name": "region", "type": "VARCHAR", "description": "Geographic region: NORTH, SOUTH, EAST, WEST, LONDON"},
            {"name": "merchant_category", "type": "VARCHAR", "description": "Category of merchant"},
            {"name": "created_at", "type": "TIMESTAMP", "description": "When the transaction occurred"},
            {"name": "payment_method", "type": "VARCHAR", "description": "CARD, BANK_TRANSFER, or DIRECT_DEBIT"},
            {"name": "error_code", "type": "VARCHAR", "description": "Error code for failed transactions, NULL for success"}
        ]
    },
    {
        "table_name": "mock_api_gateway_logs",
        "semantic_definition": "API gateway request and response logs from all banking services. Use this to analyze API performance, error rates, latency patterns, and service health. Includes Tyk gateway events.",
        "columns_metadata": [
            {"name": "id", "type": "UUID", "description": "Log entry identifier"},
            {"name": "timestamp", "type": "TIMESTAMP", "description": "When the request was processed"},
            {"name": "endpoint", "type": "VARCHAR", "description": "API endpoint path e.g. /payments/process"},
            {"name": "method", "type": "VARCHAR", "description": "HTTP method: GET, POST, etc."},
            {"name": "status_code", "type": "INTEGER", "description": "HTTP response status code"},
            {"name": "response_time_ms", "type": "INTEGER", "description": "Response time in milliseconds"},
            {"name": "error_message", "type": "TEXT", "description": "Error message if status >= 400"},
            {"name": "region", "type": "VARCHAR", "description": "Geographic region of the request"},
            {"name": "service_name", "type": "VARCHAR", "description": "Backend service that handled the request"}
        ]
    },
    {
        "table_name": "mock_customers",
        "semantic_definition": "Customer master data including demographics, segments, and regional information. Use to analyze customer distribution, segmentation, and regional breakdown.",
        "columns_metadata": [
            {"name": "id", "type": "UUID", "description": "Customer identifier"},
            {"name": "full_name", "type": "VARCHAR", "description": "Customer full name"},
            {"name": "region", "type": "VARCHAR", "description": "Customer home region"},
            {"name": "customer_segment", "type": "VARCHAR", "description": "PREMIUM, STANDARD, or BASIC"},
            {"name": "created_at", "type": "TIMESTAMP", "description": "Account creation date"},
            {"name": "is_active", "type": "BOOLEAN", "description": "Whether account is currently active"}
        ]
    },
    {
        "table_name": "mock_failed_transactions",
        "semantic_definition": "Detailed records of failed payment transactions with extended failure analysis. Subset of mock_transactions with additional failure_reason text. Use for failure analysis and root cause investigation.",
        "columns_metadata": [
            {"name": "id", "type": "UUID", "description": "Transaction identifier"},
            {"name": "amount", "type": "DECIMAL", "description": "Failed transaction amount in GBP"},
            {"name": "region", "type": "VARCHAR", "description": "Region where failure occurred"},
            {"name": "error_code", "type": "VARCHAR", "description": "Machine-readable error code"},
            {"name": "failure_reason", "type": "TEXT", "description": "Human-readable explanation of the failure"},
            {"name": "created_at", "type": "TIMESTAMP", "description": "When the failure occurred"}
        ]
    },
    {
        "table_name": "mock_system_health_metrics",
        "semantic_definition": "System resource utilization metrics collected every 5 minutes from all banking services. Use to identify resource bottlenecks, correlate outages with resource exhaustion, and analyze service health trends.",
        "columns_metadata": [
            {"name": "service_name", "type": "VARCHAR", "description": "Name of the service being monitored"},
            {"name": "timestamp", "type": "TIMESTAMP", "description": "When metrics were collected"},
            {"name": "cpu_usage_pct", "type": "FLOAT", "description": "CPU usage percentage 0-100"},
            {"name": "memory_usage_pct", "type": "FLOAT", "description": "Memory usage percentage 0-100"},
            {"name": "disk_usage_pct", "type": "FLOAT", "description": "Disk usage percentage 0-100"}
        ]
    },
    {
        "table_name": "mock_loan_applications",
        "semantic_definition": "Loan application records including amounts, purposes, decisions, and interest rates. Use to analyze lending patterns, approval rates, and portfolio composition.",
        "columns_metadata": [
            {"name": "customer_id", "type": "UUID", "description": "Applicant customer"},
            {"name": "amount", "type": "DECIMAL", "description": "Requested loan amount in GBP"},
            {"name": "purpose", "type": "VARCHAR", "description": "Loan purpose: MORTGAGE, PERSONAL, BUSINESS, AUTO"},
            {"name": "status", "type": "VARCHAR", "description": "APPROVED, REJECTED, PENDING"},
            {"name": "applied_at", "type": "TIMESTAMP", "description": "Application submission date"},
            {"name": "decision_at", "type": "TIMESTAMP", "description": "Decision date, NULL if pending"},
            {"name": "rate", "type": "FLOAT", "description": "Approved interest rate percentage"}
        ]
    },
    {
        "table_name": "mock_branch_performance",
        "semantic_definition": "Monthly performance metrics for each NatWest branch. Use to compare branch performance, identify top and bottom performers, and analyze regional trends.",
        "columns_metadata": [
            {"name": "branch_id", "type": "UUID", "description": "Branch identifier"},
            {"name": "month", "type": "DATE", "description": "First day of the reporting month"},
            {"name": "transaction_count", "type": "INTEGER", "description": "Total transactions processed"},
            {"name": "total_amount", "type": "DECIMAL", "description": "Total transaction value in GBP"},
            {"name": "customer_count", "type": "INTEGER", "description": "Unique customers served"},
            {"name": "satisfaction_score", "type": "FLOAT", "description": "Customer satisfaction score 0-10"}
        ]
    },
    {
        "table_name": "mock_credit_scores",
        "semantic_definition": "Customer credit scores and ratings. Use to analyze credit risk distribution, segment customers by creditworthiness, and understand portfolio risk.",
        "columns_metadata": [
            {"name": "customer_id", "type": "UUID", "description": "Customer identifier"},
            {"name": "score", "type": "INTEGER", "description": "Numeric credit score 300-850"},
            {"name": "score_date", "type": "DATE", "description": "Date score was calculated"},
            {"name": "rating", "type": "VARCHAR", "description": "EXCELLENT (750+), GOOD (670-749), FAIR (580-669), POOR (<580)"}
        ]
    }
]
```

---

## ChromaDB INGESTION: `vectorstore/ingest.py`

This script runs once. It loads customer review text from `mock_customer_complaints` and `mock_customer_support_tickets`, splits it into chunks, embeds it, and stores in ChromaDB.

```python
"""
Ingests unstructured text data into ChromaDB for RAG retrieval.
Run this script AFTER mock_data generation scripts have populated the DB.
Run: python -m backend.vectorstore.ingest
"""

import os
import psycopg2
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
CHROMA_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")

def ingest():
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Load complaint texts
    cur.execute("SELECT id::text, complaint_text, category, created_at::text FROM mock_customer_complaints LIMIT 50000")
    complaints = cur.fetchall()

    # Load support ticket texts  
    cur.execute("SELECT id::text, issue_description, priority, created_at::text FROM mock_customer_support_tickets LIMIT 50000")
    tickets = cur.fetchall()

    conn.close()

    documents = []
    for row in complaints:
        if row[1]:  # complaint_text not null
            documents.append(Document(
                page_content=row[1],
                metadata={"source": "customer_complaint", "id": row[0], "category": row[2], "date": row[3]}
            ))

    for row in tickets:
        if row[1]:  # issue_description not null
            documents.append(Document(
                page_content=row[1],
                metadata={"source": "support_ticket", "id": row[0], "priority": row[2], "date": row[3]}
            ))

    print(f"Loaded {len(documents)} documents. Splitting...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks. Embedding... (this takes 5-10 minutes)")

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name="customer_reviews",
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    # Batch ingest to avoid memory issues
    batch_size = 1000
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        vectorstore.add_documents(batch)
        print(f"Ingested {min(i+batch_size, len(chunks))}/{len(chunks)} chunks...")

    print(f"Done. ChromaDB populated at {CHROMA_PATH}")

if __name__ == "__main__":
    ingest()
```

---

## DEPLOYMENT STEPS

### Backend (Render.com)

1. Go to render.com → New Web Service → Connect GitHub repo
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt && alembic upgrade head`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env.example` with real values
6. **Critical:** Before deploying, run `ingest.py` locally, commit the `chroma_data/` folder so it deploys with the service.

### Frontend (Vercel)

1. Go to vercel.com → New Project → Import GitHub repo
2. Root directory: `frontend`
3. Framework: Next.js (auto-detected)
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://banquoite-api.onrender.com`)
5. Deploy.

### Verify deployment

```bash
# Backend health check
curl https://banquoite-api.onrender.com/health
# Expected: {"status": "ok"}

# Frontend
# Open https://your-project.vercel.app
# Should show login page
```

---

## README.md — REQUIRED CONTENT

```markdown
# Banquoite — Talk to Data

## Overview
Banquoite is an AI-powered enterprise intelligence portal built for the NatWest "Talk to Data" hackathon. It allows banking teams to ask natural language questions about segregated enterprise data and receive instant, trustworthy answers. Non-technical managers receive simplified explanations with charts. Developers receive technical detail with SQL, table references, and logs. Every answer includes a Chain of Thought transparency layer showing exactly which data sources were used.

## Live Demo
- Frontend: [your-vercel-url.vercel.app]
- Backend API: [your-render-url.onrender.com]

## Features (Implemented)
- Multi-agent AI pipeline (Orchestrator → Relevancy → SQL Generation → RAG → Execution → Synthesis → Persona)
- Persona-based output: Manager (simplified, charts) and Developer (SQL, technical detail)
- Chain of Thought transparency on every answer
- Self-service onboarding: Data Owners register databases and configure table access
- Data segregation: AI only accesses tables explicitly approved per team
- Personalized chatrooms with persistent history
- Alert Center with pre-detected anomalies
- Scheduled query interface (UI complete; backend cron operational)
- Proactive anomaly detection (APScheduler monitoring key metrics)
- Hybrid SQL + RAG: structured transaction data + unstructured customer reviews
- Mock enterprise dataset: ~1M rows across 40 tables

## Features (Partial — Planned for Production)
- Alert configuration UI (currently seeded via script; configuration screen planned)
- Semantic caching (planned; in-memory only for hackathon)
- Multi-database encryption (connection strings stored; encryption layer planned)
- Email delivery (Resend integrated; triggered by scheduler)

## Tech Stack
- Frontend: Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- Backend: Python 3.11, FastAPI, SQLAlchemy 2.0
- Agent Framework: LangGraph + LangChain
- LLM: Groq API (llama-3.1-70b-versatile)
- Vector Store: ChromaDB + sentence-transformers
- Database: PostgreSQL on Neon.tech
- Deployment: Vercel + Render.com

## Architecture
[Describe the 7-agent pipeline, LangGraph graph, Master Config Table security model]

## Installation

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env values
alembic upgrade head
python -m backend.mock_data.generate_transactions
python -m backend.mock_data.generate_customers
python -m backend.mock_data.generate_system_logs
python -m backend.mock_data.generate_products_finance
python -m backend.mock_data.generate_geography
python -m backend.mock_data.seed_alerts
python -m backend.mock_data.seed_master_config
python -m backend.vectorstore.ingest
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL
npm run dev
```

## Usage Examples

**Ask a business question (Manager persona):**
> "Why did revenue drop last month?"

**Ask a technical question (Developer persona):**
> "Show me API gateway error rates by service for the past 7 days"

**Scheduled report:**
> Set up: "Send me a daily transaction summary every morning at 9am"

## Team
[Team member names]

## License
Apache 2.0 — see LICENSE file
```

---

## LICENSE FILE

Create a file named `LICENSE` in the root directory with the full Apache 2.0 license text. Get it from: https://www.apache.org/licenses/LICENSE-2.0.txt

---

## .gitignore

```
# Python
__pycache__/
*.py[cod]
venv/
.env
*.egg-info/

# Node
node_modules/
.next/
.env.local

# Data — commit chroma_data ONLY if needed for deployment
# chroma_data/   ← remove this line if you need to commit it for Render

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## COMPLIANCE AUDIT SCRIPT

Run this at hour 44 before code freeze:

```bash
# 1. Check for hardcoded secrets
echo "=== Checking for secrets ==="
grep -r "gsk_" . --include="*.py" --include="*.ts" --include="*.tsx" | grep -v ".env"
grep -r "re_" . --include="*.py" --include="*.ts" --include="*.tsx" | grep -v ".env"

# 2. Check all commits are signed
echo "=== Checking DCO sign-off ==="
git log --format="%H %s" | head -20

# 3. Verify .env.example has no real values
echo "=== Checking .env.example ==="
grep -v "^#" backend/.env.example | grep -v "^$"

# 4. Confirm requirements.txt is up to date
echo "=== Backend dependencies ==="
pip freeze > /tmp/actual.txt
diff requirements.txt /tmp/actual.txt

# 5. Confirm package.json is up to date
echo "=== Frontend dependencies ==="
cd frontend && npm list --depth=0
```
