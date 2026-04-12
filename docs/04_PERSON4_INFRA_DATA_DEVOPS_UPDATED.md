# PERSON 4 — INFRA, DATA & DEVOPS ENGINEER
## Read 00_MASTER_SHARED_CONTEXT_FINAL.md first. Everything in that document applies to you.
## This file supersedes any earlier version of 04_PERSON4. If anything conflicts, THIS FILE WINS.

---

## YOUR ROLE

You are the silent unlocker. Every other team member depends on things you do in the first 6 hours. You set up the database, run migrations, generate approximately 1 million rows of mock data across 40 tables (covering 5 teams), seed ChromaDB, seed the governance demo users, deploy both services, write the README, and ensure compliance. You never write agent logic, never write FastAPI routes, never write React components. You build the stage everyone else performs on.

---

## YOUR FILES — COMPLETE LIST

```
backend/mock_data/generate_transactions.py        ← Team A (Payments) — 12 tables, ~500,000 rows
backend/mock_data/generate_customers.py           ← Team D (Customer) + Team C (Risk) — 12 tables, ~150,000 rows
backend/mock_data/generate_system_logs.py         ← Team B (Operations) — 10 tables, ~300,000 rows
backend/mock_data/generate_products_finance.py    ← Team E (Finance) — 6 tables, ~30,000 rows
backend/mock_data/generate_geography.py           ← Shared reference tables — 4 tables, ~5,000 rows
backend/mock_data/seed_alerts.py                  ← Seeds alert_configurations + alerts for demo
backend/mock_data/seed_master_config.py           ← UPDATED: seeds 5 teams + assigns tables per team
backend/mock_data/seed_governance.py              ← NEW: seeds PLATFORM_ADMIN + ENTERPRISE_ANALYST demo users
backend/vectorstore/ingest.py                     ← ChromaDB ingestion from mock text data

frontend/app/(portal)/onboarding/page.tsx         ← You build this page (uses OnboardingFlow component)
frontend/app/(portal)/alerts/page.tsx             ← You build this page (uses AlertCenter component)
frontend/app/(portal)/admin/page.tsx              ← NEW: You build this page (uses AdminGovernancePanel component)

README.md
LICENSE
.gitignore
render.yaml  (or railway.json)
```

---

## HOUR-BY-HOUR PLAN

### Hour 0–2 (with team — do not split until complete)
1. Create GitHub repository (private). Name: `banquoite`
2. Agree on single commit email. All team members run:
   ```bash
   git config user.email "team@banquoite.dev"
   git config user.name "Banquoite Team"
   ```
3. Create Neon.tech account. Create a database named `banquoite_prod`. Copy the `DATABASE_URL` connection string and share with the team securely (not in a public chat).
4. Create Groq account at console.groq.com. Generate API key (`gsk_...`). Share with team securely.
5. Create Resend account at resend.com. Generate API key (`re_...`). Share with team securely.
6. Create Vercel account. Connect the GitHub repository.
7. Create Render.com account. Connect the GitHub repository.
8. Wait for **Person 2** to push `models.py` and run `alembic upgrade head`. After that, verify in the Neon dashboard that these 12 core tables exist:
   - `teams`, `users`, `user_team_access`, `database_connections`, `master_config`
   - `chatrooms`, `messages`, `scheduled_queries`, `scheduled_reports`
   - `alert_configurations`, `alerts`, `dashboard_cards`
   If any are missing, flag to Person 2 immediately.

### Hour 2–8 (data generation — your most critical block)
Run scripts in this exact order. Each creates tables if missing, then bulk-inserts data.

```bash
# In the backend directory, with .env loaded:
python -m backend.mock_data.generate_transactions
python -m backend.mock_data.generate_customers
python -m backend.mock_data.generate_system_logs
python -m backend.mock_data.generate_products_finance
python -m backend.mock_data.generate_geography
python -m backend.mock_data.seed_alerts
python -m backend.mock_data.seed_master_config
python -m backend.mock_data.seed_governance
```

After all scripts complete, verify in the Neon dashboard:
- 40 `mock_*` tables exist.
- `mock_transactions` has ~250,000 rows.
- `mock_api_gateway_logs` has ~100,000 rows.
- `teams` table has exactly 5 rows (A–E).
- `users` table has 5 demo user rows (admin, enterprise, analyst.a, analyst.b, owner.a).
- `user_team_access` has 3 rows (enterprise analyst gets Team A + Team B; analyst.a gets Team A; analyst.b gets Team B).
- `master_config` has 40 rows (all mock tables assigned to their teams).

### Hour 8–10 (ChromaDB ingestion)
Run the ingestion script after mock data is generated. This embeds text from `mock_customer_complaints` and `mock_customer_support_tickets` into ChromaDB for RAG retrieval.

```bash
python -m backend.vectorstore.ingest
```

After completion, the `chroma_data/` folder will be created in the project root. Commit this folder now because Render.com has an ephemeral filesystem:

```bash
git add chroma_data/
git commit -s -m "chore: add ChromaDB vector store for RAG"
```

### Hour 10–14 (deployment)
**Backend on Render.com:**
1. Go to render.com → New Web Service → Connect GitHub repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt && alembic upgrade head`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env.example` with real values.
6. Deploy and wait for green health check at `/health`.

**Frontend on Vercel:**
1. Go to vercel.com → New Project → Import GitHub repo.
2. Root directory: `frontend`
3. Framework: Next.js (auto-detected).
4. Set environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL.
5. Deploy.

**Verify:**
```bash
curl https://your-render-url.onrender.com/health
# Expected: {"status": "ok"}
```

### Hour 14–24 (monitoring + support)
- Watch backend logs on Render. Fix any startup or import failures.
- Confirm Person 2's routes return HTTP 200 on basic endpoints.
- Confirm Person 3's frontend loads correctly on the Vercel URL.
- If Person 1 asks for a specific table's columns or row count, query Neon and share immediately.

### Hour 24–32 (build your three pages)

**Page 1: `app/(portal)/onboarding/page.tsx`**
This page is used by DATA_OWNERs. It imports and renders the `<OnboardingFlow />` component which Person 3 is building. Your job is only the page shell:
- Check authentication via `js-cookie` (read JWT, decode role).
- If `role !== 'DATA_OWNER'`, redirect to `/chat`.
- Otherwise render `<OnboardingFlow />`.

**Page 2: `app/(portal)/alerts/page.tsx`**
This page is used by all authenticated users. It imports and renders the `<AlertCenter />` component from Person 3.
- Authenticate. If not logged in, redirect to `/login`.
- Otherwise render `<AlertCenter />`.

**Page 3 (NEW): `app/(portal)/admin/page.tsx`**
This page is used exclusively by the PLATFORM_ADMIN. This is the governance dashboard.
- Check authentication. If `role !== 'PLATFORM_ADMIN'`, redirect to `/chat` with an error toast.
- Render the `<AdminGovernancePanel />` component which Person 3 is building.
- The panel has two sections:
  - **Table Assignment** — calls `GET /admin/tables` and `GET /admin/teams`, lets admin assign tables to teams via checkboxes.
  - **Cross-Team Access** — calls `GET /admin/users`, lets admin select ENTERPRISE_ANALYST users and tick which teams they can access (calls `POST /admin/users/{user_id}/access`).

### Hour 32–44 (compliance + README)
- Write `README.md` (full spec below in this document).
- Create `LICENSE` file with Apache 2.0 text.
- Write `.gitignore`.
- Run the full compliance audit script (at the bottom of this document).
- Verify the DCO sign-off on all commits: `git log --format="%s%n%b" | grep "Signed-off-by"`.
- Rehearse the 3-beat governance demo sequence twice with the full team.

---

## DATA GENERATION — RULES THAT APPLY TO ALL SCRIPTS

```
CRITICAL PERFORMANCE RULE:
- Use psycopg2 with COPY FROM (StringIO buffer) — NOT row-by-row INSERT.
- Row-by-row INSERT for 1M rows takes 2–3 hours. COPY takes 5–10 minutes.
- Each script: CREATE TABLE IF NOT EXISTS, then COPY data in.
- Use faker.Faker(locale='en_GB') for realistic UK-style data.
- Use random.seed(42) at the top of each script for reproducibility.
- All UUIDs: use str(uuid.uuid4()).
- All scripts accept DATABASE_URL from environment (os.getenv("DATABASE_URL")).
- Strip "+asyncpg" from DATABASE_URL before passing to psycopg2:
    db_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
```

---

## Script 1: `generate_transactions.py`
### Team A — Payments domain — Target: ~500,000 rows across 12 tables

**Primary table `mock_transactions` schema (250,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_transactions (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'GBP',
  status VARCHAR(20) NOT NULL,        -- 'SUCCESS' or 'FAILED'
  region VARCHAR(20) NOT NULL,        -- 'NORTH', 'SOUTH', 'EAST', 'WEST', 'LONDON'
  merchant_category VARCHAR(50),
  created_at TIMESTAMP NOT NULL,
  payment_method VARCHAR(20),         -- 'CARD', 'BANK_TRANSFER', 'DIRECT_DEBIT'
  error_code VARCHAR(50)              -- NULL for SUCCESS, code for FAILED
);
```

**Generation rules for mock_transactions:**
- 85% SUCCESS, 15% FAILED overall.
- Create a spike period: exactly 2 days before today's date, failure rate = 35% between 14:00–16:00. This is the anomaly that Use Case 1 will detect.
- Regions: NORTH 25%, SOUTH 20%, EAST 20%, WEST 15%, LONDON 20%.
- Amounts: normal distribution centered on £150, range £1–£50,000.
- Dates: last 90 days, weighted toward recent dates.
- merchant_category values: 'RETAIL', 'FOOD_BEVERAGE', 'TRANSPORT', 'UTILITIES', 'HEALTHCARE', 'ENTERTAINMENT'
- error_code values (for FAILED only): 'INSUFFICIENT_FUNDS', 'CARD_DECLINED', 'TIMEOUT', 'FRAUD_SUSPECTED', 'SYSTEM_ERROR'

**Other transaction tables (COPY insert, rows as specified):**
- `mock_failed_transactions` (50,000 rows) — columns: id UUID, transaction_id UUID, amount DECIMAL, region VARCHAR, error_code VARCHAR, failure_reason TEXT, created_at TIMESTAMP
- `mock_payment_events` (50,000 rows) — columns: id UUID, transaction_id UUID, event_type VARCHAR (INITIATED/PROCESSING/COMPLETED/FAILED), timestamp TIMESTAMP, metadata JSONB
- `mock_refunds` (20,000 rows) — columns: id UUID, transaction_id UUID, refund_amount DECIMAL, reason VARCHAR, status VARCHAR (PENDING/APPROVED/REJECTED), created_at TIMESTAMP
- `mock_chargebacks` (10,000 rows) — columns: id UUID, transaction_id UUID, chargeback_amount DECIMAL, dispute_reason TEXT, outcome VARCHAR (WON/LOST/PENDING), created_at TIMESTAMP
- `mock_transaction_fees` (30,000 rows) — columns: id UUID, transaction_id UUID, fee_amount DECIMAL, fee_type VARCHAR, waived BOOLEAN
- `mock_fx_conversions` (15,000 rows) — columns: id UUID, from_currency VARCHAR, to_currency VARCHAR, amount DECIMAL, converted_amount DECIMAL, rate DECIMAL, created_at TIMESTAMP
- `mock_batch_payments` (5,000 rows) — columns: id UUID, batch_id VARCHAR, total_amount DECIMAL, transaction_count INTEGER, status VARCHAR, scheduled_at TIMESTAMP, executed_at TIMESTAMP
- `mock_recurring_payments` (10,000 rows) — columns: id UUID, customer_id UUID, amount DECIMAL, frequency VARCHAR (WEEKLY/MONTHLY/ANNUAL), next_run_at TIMESTAMP, status VARCHAR
- `mock_payment_methods` (30,000 rows) — columns: id UUID, customer_id UUID, method_type VARCHAR, last_four VARCHAR, is_default BOOLEAN, created_at TIMESTAMP
- `mock_merchant_categories` (100 rows) — columns: id UUID, category_code VARCHAR, category_name VARCHAR, avg_transaction_value DECIMAL, transaction_count INTEGER
- `mock_transaction_limits` (20,000 rows) — columns: id UUID, customer_id UUID, daily_limit DECIMAL, monthly_limit DECIMAL, current_daily_used DECIMAL, current_monthly_used DECIMAL

---

## Script 2: `generate_customers.py`
### Team D (Customer) + Team C (Risk) — Target: ~150,000 rows across 12 tables

**NOTE FOR SEEDING:** These tables span two team domains. `seed_master_config.py` will assign each table to its correct team (D or C). Generation can happen in one script for efficiency.

**Team D — Customer domain:**

**Primary table `mock_customers` (50,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_customers (
  id UUID PRIMARY KEY,
  full_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  region VARCHAR(20),
  customer_segment VARCHAR(20),   -- 'PREMIUM', 'STANDARD', 'BASIC'
  created_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);
```

- `mock_customer_accounts` (50,000 rows) — columns: id UUID, customer_id UUID, account_number VARCHAR, account_type VARCHAR (CURRENT/SAVINGS), balance DECIMAL, opened_at TIMESTAMP
- `mock_customer_segments` (3 rows) — columns: id UUID, segment_name VARCHAR, avg_balance DECIMAL, avg_transactions_per_month FLOAT, churn_rate FLOAT
- `mock_customer_onboarding` (30,000 rows) — columns: id UUID, customer_id UUID, step_name VARCHAR, completed_at TIMESTAMP, time_taken_seconds INTEGER
- `mock_customer_feedback` (10,000 rows) — columns: id UUID, customer_id UUID, rating INTEGER (1-5), feedback_text TEXT, category VARCHAR, created_at TIMESTAMP
- `mock_customer_lifetime_value` (20,000 rows) — columns: id UUID, customer_id UUID, ltv_amount DECIMAL, calculated_at TIMESTAMP, segment VARCHAR

**Team C — Risk domain:**

- `mock_kyc_records` (30,000 rows) — columns: id UUID, customer_id UUID, kyc_status VARCHAR (VERIFIED/PENDING/FAILED), verified_at TIMESTAMP, document_type VARCHAR
- `mock_customer_complaints` (20,000 rows) — columns: id UUID, customer_id UUID, complaint_text TEXT, category VARCHAR, status VARCHAR (OPEN/RESOLVED/ESCALATED), created_at TIMESTAMP. **Use Faker to generate realistic complaint text — this data feeds ChromaDB RAG.**
- `mock_customer_support_tickets` (20,000 rows) — columns: id UUID, customer_id UUID, issue_description TEXT, priority VARCHAR (HIGH/MEDIUM/LOW), resolved_at TIMESTAMP, agent_id UUID. **Use Faker for realistic issue descriptions — this data also feeds ChromaDB RAG.**
- `mock_customer_churn_events` (5,000 rows) — columns: id UUID, customer_id UUID, churn_date TIMESTAMP, reason VARCHAR, predicted_at TIMESTAMP, model_confidence FLOAT
- `mock_fraud_cases` (8,000 rows) — columns: id UUID, customer_id UUID, transaction_id UUID, case_type VARCHAR (CARD_FRAUD/IDENTITY_THEFT/PHISHING), status VARCHAR (OPEN/CLOSED/REFERRED), detected_at TIMESTAMP, amount_at_risk DECIMAL
- `mock_compliance_flags` (5,000 rows) — columns: id UUID, customer_id UUID, flag_type VARCHAR (AML/PEP/SANCTIONS), severity VARCHAR (HIGH/MEDIUM/LOW), flagged_at TIMESTAMP, resolved BOOLEAN

---

## Script 3: `generate_system_logs.py`
### Team B — Operations domain — Target: ~300,000 rows across 10 tables

**Primary table `mock_api_gateway_logs` (100,000 rows):**
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
- Status codes: 200 (95%), 500 (3%), 429 (1%), 503 (1%)
- Create a latency spike: same 2-days-ago window as transactions (14:00–16:00). P95 latency = 2000ms+. This is the cross-domain correlation the ENTERPRISE_ANALYST demo query relies on.
- Normal response times: 50–300ms (normal distribution, mean 120ms)

**`mock_tyk_gateway_events` (50,000 rows):**
```sql
CREATE TABLE IF NOT EXISTS mock_tyk_gateway_events (
  id UUID PRIMARY KEY,
  event_type VARCHAR(50),     -- 'REQUEST', 'RESPONSE', 'ERROR', 'RATE_LIMIT'
  api_id VARCHAR(100),
  api_name VARCHAR(100),
  org_id VARCHAR(100),
  timestamp TIMESTAMP,
  latency_ms INTEGER,
  error_code VARCHAR(50)
);
```

**Other system log tables (COPY insert, rows as specified):**
- `mock_login_events` (30,000 rows) — columns: id UUID, user_id UUID, timestamp TIMESTAMP, ip_address VARCHAR, success BOOLEAN, failure_reason VARCHAR, device_type VARCHAR
- `mock_system_health_metrics` (50,000 rows) — columns: id UUID, service_name VARCHAR, timestamp TIMESTAMP, cpu_usage_pct FLOAT, memory_usage_pct FLOAT, disk_usage_pct FLOAT
- `mock_service_latency_logs` (30,000 rows) — columns: id UUID, service_name VARCHAR, timestamp TIMESTAMP, p50_ms INTEGER, p95_ms INTEGER, p99_ms INTEGER, request_count INTEGER
- `mock_error_logs` (20,000 rows) — columns: id UUID, service_name VARCHAR, timestamp TIMESTAMP, error_level VARCHAR (INFO/WARN/ERROR/FATAL), message TEXT, stack_trace TEXT
- `mock_deployment_events` (1,000 rows) — columns: id UUID, service_name VARCHAR, version VARCHAR, deployed_at TIMESTAMP, deployed_by VARCHAR, status VARCHAR (SUCCESS/FAILED/ROLLBACK), rollback_at TIMESTAMP
- `mock_audit_trail` (30,000 rows) — columns: id UUID, user_id UUID, action VARCHAR, resource_type VARCHAR, resource_id VARCHAR, timestamp TIMESTAMP, ip_address VARCHAR
- `mock_session_events` (20,000 rows) — columns: id UUID, session_id VARCHAR, user_id UUID, event_type VARCHAR (LOGIN/LOGOUT/TIMEOUT/REFRESH), timestamp TIMESTAMP, duration_seconds INTEGER
- `mock_notification_delivery_logs` (20,000 rows) — columns: id UUID, notification_id UUID, channel VARCHAR (EMAIL/SMS/PUSH), recipient VARCHAR, status VARCHAR (DELIVERED/FAILED/BOUNCED), delivered_at TIMESTAMP, error_message TEXT

---

## Script 4: `generate_products_finance.py`
### Team E — Finance domain — Target: ~30,000 rows across 6 tables

**These are the EXACT 6 tables assigned to Team E in the master schema. Do not add others.**

- `mock_products` (500 rows) — columns: id UUID, name VARCHAR, category VARCHAR (CURRENT_ACCOUNT/SAVINGS/LOAN/MORTGAGE/CARD), monthly_fee DECIMAL, interest_rate FLOAT, min_balance DECIMAL, is_active BOOLEAN
- `mock_loan_applications` (20,000 rows) — columns: id UUID, customer_id UUID, amount DECIMAL, purpose VARCHAR (MORTGAGE/PERSONAL/BUSINESS/AUTO), status VARCHAR (APPROVED/REJECTED/PENDING), applied_at TIMESTAMP, decision_at TIMESTAMP, rate FLOAT
- `mock_revenue_monthly` (300 rows = 5 regions × 5 years × 12 months) — columns: id UUID, month DATE, region VARCHAR, revenue DECIMAL, net_profit DECIMAL, cost DECIMAL, transaction_count INTEGER
- `mock_cost_centres` (100 rows) — columns: id UUID, centre_name VARCHAR, department VARCHAR, budget DECIMAL, actual_spend DECIMAL, variance DECIMAL, period_start DATE, period_end DATE
- `mock_branch_performance` (2,400 rows = 200 branches × 12 months) — columns: id UUID, branch_id UUID, month DATE, transaction_count INTEGER, total_amount DECIMAL, customer_count INTEGER, satisfaction_score FLOAT
- `mock_regulatory_reports` (500 rows) — columns: id UUID, report_type VARCHAR (BASEL_III/IFRS9/PRA_RETURN), period_start DATE, period_end DATE, status VARCHAR (DRAFT/SUBMITTED/ACCEPTED/REJECTED), submitted_at TIMESTAMP, notes TEXT

---

## Script 5: `generate_geography.py`
### Shared reference tables — Target: ~5,000 rows across 4 tables
### These tables are NOT assigned to any team's master_config — they are shared lookup tables used in SQL JOINs.

- `mock_regions` (5 rows) — columns: id UUID, region_name VARCHAR (NORTH/SOUTH/EAST/WEST/LONDON), region_code VARCHAR, population INTEGER, gdp_billion FLOAT, num_branches INTEGER
- `mock_branches` (200 rows) — columns: id UUID, branch_name VARCHAR, region VARCHAR, address TEXT, opened_at TIMESTAMP, is_active BOOLEAN, num_staff INTEGER
- `mock_atm_locations` (1,000 rows) — columns: id UUID, branch_id UUID, location_name VARCHAR, region VARCHAR, is_operational BOOLEAN, last_maintenance TIMESTAMP
- `mock_postcode_regions` (500 rows) — columns: id UUID, postcode_prefix VARCHAR, region VARCHAR, county VARCHAR, country VARCHAR DEFAULT 'England'

---

## Script 6: `seed_alerts.py`
### Seeds alert_configurations and pre-triggered alerts for Team B (Operations)

**IMPORTANT:** This script must run AFTER `seed_master_config.py` because it references the seeded team UUIDs. Read team UUIDs from the database — do not hardcode them.

```python
"""
seed_alerts.py

Seeds:
1. 2 alert configurations for Team B (Operations)
2. 3 pre-triggered alerts (is_read=False) for the demo

Run AFTER seed_master_config.py.
"""

import os
import uuid
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")

def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Fetch Team B UUID from teams table
    cur.execute("SELECT id FROM teams WHERE name = 'Team B — Operations' LIMIT 1")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Team B not found. Run seed_master_config.py first.")
    team_b_id = str(row[0])

    # Insert alert configurations
    config_1_id = str(uuid.uuid4())
    config_2_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO alert_configurations (id, team_id, metric_name, table_name, threshold, condition, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (config_1_id, team_b_id, 'failed_transaction_rate', 'mock_transactions', 0.15, 'ABOVE', True))

    cur.execute("""
        INSERT INTO alert_configurations (id, team_id, metric_name, table_name, threshold, condition, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (config_2_id, team_b_id, 'api_p95_latency_ms', 'mock_api_gateway_logs', 2000.0, 'ABOVE', True))

    # Insert pre-triggered alerts
    alerts = [
        {
            "id": str(uuid.uuid4()),
            "team_id": team_b_id,
            "alert_config_id": config_1_id,
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
        },
        {
            "id": str(uuid.uuid4()),
            "team_id": team_b_id,
            "alert_config_id": config_2_id,
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
        },
        {
            "id": str(uuid.uuid4()),
            "team_id": team_b_id,
            "alert_config_id": None,
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
    ]

    import json
    for a in alerts:
        cur.execute("""
            INSERT INTO alerts (id, team_id, alert_config_id, title, description, severity, data_snapshot, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (a["id"], a["team_id"], a["alert_config_id"], a["title"], a["description"],
              a["severity"], json.dumps(a["data_snapshot"]), False, datetime.utcnow()))

    conn.commit()
    conn.close()
    print("seed_alerts.py complete.")

if __name__ == "__main__":
    seed()
```

---

## Script 7: `seed_master_config.py` — COMPLETE REWRITE
### Seeds 5 teams and assigns the correct mock_ tables to each team

**This is the security boundary. The AI pipeline reads ONLY rows from master_config. If a table is not here, the AI cannot use it.**

```python
"""
seed_master_config.py

Creates 5 teams and assigns all 40 mock_ tables to the correct team.
Also seeds a demo database_connection row for each team (required by master_config FK).

Teams:
  Team A — Payments    → 12 transaction tables
  Team B — Operations  → 10 system/log tables
  Team C — Risk        → 6 risk/compliance tables
  Team D — Customer    → 6 customer tables
  Team E — Finance     → 6 finance/product tables

Also creates DATA_OWNER users for each team (used for onboarding demo).
Run this AFTER Alembic migration and AFTER data generation scripts.
"""

import os
import uuid
import json
import psycopg2
from datetime import datetime
from passlib.context import CryptContext

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----- TEAM DEFINITIONS -----
TEAMS = [
    {"name": "Team A — Payments"},
    {"name": "Team B — Operations"},
    {"name": "Team C — Risk"},
    {"name": "Team D — Customer"},
    {"name": "Team E — Finance"},
]

# ----- TABLE ASSIGNMENTS PER TEAM -----
# Each entry: (table_name, semantic_definition, columns_metadata list)
TEAM_TABLE_ASSIGNMENTS = {
    "Team A — Payments": [
        ("mock_transactions",
         "All payment transactions processed by NatWest. Includes successful and failed payments with amounts, regions, merchant categories, and timestamps. Use this table to analyze transaction volumes, failure rates, revenue, and regional performance.",
         [
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
         ]),
        ("mock_failed_transactions",
         "Detailed records of failed payment transactions with extended failure analysis. Subset of mock_transactions with additional failure_reason text. Use for failure analysis and root cause investigation.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "transaction_id", "type": "UUID", "description": "Reference to mock_transactions"},
             {"name": "amount", "type": "DECIMAL", "description": "Failed transaction amount in GBP"},
             {"name": "region", "type": "VARCHAR", "description": "Region where failure occurred"},
             {"name": "error_code", "type": "VARCHAR", "description": "Machine-readable error code"},
             {"name": "failure_reason", "type": "TEXT", "description": "Human-readable explanation of the failure"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "When the failure occurred"}
         ]),
        ("mock_payment_events",
         "Event log showing the lifecycle of each payment: INITIATED → PROCESSING → COMPLETED or FAILED. Use to analyze payment pipeline performance and drop-off points.",
         [
             {"name": "id", "type": "UUID", "description": "Event identifier"},
             {"name": "transaction_id", "type": "UUID", "description": "Payment transaction reference"},
             {"name": "event_type", "type": "VARCHAR", "description": "INITIATED, PROCESSING, COMPLETED, or FAILED"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "When this event occurred"},
             {"name": "metadata", "type": "JSONB", "description": "Additional event context"}
         ]),
        ("mock_refunds",
         "Refund records linked to original transactions. Use to analyze refund rates, reasons, and approval outcomes.",
         [
             {"name": "id", "type": "UUID", "description": "Refund record identifier"},
             {"name": "transaction_id", "type": "UUID", "description": "Original transaction reference"},
             {"name": "refund_amount", "type": "DECIMAL", "description": "Refund amount in GBP"},
             {"name": "reason", "type": "VARCHAR", "description": "Reason for refund"},
             {"name": "status", "type": "VARCHAR", "description": "PENDING, APPROVED, or REJECTED"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Refund request date"}
         ]),
        ("mock_chargebacks",
         "Chargeback dispute records. Use to analyze dispute volumes, outcomes, and financial exposure.",
         [
             {"name": "id", "type": "UUID", "description": "Chargeback identifier"},
             {"name": "transaction_id", "type": "UUID", "description": "Disputed transaction reference"},
             {"name": "chargeback_amount", "type": "DECIMAL", "description": "Disputed amount in GBP"},
             {"name": "dispute_reason", "type": "TEXT", "description": "Reason provided by customer"},
             {"name": "outcome", "type": "VARCHAR", "description": "WON, LOST, or PENDING"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Date dispute was raised"}
         ]),
        ("mock_transaction_fees",
         "Fee records for each processed transaction. Use to analyze fee revenue by type and track waived fees.",
         [
             {"name": "id", "type": "UUID", "description": "Fee record identifier"},
             {"name": "transaction_id", "type": "UUID", "description": "Transaction reference"},
             {"name": "fee_amount", "type": "DECIMAL", "description": "Fee charged in GBP"},
             {"name": "fee_type", "type": "VARCHAR", "description": "Type of fee: PROCESSING, INTERNATIONAL, OVERDRAFT"},
             {"name": "waived", "type": "BOOLEAN", "description": "Whether the fee was waived"}
         ]),
        ("mock_fx_conversions",
         "Foreign exchange conversion records. Use to analyze multi-currency transaction volumes and FX rates applied.",
         [
             {"name": "id", "type": "UUID", "description": "Conversion record identifier"},
             {"name": "from_currency", "type": "VARCHAR", "description": "Source currency code"},
             {"name": "to_currency", "type": "VARCHAR", "description": "Target currency code"},
             {"name": "amount", "type": "DECIMAL", "description": "Original amount"},
             {"name": "converted_amount", "type": "DECIMAL", "description": "Amount after conversion"},
             {"name": "rate", "type": "DECIMAL", "description": "Exchange rate applied"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Conversion timestamp"}
         ]),
        ("mock_batch_payments",
         "Batch payment job records. Use to analyze bulk payment processing performance, scheduling, and failure rates.",
         [
             {"name": "id", "type": "UUID", "description": "Batch record identifier"},
             {"name": "batch_id", "type": "VARCHAR", "description": "Batch job identifier"},
             {"name": "total_amount", "type": "DECIMAL", "description": "Total value of batch in GBP"},
             {"name": "transaction_count", "type": "INTEGER", "description": "Number of transactions in batch"},
             {"name": "status", "type": "VARCHAR", "description": "PENDING, PROCESSING, COMPLETED, FAILED"},
             {"name": "scheduled_at", "type": "TIMESTAMP", "description": "When batch was scheduled"},
             {"name": "executed_at", "type": "TIMESTAMP", "description": "When batch was actually executed"}
         ]),
        ("mock_recurring_payments",
         "Recurring payment mandates. Use to analyze direct debit volumes, frequencies, and upcoming scheduled payments.",
         [
             {"name": "id", "type": "UUID", "description": "Mandate identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer who set up the mandate"},
             {"name": "amount", "type": "DECIMAL", "description": "Recurring amount in GBP"},
             {"name": "frequency", "type": "VARCHAR", "description": "WEEKLY, MONTHLY, or ANNUAL"},
             {"name": "next_run_at", "type": "TIMESTAMP", "description": "Next scheduled execution date"},
             {"name": "status", "type": "VARCHAR", "description": "ACTIVE or CANCELLED"}
         ]),
        ("mock_payment_methods",
         "Customer registered payment methods. Use to analyze payment method distribution and default method preferences.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "method_type", "type": "VARCHAR", "description": "CARD, BANK_TRANSFER, or DIRECT_DEBIT"},
             {"name": "last_four", "type": "VARCHAR", "description": "Last 4 digits of card/account"},
             {"name": "is_default", "type": "BOOLEAN", "description": "Whether this is the customer's default method"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "When method was registered"}
         ]),
        ("mock_merchant_categories",
         "Merchant category reference data. Use to join with mock_transactions to get category names and averages.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "category_code", "type": "VARCHAR", "description": "Short category code"},
             {"name": "category_name", "type": "VARCHAR", "description": "Human-readable category name"},
             {"name": "avg_transaction_value", "type": "DECIMAL", "description": "Average transaction amount for this category"},
             {"name": "transaction_count", "type": "INTEGER", "description": "Total transactions in this category"}
         ]),
        ("mock_transaction_limits",
         "Daily and monthly transaction limits per customer. Use to identify customers approaching or exceeding limits.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "daily_limit", "type": "DECIMAL", "description": "Maximum daily spend in GBP"},
             {"name": "monthly_limit", "type": "DECIMAL", "description": "Maximum monthly spend in GBP"},
             {"name": "current_daily_used", "type": "DECIMAL", "description": "Amount used today"},
             {"name": "current_monthly_used", "type": "DECIMAL", "description": "Amount used this month"}
         ]),
    ],

    "Team B — Operations": [
        ("mock_api_gateway_logs",
         "API gateway request and response logs from all banking services. Use to analyze API performance, error rates, latency patterns, and service health. Includes endpoint, status code, and response time.",
         [
             {"name": "id", "type": "UUID", "description": "Log entry identifier"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "When the request was processed"},
             {"name": "endpoint", "type": "VARCHAR", "description": "API endpoint path e.g. /payments/process"},
             {"name": "method", "type": "VARCHAR", "description": "HTTP method: GET, POST, etc."},
             {"name": "status_code", "type": "INTEGER", "description": "HTTP response status code"},
             {"name": "response_time_ms", "type": "INTEGER", "description": "Response time in milliseconds"},
             {"name": "error_message", "type": "TEXT", "description": "Error message if status >= 400"},
             {"name": "region", "type": "VARCHAR", "description": "Geographic region of the request"},
             {"name": "service_name", "type": "VARCHAR", "description": "Backend service that handled the request"}
         ]),
        ("mock_tyk_gateway_events",
         "Tyk API gateway events including rate limiting, authentication failures, and routing events. Use for detailed gateway-level analysis.",
         [
             {"name": "id", "type": "UUID", "description": "Event identifier"},
             {"name": "event_type", "type": "VARCHAR", "description": "REQUEST, RESPONSE, ERROR, or RATE_LIMIT"},
             {"name": "api_id", "type": "VARCHAR", "description": "API identifier in Tyk"},
             {"name": "api_name", "type": "VARCHAR", "description": "Human-readable API name"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "Event timestamp"},
             {"name": "latency_ms", "type": "INTEGER", "description": "Request latency in milliseconds"},
             {"name": "error_code", "type": "VARCHAR", "description": "Error code if applicable"}
         ]),
        ("mock_login_events",
         "User authentication events — successes and failures. Use to detect brute-force attacks, unusual login patterns, and regional authentication anomalies.",
         [
             {"name": "id", "type": "UUID", "description": "Event identifier"},
             {"name": "user_id", "type": "UUID", "description": "User attempting login"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "Login attempt timestamp"},
             {"name": "ip_address", "type": "VARCHAR", "description": "Source IP address"},
             {"name": "success", "type": "BOOLEAN", "description": "Whether login succeeded"},
             {"name": "failure_reason", "type": "VARCHAR", "description": "Reason for failure if not successful"},
             {"name": "device_type", "type": "VARCHAR", "description": "MOBILE, DESKTOP, or TABLET"}
         ]),
        ("mock_system_health_metrics",
         "System resource utilization metrics collected every 5 minutes from all banking services. Use to identify resource bottlenecks, correlate outages with resource exhaustion, and analyze service health trends.",
         [
             {"name": "id", "type": "UUID", "description": "Metric record identifier"},
             {"name": "service_name", "type": "VARCHAR", "description": "Name of the service being monitored"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "When metrics were collected"},
             {"name": "cpu_usage_pct", "type": "FLOAT", "description": "CPU usage percentage 0-100"},
             {"name": "memory_usage_pct", "type": "FLOAT", "description": "Memory usage percentage 0-100"},
             {"name": "disk_usage_pct", "type": "FLOAT", "description": "Disk usage percentage 0-100"}
         ]),
        ("mock_service_latency_logs",
         "P50/P95/P99 latency percentiles for each service aggregated per minute. Use to understand latency distribution and identify tail-latency problems.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "service_name", "type": "VARCHAR", "description": "Service name"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "Measurement timestamp"},
             {"name": "p50_ms", "type": "INTEGER", "description": "Median response time"},
             {"name": "p95_ms", "type": "INTEGER", "description": "95th percentile response time"},
             {"name": "p99_ms", "type": "INTEGER", "description": "99th percentile response time"},
             {"name": "request_count", "type": "INTEGER", "description": "Total requests in this window"}
         ]),
        ("mock_error_logs",
         "Application error logs from all services. Use to identify error patterns, high-frequency errors, and service degradation events.",
         [
             {"name": "id", "type": "UUID", "description": "Log identifier"},
             {"name": "service_name", "type": "VARCHAR", "description": "Service that generated the error"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "When the error occurred"},
             {"name": "error_level", "type": "VARCHAR", "description": "INFO, WARN, ERROR, or FATAL"},
             {"name": "message", "type": "TEXT", "description": "Error message text"},
             {"name": "stack_trace", "type": "TEXT", "description": "Stack trace if available"}
         ]),
        ("mock_deployment_events",
         "Service deployment history including version, status, and rollback events. Use to correlate production incidents with deployments.",
         [
             {"name": "id", "type": "UUID", "description": "Deployment identifier"},
             {"name": "service_name", "type": "VARCHAR", "description": "Service that was deployed"},
             {"name": "version", "type": "VARCHAR", "description": "Version deployed e.g. v2.3.1"},
             {"name": "deployed_at", "type": "TIMESTAMP", "description": "Deployment timestamp"},
             {"name": "deployed_by", "type": "VARCHAR", "description": "Engineer who triggered deployment"},
             {"name": "status", "type": "VARCHAR", "description": "SUCCESS, FAILED, or ROLLBACK"},
             {"name": "rollback_at", "type": "TIMESTAMP", "description": "When rollback occurred, NULL if not rolled back"}
         ]),
        ("mock_audit_trail",
         "Complete audit trail of all user actions on the platform. Use for compliance reporting, access auditing, and security investigations.",
         [
             {"name": "id", "type": "UUID", "description": "Audit record identifier"},
             {"name": "user_id", "type": "UUID", "description": "User who performed the action"},
             {"name": "action", "type": "VARCHAR", "description": "Action performed e.g. TABLE_REGISTERED, CONFIG_UPDATED"},
             {"name": "resource_type", "type": "VARCHAR", "description": "Type of resource affected"},
             {"name": "resource_id", "type": "VARCHAR", "description": "ID of the affected resource"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "When the action occurred"},
             {"name": "ip_address", "type": "VARCHAR", "description": "IP address of the user"}
         ]),
        ("mock_session_events",
         "User session lifecycle events. Use to analyze session durations, timeout rates, and concurrent user patterns.",
         [
             {"name": "id", "type": "UUID", "description": "Event identifier"},
             {"name": "session_id", "type": "VARCHAR", "description": "Session identifier"},
             {"name": "user_id", "type": "UUID", "description": "User reference"},
             {"name": "event_type", "type": "VARCHAR", "description": "LOGIN, LOGOUT, TIMEOUT, or REFRESH"},
             {"name": "timestamp", "type": "TIMESTAMP", "description": "Event timestamp"},
             {"name": "duration_seconds", "type": "INTEGER", "description": "Session duration if LOGOUT or TIMEOUT"}
         ]),
        ("mock_notification_delivery_logs",
         "Notification delivery records across all channels. Use to analyze delivery success rates by channel and identify delivery failures.",
         [
             {"name": "id", "type": "UUID", "description": "Delivery record identifier"},
             {"name": "notification_id", "type": "UUID", "description": "Notification reference"},
             {"name": "channel", "type": "VARCHAR", "description": "EMAIL, SMS, or PUSH"},
             {"name": "recipient", "type": "VARCHAR", "description": "Email address or phone number"},
             {"name": "status", "type": "VARCHAR", "description": "DELIVERED, FAILED, or BOUNCED"},
             {"name": "delivered_at", "type": "TIMESTAMP", "description": "Delivery timestamp, NULL if failed"},
             {"name": "error_message", "type": "TEXT", "description": "Error if delivery failed"}
         ]),
    ],

    "Team C — Risk": [
        ("mock_kyc_records",
         "Know Your Customer verification records. Use to analyze KYC completion rates, pending verifications, and document type distribution.",
         [
             {"name": "id", "type": "UUID", "description": "KYC record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "kyc_status", "type": "VARCHAR", "description": "VERIFIED, PENDING, or FAILED"},
             {"name": "verified_at", "type": "TIMESTAMP", "description": "Verification completion date"},
             {"name": "document_type", "type": "VARCHAR", "description": "Type of ID document used"}
         ]),
        ("mock_customer_complaints",
         "Customer complaint records with free-text descriptions and categories. Use to analyze complaint volumes, categories, resolution rates, and identify systemic issues. Also used for RAG retrieval.",
         [
             {"name": "id", "type": "UUID", "description": "Complaint identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer who complained"},
             {"name": "complaint_text", "type": "TEXT", "description": "Full complaint description in customer's own words"},
             {"name": "category", "type": "VARCHAR", "description": "Complaint category e.g. FRAUD, SERVICE, FEES"},
             {"name": "status", "type": "VARCHAR", "description": "OPEN, RESOLVED, or ESCALATED"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Date complaint was filed"}
         ]),
        ("mock_customer_support_tickets",
         "Customer support ticket records with issue descriptions and resolution status. Use to analyze support load, priority distribution, and resolution times. Also used for RAG retrieval.",
         [
             {"name": "id", "type": "UUID", "description": "Ticket identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "issue_description", "type": "TEXT", "description": "Detailed description of the support issue"},
             {"name": "priority", "type": "VARCHAR", "description": "HIGH, MEDIUM, or LOW"},
             {"name": "resolved_at", "type": "TIMESTAMP", "description": "Resolution timestamp, NULL if open"},
             {"name": "agent_id", "type": "UUID", "description": "Support agent who handled the ticket"}
         ]),
        ("mock_customer_churn_events",
         "Customer churn prediction and actual churn events. Use to analyze churn rates by segment, identify at-risk customers, and evaluate model confidence.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "churn_date", "type": "TIMESTAMP", "description": "Date customer churned"},
             {"name": "reason", "type": "VARCHAR", "description": "Reason for churn"},
             {"name": "predicted_at", "type": "TIMESTAMP", "description": "When churn was predicted by model"},
             {"name": "model_confidence", "type": "FLOAT", "description": "Model confidence score 0-1"}
         ]),
        ("mock_fraud_cases",
         "Fraud investigation cases linked to transactions. Use to analyze fraud types, detection rates, and financial exposure.",
         [
             {"name": "id", "type": "UUID", "description": "Case identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Affected customer"},
             {"name": "transaction_id", "type": "UUID", "description": "Fraudulent transaction reference"},
             {"name": "case_type", "type": "VARCHAR", "description": "CARD_FRAUD, IDENTITY_THEFT, or PHISHING"},
             {"name": "status", "type": "VARCHAR", "description": "OPEN, CLOSED, or REFERRED"},
             {"name": "detected_at", "type": "TIMESTAMP", "description": "When fraud was detected"},
             {"name": "amount_at_risk", "type": "DECIMAL", "description": "Financial exposure in GBP"}
         ]),
        ("mock_compliance_flags",
         "AML, PEP, and sanctions compliance flags for customers. Use to analyze compliance exposure, flag resolution rates, and risk distribution.",
         [
             {"name": "id", "type": "UUID", "description": "Flag identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Flagged customer"},
             {"name": "flag_type", "type": "VARCHAR", "description": "AML, PEP, or SANCTIONS"},
             {"name": "severity", "type": "VARCHAR", "description": "HIGH, MEDIUM, or LOW"},
             {"name": "flagged_at", "type": "TIMESTAMP", "description": "When flag was raised"},
             {"name": "resolved", "type": "BOOLEAN", "description": "Whether the flag has been resolved"}
         ]),
    ],

    "Team D — Customer": [
        ("mock_customers",
         "Customer master data including demographics, segments, and regional information. Use to analyze customer distribution, segmentation, and regional breakdown.",
         [
             {"name": "id", "type": "UUID", "description": "Customer identifier"},
             {"name": "full_name", "type": "VARCHAR", "description": "Customer full name"},
             {"name": "email", "type": "VARCHAR", "description": "Customer email address"},
             {"name": "phone", "type": "VARCHAR", "description": "Customer phone number"},
             {"name": "region", "type": "VARCHAR", "description": "Customer home region"},
             {"name": "customer_segment", "type": "VARCHAR", "description": "PREMIUM, STANDARD, or BASIC"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Account creation date"},
             {"name": "is_active", "type": "BOOLEAN", "description": "Whether account is currently active"}
         ]),
        ("mock_customer_accounts",
         "Bank account records per customer. Use to analyze account type distribution, balances, and account opening trends.",
         [
             {"name": "id", "type": "UUID", "description": "Account record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Account holder reference"},
             {"name": "account_number", "type": "VARCHAR", "description": "Bank account number"},
             {"name": "account_type", "type": "VARCHAR", "description": "CURRENT or SAVINGS"},
             {"name": "balance", "type": "DECIMAL", "description": "Current account balance in GBP"},
             {"name": "opened_at", "type": "TIMESTAMP", "description": "Account opening date"}
         ]),
        ("mock_customer_segments",
         "Customer segment definitions with average metrics. Use to understand segment characteristics and benchmark individual customers.",
         [
             {"name": "id", "type": "UUID", "description": "Segment identifier"},
             {"name": "segment_name", "type": "VARCHAR", "description": "Segment name: PREMIUM, STANDARD, BASIC"},
             {"name": "avg_balance", "type": "DECIMAL", "description": "Average account balance for this segment"},
             {"name": "avg_transactions_per_month", "type": "FLOAT", "description": "Average monthly transaction count"},
             {"name": "churn_rate", "type": "FLOAT", "description": "Annual churn rate for this segment"}
         ]),
        ("mock_customer_onboarding",
         "Customer onboarding step completion records. Use to analyze funnel drop-off, identify slow steps, and improve onboarding experience.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "step_name", "type": "VARCHAR", "description": "Onboarding step name e.g. EMAIL_VERIFIED, KYC_SUBMITTED"},
             {"name": "completed_at", "type": "TIMESTAMP", "description": "When step was completed"},
             {"name": "time_taken_seconds", "type": "INTEGER", "description": "Time taken to complete this step"}
         ]),
        ("mock_customer_feedback",
         "Customer satisfaction feedback scores and comments. Use to analyze NPS trends, satisfaction by region and segment.",
         [
             {"name": "id", "type": "UUID", "description": "Feedback identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer who gave feedback"},
             {"name": "rating", "type": "INTEGER", "description": "Rating score 1-5"},
             {"name": "feedback_text", "type": "TEXT", "description": "Optional written feedback"},
             {"name": "category", "type": "VARCHAR", "description": "Feedback category: APP, SERVICE, FEES, SUPPORT"},
             {"name": "created_at", "type": "TIMESTAMP", "description": "Feedback submission date"}
         ]),
        ("mock_customer_lifetime_value",
         "Calculated customer lifetime value scores. Use to segment customers by profitability and prioritize retention efforts.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Customer reference"},
             {"name": "ltv_amount", "type": "DECIMAL", "description": "Estimated lifetime value in GBP"},
             {"name": "calculated_at", "type": "TIMESTAMP", "description": "When LTV was last calculated"},
             {"name": "segment", "type": "VARCHAR", "description": "LTV segment: HIGH_VALUE, MID_VALUE, LOW_VALUE"}
         ]),
    ],

    "Team E — Finance": [
        ("mock_products",
         "Bank product catalogue including accounts, loans, mortgages, and cards. Use to analyze product mix, pricing, and feature distribution.",
         [
             {"name": "id", "type": "UUID", "description": "Product identifier"},
             {"name": "name", "type": "VARCHAR", "description": "Product name"},
             {"name": "category", "type": "VARCHAR", "description": "CURRENT_ACCOUNT, SAVINGS, LOAN, MORTGAGE, or CARD"},
             {"name": "monthly_fee", "type": "DECIMAL", "description": "Monthly fee in GBP"},
             {"name": "interest_rate", "type": "FLOAT", "description": "Annual interest rate percentage"},
             {"name": "min_balance", "type": "DECIMAL", "description": "Minimum balance required"},
             {"name": "is_active", "type": "BOOLEAN", "description": "Whether product is currently offered"}
         ]),
        ("mock_loan_applications",
         "Loan application records including amounts, purposes, decisions, and interest rates. Use to analyze lending patterns, approval rates, and portfolio composition.",
         [
             {"name": "id", "type": "UUID", "description": "Application identifier"},
             {"name": "customer_id", "type": "UUID", "description": "Applicant customer"},
             {"name": "amount", "type": "DECIMAL", "description": "Requested loan amount in GBP"},
             {"name": "purpose", "type": "VARCHAR", "description": "MORTGAGE, PERSONAL, BUSINESS, or AUTO"},
             {"name": "status", "type": "VARCHAR", "description": "APPROVED, REJECTED, or PENDING"},
             {"name": "applied_at", "type": "TIMESTAMP", "description": "Application submission date"},
             {"name": "decision_at", "type": "TIMESTAMP", "description": "Decision date, NULL if pending"},
             {"name": "rate", "type": "FLOAT", "description": "Approved interest rate percentage"}
         ]),
        ("mock_revenue_monthly",
         "Monthly revenue and cost breakdown by region. Use to analyze profitability trends, regional performance, and cost ratios.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "month", "type": "DATE", "description": "First day of the reporting month"},
             {"name": "region", "type": "VARCHAR", "description": "Region: NORTH, SOUTH, EAST, WEST, LONDON"},
             {"name": "revenue", "type": "DECIMAL", "description": "Total revenue in GBP"},
             {"name": "net_profit", "type": "DECIMAL", "description": "Net profit after costs"},
             {"name": "cost", "type": "DECIMAL", "description": "Total operating cost"},
             {"name": "transaction_count", "type": "INTEGER", "description": "Number of transactions generating this revenue"}
         ]),
        ("mock_cost_centres",
         "Internal cost centre budgets and actual spend records. Use to analyze departmental spending, budget variance, and over/underspend.",
         [
             {"name": "id", "type": "UUID", "description": "Cost centre identifier"},
             {"name": "centre_name", "type": "VARCHAR", "description": "Cost centre name"},
             {"name": "department", "type": "VARCHAR", "description": "Owning department"},
             {"name": "budget", "type": "DECIMAL", "description": "Allocated budget in GBP"},
             {"name": "actual_spend", "type": "DECIMAL", "description": "Actual spend to date"},
             {"name": "variance", "type": "DECIMAL", "description": "Budget minus actual (positive = underspend)"},
             {"name": "period_start", "type": "DATE", "description": "Budget period start"},
             {"name": "period_end", "type": "DATE", "description": "Budget period end"}
         ]),
        ("mock_branch_performance",
         "Monthly performance metrics for each NatWest branch. Use to compare branch performance, identify top and bottom performers, and analyze regional trends.",
         [
             {"name": "id", "type": "UUID", "description": "Record identifier"},
             {"name": "branch_id", "type": "UUID", "description": "Branch identifier"},
             {"name": "month", "type": "DATE", "description": "First day of the reporting month"},
             {"name": "transaction_count", "type": "INTEGER", "description": "Total transactions processed"},
             {"name": "total_amount", "type": "DECIMAL", "description": "Total transaction value in GBP"},
             {"name": "customer_count", "type": "INTEGER", "description": "Unique customers served"},
             {"name": "satisfaction_score", "type": "FLOAT", "description": "Customer satisfaction score 0-10"}
         ]),
        ("mock_regulatory_reports",
         "Regulatory report submissions including Basel III, IFRS 9, and PRA returns. Use to track submission status and compliance deadlines.",
         [
             {"name": "id", "type": "UUID", "description": "Report identifier"},
             {"name": "report_type", "type": "VARCHAR", "description": "BASEL_III, IFRS9, or PRA_RETURN"},
             {"name": "period_start", "type": "DATE", "description": "Reporting period start"},
             {"name": "period_end", "type": "DATE", "description": "Reporting period end"},
             {"name": "status", "type": "VARCHAR", "description": "DRAFT, SUBMITTED, ACCEPTED, or REJECTED"},
             {"name": "submitted_at", "type": "TIMESTAMP", "description": "Submission timestamp, NULL if not yet submitted"},
             {"name": "notes", "type": "TEXT", "description": "Notes from regulator or internal reviewer"}
         ]),
    ],
}


def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. Insert teams (use fixed UUIDs for reproducibility)
    team_ids = {}
    for team in TEAMS:
        team_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO teams (id, name, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (team_id, team["name"], datetime.utcnow()))
        row = cur.fetchone()
        if row:
            team_ids[team["name"]] = str(row[0])
        else:
            # Already exists — fetch it
            cur.execute("SELECT id FROM teams WHERE name = %s", (team["name"],))
            team_ids[team["name"]] = str(cur.fetchone()[0])

    print(f"Teams seeded: {list(team_ids.keys())}")

    # 2. Insert a demo database_connection for each team (required by master_config FK)
    db_connection_ids = {}
    demo_conn_str_enc = "demo_connection_string_encrypted"  # placeholder for demo
    for team_name, t_id in team_ids.items():
        dc_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO database_connections (id, team_id, name, connection_string_enc, db_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (dc_id, t_id, f"{team_name} DB", demo_conn_str_enc, "POSTGRES", datetime.utcnow()))
        row = cur.fetchone()
        if row:
            db_connection_ids[team_name] = str(row[0])
        else:
            cur.execute("SELECT id FROM database_connections WHERE team_id = %s LIMIT 1", (t_id,))
            db_connection_ids[team_name] = str(cur.fetchone()[0])

    # 3. Insert master_config rows — one per table per team
    total_inserted = 0
    for team_name, tables in TEAM_TABLE_ASSIGNMENTS.items():
        t_id = team_ids[team_name]
        dc_id = db_connection_ids[team_name]
        for (table_name, semantic_def, cols_meta) in tables:
            mc_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO master_config
                  (id, db_connection_id, team_id, table_name, semantic_definition, columns_metadata, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (mc_id, dc_id, t_id, table_name, semantic_def,
                  json.dumps(cols_meta), True, datetime.utcnow()))
            total_inserted += 1

    conn.commit()
    conn.close()
    print(f"seed_master_config.py complete. {total_inserted} master_config rows inserted across 5 teams.")
    print(f"Team IDs: {team_ids}")


if __name__ == "__main__":
    seed()
```

---

## Script 8: `seed_governance.py` — NEW SCRIPT
### Seeds all demo users including PLATFORM_ADMIN and ENTERPRISE_ANALYST

**This script must run LAST — after seed_master_config.py — because it needs team UUIDs.**

```python
"""
seed_governance.py

Seeds the 5 demo users for the hackathon presentation:
  1. admin@banquoite.dev        → PLATFORM_ADMIN (no team)
  2. enterprise@banquoite.dev   → ENTERPRISE_ANALYST (Team A home, access to Team A + Team B)
  3. analyst.a@banquoite.dev    → ANALYST (Team A only)
  4. analyst.b@banquoite.dev    → ANALYST (Team B only)
  5. owner.a@banquoite.dev      → DATA_OWNER (Team A)

Also seeds user_team_access rows:
  - analyst.a gets 1 row: Team A
  - analyst.b gets 1 row: Team B
  - enterprise gets 2 rows: Team A + Team B

Run AFTER seed_master_config.py.
Demo credentials are in 00_MASTER_SHARED_CONTEXT_FINAL.md Section 13.
"""

import os
import uuid
import psycopg2
from datetime import datetime
from passlib.context import CryptContext

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USERS = [
    {
        "email": "admin@banquoite.dev",
        "name": "Platform Admin",
        "password": "Admin1234!",
        "persona": "TECHNICAL",
        "role": "PLATFORM_ADMIN",
        "team_name": None,  # PLATFORM_ADMIN has no team
    },
    {
        "email": "enterprise@banquoite.dev",
        "name": "Enterprise Analyst",
        "password": "Enterprise1234!",
        "persona": "EXECUTIVE",
        "role": "ENTERPRISE_ANALYST",
        "team_name": "Team A — Payments",  # organisational home team
        "access_teams": ["Team A — Payments", "Team B — Operations"],
    },
    {
        "email": "analyst.a@banquoite.dev",
        "name": "Analyst Team A",
        "password": "Analyst1234!",
        "persona": "EXECUTIVE",
        "role": "ANALYST",
        "team_name": "Team A — Payments",
        "access_teams": ["Team A — Payments"],
    },
    {
        "email": "analyst.b@banquoite.dev",
        "name": "Analyst Team B",
        "password": "Analyst1234!",
        "persona": "TECHNICAL",
        "role": "ANALYST",
        "team_name": "Team B — Operations",
        "access_teams": ["Team B — Operations"],
    },
    {
        "email": "owner.a@banquoite.dev",
        "name": "Data Owner Team A",
        "password": "Owner1234!",
        "persona": "TECHNICAL",
        "role": "DATA_OWNER",
        "team_name": "Team A — Payments",
        "access_teams": ["Team A — Payments"],
    },
]


def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Fetch all team IDs
    cur.execute("SELECT name, id FROM teams")
    team_rows = cur.fetchall()
    if not team_rows:
        raise RuntimeError("No teams found. Run seed_master_config.py first.")
    team_id_map = {name: str(tid) for name, tid in team_rows}
    print(f"Found teams: {list(team_id_map.keys())}")

    # Find PLATFORM_ADMIN user id for granted_by field
    admin_user_id = None

    inserted_users = {}

    for u in DEMO_USERS:
        user_id = str(uuid.uuid4())
        hashed_pw = pwd_context.hash(u["password"])
        team_id = team_id_map.get(u["team_name"]) if u["team_name"] else None

        cur.execute("""
            INSERT INTO users (id, email, name, password_hash, persona, role, team_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE
              SET name = EXCLUDED.name,
                  password_hash = EXCLUDED.password_hash,
                  role = EXCLUDED.role,
                  team_id = EXCLUDED.team_id
            RETURNING id
        """, (user_id, u["email"], u["name"], hashed_pw,
              u["persona"], u["role"], team_id, datetime.utcnow()))

        returned_id = str(cur.fetchone()[0])
        inserted_users[u["email"]] = returned_id

        if u["role"] == "PLATFORM_ADMIN":
            admin_user_id = returned_id

        print(f"  User seeded: {u['email']} ({u['role']})")

    conn.commit()

    # Seed user_team_access rows
    for u in DEMO_USERS:
        if "access_teams" not in u:
            continue
        user_id = inserted_users[u["email"]]
        for team_name in u["access_teams"]:
            team_id = team_id_map.get(team_name)
            if not team_id:
                print(f"  WARNING: Team '{team_name}' not found for user {u['email']}")
                continue
            access_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO user_team_access (id, user_id, team_id, granted_by, granted_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, team_id) DO NOTHING
            """, (access_id, user_id, team_id, admin_user_id, datetime.utcnow()))
            print(f"  Access granted: {u['email']} → {team_name}")

    conn.commit()
    conn.close()
    print("\nseed_governance.py complete.")
    print("\nDemo credentials:")
    for u in DEMO_USERS:
        print(f"  {u['email']} / {u['password']}  ({u['role']})")


if __name__ == "__main__":
    seed()
```

---

## ChromaDB INGESTION: `vectorstore/ingest.py`

This script runs once. It loads complaint and support ticket text from the database, splits it, embeds it with a local model, and persists to ChromaDB. This enables the RAG agent to answer questions like "What are customers saying about payment failures?"

```python
"""
vectorstore/ingest.py

Ingests unstructured text from mock_customer_complaints and mock_customer_support_tickets
into ChromaDB for RAG retrieval by the rag_agent.

Run AFTER data generation scripts.
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

    cur.execute("""
        SELECT id::text, complaint_text, category, created_at::text
        FROM mock_customer_complaints
        WHERE complaint_text IS NOT NULL AND LENGTH(complaint_text) > 20
        LIMIT 50000
    """)
    complaints = cur.fetchall()

    cur.execute("""
        SELECT id::text, issue_description, priority, created_at::text
        FROM mock_customer_support_tickets
        WHERE issue_description IS NOT NULL AND LENGTH(issue_description) > 20
        LIMIT 50000
    """)
    tickets = cur.fetchall()
    conn.close()

    print(f"Loaded {len(complaints)} complaints and {len(tickets)} support tickets.")

    documents = []
    for row in complaints:
        documents.append(Document(
            page_content=row[1],
            metadata={"source": "customer_complaint", "id": row[0], "category": row[2], "date": row[3]}
        ))
    for row in tickets:
        documents.append(Document(
            page_content=row[1],
            metadata={"source": "support_ticket", "id": row[0], "priority": row[2], "date": row[3]}
        ))

    print(f"Total documents: {len(documents)}. Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"Total chunks: {len(chunks)}. Starting embedding (5–10 minutes on CPU)...")

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name="customer_reviews",
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )

    batch_size = 1000
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")

    print(f"\nDone. ChromaDB populated at: {CHROMA_PATH}")
    print("Commit the chroma_data/ folder before deploying to Render.")


if __name__ == "__main__":
    ingest()
```

---

## ADMIN PAGE: `frontend/app/(portal)/admin/page.tsx`

Build this page at Hour 24–32. It is accessible ONLY to users with `role === 'PLATFORM_ADMIN'`.

```typescript
// frontend/app/(portal)/admin/page.tsx
// 
// This page renders the AdminGovernancePanel component built by Person 3.
// Your responsibility: authentication guard + page shell.
// 
// Logic:
// 1. On mount, read JWT from cookie (js-cookie).
// 2. Decode the JWT payload (base64 decode the middle segment).
// 3. If role !== 'PLATFORM_ADMIN', router.push('/chat').
// 4. If role === 'PLATFORM_ADMIN', render <AdminGovernancePanel />.
//
// The AdminGovernancePanel component handles all API calls to /admin/* endpoints.
// It expects no props — it manages its own state internally.
//
// Page title in the browser tab: "Admin Governance | Banquoite"

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import AdminGovernancePanel from '@/components/AdminGovernancePanel';

export default function AdminPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = Cookies.get('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.role !== 'PLATFORM_ADMIN') {
        router.push('/chat');
        return;
      }
      setAuthorized(true);
    } catch {
      router.push('/login');
    }
  }, [router]);

  if (!authorized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Checking permissions...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Platform Governance</h1>
        <p className="text-gray-500 mb-8">
          Manage table assignments across all 5 teams and control cross-team data access.
        </p>
        <AdminGovernancePanel />
      </div>
    </div>
  );
}
```

---

## DEPLOYMENT STEPS

### Backend on Render.com

1. Go to render.com → New Web Service → Connect GitHub repo.
2. Root directory: `backend`
3. Build command:
   ```bash
   pip install -r requirements.txt && alembic upgrade head
   ```
4. Start command:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Add all environment variables from `.env.example` with real values.
6. **Critical:** Before deploying, run `ingest.py` locally and commit the `chroma_data/` folder. Render has an ephemeral filesystem — without this the RAG agent fails.
7. Deploy. Wait for green health check.

### Frontend on Vercel

1. Go to vercel.com → New Project → Import GitHub repo.
2. Root directory: `frontend`
3. Framework: Next.js (auto-detected).
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://banquoite-api.onrender.com`).
5. Deploy.

### Verify both deployments

```bash
# Backend health check
curl https://banquoite-api.onrender.com/health
# Expected: {"status": "ok"}

# Test demo login
curl -X POST https://banquoite-api.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@banquoite.dev", "password": "Admin1234!"}'
# Expected: {"access_token": "...", "user": {"role": "PLATFORM_ADMIN"}}

# Frontend: open https://your-project.vercel.app
# Should show login page
```

---

## README.md — REQUIRED CONTENT

```markdown
# Banquoite — Talk to Data

## Overview
Banquoite is an AI-powered enterprise intelligence portal built for the NatWest "Talk to Data: Seamless Self-Service Intelligence" hackathon. It allows banking teams to ask natural language questions about segregated enterprise data and receive instant, trustworthy answers.

- Non-technical EXECUTIVEs receive simplified explanations with charts.
- TECHNICALs receive technical detail with SQL, table references, and execution logs.
- Enterprise Analysts can query across multiple teams' data simultaneously.
- Every answer includes a Chain of Thought transparency layer showing exactly which data sources were used, what SQL was executed, and how the AI reasoned.

## Live Demo
- Frontend: [your-vercel-url.vercel.app]
- Backend API: [your-render-url.onrender.com]

## Demo Credentials
| Role | Email | Password |
|---|---|---|
| Platform Admin | admin@banquoite.dev | Admin1234! |
| Enterprise Analyst | enterprise@banquoite.dev | Enterprise1234! |
| Analyst (Team A) | analyst.a@banquoite.dev | Analyst1234! |
| Analyst (Team B) | analyst.b@banquoite.dev | Analyst1234! |
| Data Owner (Team A) | owner.a@banquoite.dev | Owner1234! |

## Features (Implemented)
- Multi-agent AI pipeline: Orchestrator → Relevancy → SQL Generation → RAG → Execution → Synthesis → Persona
- Persona-based output: EXECUTIVE (simplified English, charts) and TECHNICAL (SQL, technical detail)
- Chain of Thought transparency panel on every answer
- 4-tier role hierarchy: PLATFORM_ADMIN, DATA_OWNER, ENTERPRISE_ANALYST, ANALYST
- Enterprise Data Governance: Platform Admin assigns tables to teams and controls cross-team access
- Cross-domain analytics: Enterprise Analyst queries across 2+ teams simultaneously
- Self-service onboarding: Data Owners register database connections and configure table metadata
- Data segregation enforced at pipeline level — teams cannot access each other's data
- Personalized chatrooms with persistent conversation history
- Alert Center with pre-detected anomalies
- Scheduled query interface (UI + backend cron operational)
- Proactive anomaly detection via APScheduler
- Hybrid SQL + RAG: structured transaction data + unstructured customer reviews
- Mock enterprise dataset: ~1M rows across 40 tables covering 5 business domains

## Features (Partial — Planned for Production)
- Alert configuration UI (currently seeded via script; UI screen planned)
- Semantic caching (in-memory only for hackathon; Redis planned)
- Multi-database connection encryption (placeholder for hackathon)
- Email delivery via Resend (integrated; triggered by scheduler)

## Architecture

### Agent Pipeline (LangGraph)
```
User Query → Orchestrator → Relevancy Agent → [SQL Agent + RAG Agent in parallel]
                                             → Execution Agent → Synthesis Agent → Persona Agent → Answer
```

### Security Model
All AI access is governed by the `master_config` table. The pipeline only sees tables explicitly registered there. The `user_team_access` table controls which teams a user can query. For ANALYST: 1 team. For ENTERPRISE_ANALYST: 2+ teams.

### Role Hierarchy
```
PLATFORM_ADMIN → sees all 40 tables, assigns to teams, grants cross-team access
DATA_OWNER     → manages their own team's semantic definitions
ENTERPRISE_ANALYST → queries across 2+ teams simultaneously
ANALYST        → queries only their own team's data
```

## Tech Stack
- Frontend: Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- Backend: Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic
- Agent Framework: LangGraph 0.2.x, LangChain Core
- LLM: Groq API (llama-3.1-70b-versatile)
- Vector Store: ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
- Background Jobs: APScheduler
- Database: PostgreSQL on Neon.tech
- Deployment: Vercel (frontend) + Render.com (backend)

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Neon.tech PostgreSQL database
- A Groq API key (free at console.groq.com)
- A Resend API key (free at resend.com)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env values: DATABASE_URL, GROQ_API_KEY, RESEND_API_KEY, JWT_SECRET

# Run migrations
alembic upgrade head

# Generate mock data (run in order)
python -m backend.mock_data.generate_transactions
python -m backend.mock_data.generate_customers
python -m backend.mock_data.generate_system_logs
python -m backend.mock_data.generate_products_finance
python -m backend.mock_data.generate_geography
python -m backend.mock_data.seed_alerts
python -m backend.mock_data.seed_master_config
python -m backend.mock_data.seed_governance

# Ingest text data into ChromaDB (takes 5-10 minutes)
python -m backend.vectorstore.ingest

# Start server
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Demo Walkthrough

### Beat 1 — Data Isolation (ANALYST)
Log in as `analyst.a@banquoite.dev`. Ask: *"What is total payment volume this week?"*
→ AI uses only Team A's 12 payment tables. Team B's data is completely invisible.

### Beat 2 — Cross-Domain Synthesis (ENTERPRISE_ANALYST)
Log in as `enterprise@banquoite.dev`. Ask: *"Did the spike in API errors last Tuesday cause the increase in payment failures?"*
→ Pipeline queries both Team A (payment tables) and Team B (system log tables) simultaneously and synthesizes a cross-domain answer in a single response.

### Beat 3 — Governance Control (PLATFORM_ADMIN)
Log in as `admin@banquoite.dev`. Navigate to Admin panel. Revoke Team B access from the Enterprise Analyst.
Log back in as `enterprise@banquoite.dev`. Run the same query → answer now only reflects Team A data. Boundary enforced in real time.

## License
Apache 2.0 — see LICENSE file

## Team
[Team member names]
```

---

## LICENSE FILE

Create a file named `LICENSE` in the repository root with the full Apache 2.0 license text.
Fetch the official text from: https://www.apache.org/licenses/LICENSE-2.0.txt
Do not paraphrase or shorten it.

---

## .gitignore

```
# Python
__pycache__/
*.py[cod]
*.pyo
venv/
.env
*.egg-info/
dist/
build/
.pytest_cache/

# Node
node_modules/
.next/
.env.local
.env.development.local
.env.production.local

# ChromaDB — commit this ONLY if needed for Render deployment
# Remove the line below if you commit chroma_data/ for Render:
# chroma_data/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## COMPLIANCE AUDIT SCRIPT

Run this at Hour 44 before code freeze. Every item must pass.

```bash
#!/bin/bash
echo "====== BANQUOITE COMPLIANCE AUDIT ======"

# 1. Check for hardcoded secrets
echo ""
echo "=== 1. Checking for hardcoded secrets ==="
GROQ_FOUND=$(grep -r "gsk_" . --include="*.py" --include="*.ts" --include="*.tsx" --exclude-dir=".git" | grep -v ".env")
RESEND_FOUND=$(grep -r "re_" . --include="*.py" --include="*.ts" --include="*.tsx" --exclude-dir=".git" | grep -v ".env" | grep -v "resolved" | grep -v "created")
if [ -z "$GROQ_FOUND" ] && [ -z "$RESEND_FOUND" ]; then
  echo "PASS: No hardcoded secrets found."
else
  echo "FAIL: Hardcoded secrets detected:"
  echo "$GROQ_FOUND"
  echo "$RESEND_FOUND"
fi

# 2. Check all commits have DCO sign-off
echo ""
echo "=== 2. Checking DCO sign-off on commits ==="
UNSIGNED=$(git log --format="%H %s%n%b" | grep -v "Signed-off-by" | grep -v "^$" | grep -v "^[0-9a-f]\{40\}" | head -20)
if [ -z "$UNSIGNED" ]; then
  echo "PASS: All commits appear signed."
else
  echo "WARN: Check these commits for missing sign-off:"
  git log --format="%H %ae" | head -20
fi

# 3. Verify .env.example has no real values
echo ""
echo "=== 3. Checking .env.example ==="
REAL_VALS=$(grep -E "gsk_|re_[a-zA-Z0-9]{20}" backend/.env.example)
if [ -z "$REAL_VALS" ]; then
  echo "PASS: .env.example has no real secret values."
else
  echo "FAIL: Real secret values found in .env.example"
fi

# 4. Confirm LICENSE file exists
echo ""
echo "=== 4. Checking LICENSE file ==="
if [ -f "LICENSE" ]; then
  echo "PASS: LICENSE file exists."
else
  echo "FAIL: LICENSE file missing. Create it with Apache 2.0 text."
fi

# 5. Confirm README.md exists
echo ""
echo "=== 5. Checking README.md ==="
if [ -f "README.md" ]; then
  echo "PASS: README.md exists."
else
  echo "FAIL: README.md missing."
fi

# 6. Confirm tests folder has minimum 4 files
echo ""
echo "=== 6. Checking tests folder ==="
TEST_COUNT=$(find backend/tests -name "test_*.py" | wc -l)
echo "Found $TEST_COUNT test files."
if [ "$TEST_COUNT" -ge 4 ]; then
  echo "PASS: Minimum test count met."
else
  echo "FAIL: Need at least 4 test files in backend/tests/."
fi

# 7. Confirm seed_governance.py has been run (check demo users exist)
echo ""
echo "=== 7. Checking demo users exist ==="
echo "Run this manually in Neon SQL console:"
echo "  SELECT email, role FROM users WHERE email LIKE '%@banquoite.dev';"
echo "Expected: 5 rows (admin, enterprise, analyst.a, analyst.b, owner.a)"

# 8. Confirm 40 mock tables exist
echo ""
echo "=== 8. Checking mock table count ==="
echo "Run this manually in Neon SQL console:"
echo "  SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'mock_%';"
echo "Expected: 40"

# 9. Confirm master_config has 40 rows
echo ""
echo "=== 9. Checking master_config row count ==="
echo "Run this manually in Neon SQL console:"
echo "  SELECT COUNT(*) FROM master_config WHERE is_active = TRUE;"
echo "Expected: 40"

echo ""
echo "====== AUDIT COMPLETE ======"
echo "Fix any FAIL items before code freeze at Hour 44."
```

---

## FINAL CHECKLIST — YOUR PERSONAL SIGN-OFF

At hour 44, confirm every item:

- [ ] GitHub repo is private, all commits signed with `-s`
- [ ] Neon.tech has 12 core tables + 40 mock tables (52 total)
- [ ] `teams` table has exactly 5 rows: Team A, B, C, D, E
- [ ] `master_config` has exactly 40 rows (one per mock table per team), all `is_active=TRUE`
- [ ] `users` table has 5 demo users with correct roles
- [ ] `user_team_access` has 3 rows: enterprise→A, enterprise→B, analyst.a→A, analyst.b→B, owner.a→A (5 rows total)
- [ ] `chroma_data/` committed and deployed to Render
- [ ] Backend health check passes: `GET /health` returns `{"status": "ok"}`
- [ ] Frontend loads on Vercel URL without errors
- [ ] Login works for `admin@banquoite.dev` with `Admin1234!`
- [ ] Login works for `enterprise@banquoite.dev` with `Enterprise1234!`
- [ ] Admin page (`/admin`) renders correctly and is blocked for non-admin users
- [ ] All 6 demo use cases verified working (see Master doc Section 12)
- [ ] 3-beat governance demo sequence rehearsed and working end-to-end
- [ ] `README.md` complete with all sections including demo credentials
- [ ] `LICENSE` file present with full Apache 2.0 text
- [ ] `.gitignore` committed
- [ ] `.env.example` committed with all variables, no real values
- [ ] No hardcoded secrets in any `.py`, `.ts`, or `.tsx` file
- [ ] `requirements.txt` and `package.json` present and complete
- [ ] `backend/tests/` has minimum 4 test files
