# PERSON 2 — BACKEND ENGINEER
## Read 00_MASTER_SHARED_CONTEXT.md first. Everything in that document applies to you.

---

## YOUR ROLE

You own all FastAPI routes, SQLAlchemy models, Alembic migrations, APScheduler background jobs, authentication middleware, and deployment configuration. You call Person 1's compiled `pipeline` object from `chat.py`. You provide Person 1 with `get_db_session()`. You never write agent logic, never write prompt templates, never write frontend code.

---

## YOUR FILES — COMPLETE LIST

```
backend/main.py
backend/db/models.py                     ← Write at hour 0–2 with team
backend/db/session.py
backend/db/migrations/                   ← Alembic, run at hour 2
backend/api/auth.py
backend/api/chat.py                      ← Most critical file — calls pipeline
backend/api/config.py
backend/api/scheduled.py
backend/api/alerts.py
backend/api/dashboard.py
backend/api/users.py
backend/services/scheduler_service.py
backend/services/anomaly_service.py
backend/services/notification_service.py
backend/requirements.txt
backend/.env.example
```

---

## HOUR-BY-HOUR PLAN

### Hour 0–2 (with team)
- Write `models.py` — all SQLAlchemy models from the DB schema in Master Shared Context.
- Run Alembic init: `alembic init migrations`
- Create first migration: `alembic revision --autogenerate -m "initial"`
- Run migration: `alembic upgrade head`
- Confirm all 11 core tables exist in Neon DB.

### Hour 2–16 (build all routes)
Build in this order: `session.py` → `auth.py` → `chat.py` (stub returning mock) → `config.py` → `alerts.py` → `dashboard.py` → `users.py` → `scheduled.py`

### Hour 16–20 (integration with Person 1)
- Person 1 has `pipeline.invoke()` working.
- Wire it into `chat.py`. Replace mock SSE with real pipeline call.
- Run one live query together. Debug until it works.

### Hour 20–28 (background services)
- Build `scheduler_service.py` with APScheduler.
- Build `anomaly_service.py` with APScheduler.
- Build `notification_service.py` with Resend.
- Add `PATCH /users/me` to `users.py`.

### Hour 28–36 (testing + deployment)
- Test all routes with Postman or curl.
- Fix any CORS issues.
- Confirm deployed backend on Render/Railway returns correct responses.

### Hour 36–44 (compliance)
- Write `.env.example` with every variable.
- Audit for hardcoded secrets.
- Add Apache 2.0 license check.

---

## FILE 1: `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.services.scheduler_service import start_scheduler, shutdown_scheduler
from backend.api import auth, chat, config, scheduled, alerts, dashboard, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(title="Banquoite API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chatrooms", tags=["chat"])
app.include_router(config.router, prefix="/config", tags=["config"])
app.include_router(scheduled.router, prefix="/scheduled", tags=["scheduled"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

---

## FILE 2: `db/models.py`

Implement all SQLAlchemy ORM models from the schema in Master Shared Context section 5.

Key points:
- Use `UUID` as primary key with `default=uuid.uuid4`
- Use `DateTime(timezone=True)` for all timestamp fields
- Use `JSONB` from `sqlalchemy.dialects.postgresql` for JSON fields
- `columns_metadata` in `MasterConfig` is `JSONB`
- `chain_of_thought` in `Message` is `JSONB`
- `data_snapshot` in `Alert` is `JSONB`
- `query_result` in `DashboardCard` is `JSONB`
- `result_data` in `ScheduledReport` is `JSONB`

Model names: `User`, `Team`, `DatabaseConnection`, `MasterConfig`, `Chatroom`, `Message`, `ScheduledQuery`, `ScheduledReport`, `AlertConfiguration`, `Alert`, `DashboardCard`

---

## FILE 3: `db/session.py`

Provide two sessions: async for FastAPI routes, sync for agent use.

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")

# Async engine — for FastAPI routes
async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Sync engine — for agents (Person 1 uses this)
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(sync_engine)

async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@contextmanager
def get_sync_session() -> Session:
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## FILE 4: `api/auth.py`

Implement two endpoints: `POST /auth/register` and `POST /auth/login`.

**Register logic:**
1. Check email not already taken — if taken, return 400
2. Hash password with `passlib bcrypt`
3. Find or create `Team` by `team_name` from request body
4. Create `User` with `persona`, `role`, `team_id`
5. Generate JWT with payload: `{"sub": str(user.id), "email": user.email, "role": user.role, "team_id": str(user.team_id)}`
6. Return: `{access_token, token_type: "bearer", user: {id, email, name, persona, role}}`

**Login logic:**
1. Find user by email — if not found, return 401
2. Verify password with bcrypt
3. Generate JWT with same payload
4. Return same shape

**JWT auth dependency (reused across all routes):**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db = Depends(get_async_session)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_data_owner(current_user: User = Depends(get_current_user)):
    if current_user.role != "DATA_OWNER":
        raise HTTPException(status_code=403, detail="Data Owner role required")
    return current_user
```

---

## FILE 5: `api/chat.py` — THE MOST CRITICAL FILE

This is the file that connects the frontend to Person 1's agent pipeline. Get this right.

**Endpoints:**
- `GET /chatrooms` — list user's chatrooms
- `POST /chatrooms` — create chatroom
- `GET /chatrooms/{chatroom_id}/messages` — get history
- `POST /chatrooms/{chatroom_id}/message` — run pipeline, stream response

**SSE streaming implementation:**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio
from datetime import date

from backend.agents.pipeline import pipeline
from backend.db.session import get_async_session
from backend.db.models import User, Chatroom, Message
from backend.api.auth import get_current_user
from langchain_community.chat_message_histories import SQLChatMessageHistory

router = APIRouter()

@router.post("/{chatroom_id}/message")
async def send_message(
    chatroom_id: str,
    body: dict,  # {"query": str}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Verify chatroom belongs to user
    chatroom = await db.get(Chatroom, chatroom_id)
    if not chatroom or str(chatroom.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Chatroom not found")

    user_query = body.get("query", "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Save user message to DB
    user_msg = Message(
        chatroom_id=chatroom_id,
        role="USER",
        content=user_query
    )
    db.add(user_msg)
    await db.commit()

    async def generate():
        try:
            # Build initial pipeline state
            initial_state = {
                "user_query": user_query,
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

            # Run pipeline synchronously in thread pool (pipeline.invoke is synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, pipeline.invoke, initial_state)

            final_answer = result["final_answer"]
            cot = result["chain_of_thought"]

            # Stream answer in chunks (split by words for smooth effect)
            words = final_answer.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)

            # Send final event with full CoT
            yield f"data: {json.dumps({'type': 'done', 'chain_of_thought': cot})}\n\n"

            # Save assistant message to DB
            assistant_msg = Message(
                chatroom_id=chatroom_id,
                role="ASSISTANT",
                content=final_answer,
                chain_of_thought=cot
            )
            db.add(assistant_msg)
            await db.commit()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## FILE 6: `api/config.py`

**Endpoints:**
- `POST /config/connections` — store new DB connection (role=DATA_OWNER required)
- `GET /config/scan/{connection_id}` — query INFORMATION_SCHEMA of the registered DB
- `POST /config/tables` — save a table to master_config (role=DATA_OWNER required)
- `GET /config/tables` — return all active master_config entries for the user's team
- `PATCH /config/tables/{id}` — update is_active or semantic_definition

**Schema scanner implementation:**
```python
@router.get("/scan/{connection_id}")
async def scan_database(
    connection_id: str,
    current_user: User = Depends(require_data_owner),
    db: AsyncSession = Depends(get_async_session)
):
    conn = await db.get(DatabaseConnection, connection_id)
    if not conn or str(conn.team_id) != str(current_user.team_id):
        raise HTTPException(status_code=404)
    
    # For hackathon: scan our own mock database (not the stored connection)
    # In production: decrypt connection string and connect to external DB
    # For demo: query our Neon DB's INFORMATION_SCHEMA for mock_ tables
    
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_name LIKE 'mock_%'
        ORDER BY table_name
    """))
    tables = [{"table_name": row[0], "column_count": row[1]} for row in result.fetchall()]
    return tables
```

---

## FILE 7: `api/alerts.py`

```python
GET /alerts → return all alerts WHERE team_id = current_user.team_id ORDER BY created_at DESC LIMIT 50
PATCH /alerts/{id}/read → set is_read = True WHERE id = alert_id AND team_id = current_user.team_id
```

---

## FILE 8: `api/scheduled.py`

```python
GET /scheduled → return all scheduled_queries WHERE user_id = current_user.id
POST /scheduled → create new scheduled_query, compute next_run_at from cron_expression using APScheduler's CronTrigger
PATCH /scheduled/{id} → update is_active
GET /scheduled/{id}/history → return scheduled_reports WHERE scheduled_query_id = id ORDER BY executed_at DESC
```

---

## FILE 9: `api/dashboard.py` and `api/users.py`

**dashboard.py:**
```python
GET /dashboard/cards → return dashboard_cards WHERE user_id = current_user.id ORDER BY created_at DESC LIMIT 20
```

**users.py:**
```python
GET /users/me → return current user object
PATCH /users/me → update persona or name. If persona changes, update and return updated user.
```

---

## FILE 10: `services/scheduler_service.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Run scheduled queries check every minute
    scheduler.add_job(run_due_scheduled_queries, "interval", minutes=1)
    # Run anomaly detection every 15 minutes
    scheduler.add_job(run_anomaly_detection, "interval", minutes=15)
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()

async def run_due_scheduled_queries():
    """
    1. Query scheduled_queries WHERE is_active=True AND next_run_at <= NOW()
    2. For each due query:
       a. Build PipelineState with query_text as user_query
       b. Run pipeline.invoke() synchronously
       c. Save result to scheduled_reports table
       d. If delivery == 'DASHBOARD': create dashboard_card record
       e. If delivery == 'EMAIL': call notification_service.send_report_email()
       f. Update last_run_at and next_run_at on scheduled_query
    """
    pass  # Implement with DB session + pipeline call

async def run_anomaly_detection():
    """
    1. Import run_anomaly_check from anomaly_agent
    2. Call it with a DB session
    3. For each triggered alert returned: insert into alerts table
    """
    pass
```

---

## FILE 11: `services/notification_service.py`

```python
import resend
import os

resend.api_key = os.getenv("RESEND_API_KEY")

def send_report_email(to_email: str, query_text: str, answer: str, executed_at: str):
    resend.Emails.send({
        "from": "reports@banquoite.app",
        "to": to_email,
        "subject": f"Banquoite Scheduled Report — {executed_at}",
        "html": f"""
        <h2>Your Scheduled Report</h2>
        <p><strong>Query:</strong> {query_text}</p>
        <hr>
        <p>{answer}</p>
        <p style="color: #888; font-size: 12px;">Delivered by Banquoite Intelligence Platform</p>
        """
    })
```

---

## ALEMBIC SETUP

```bash
cd backend
alembic init db/migrations
# Edit alembic.ini: sqlalchemy.url = your DATABASE_URL (sync version, not asyncpg)
# Edit db/migrations/env.py: import models and set target_metadata = Base.metadata

alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

After running, verify in Neon dashboard that all 11 core tables are created.

---

## DEPLOYMENT — RENDER.COM

Create `render.yaml` in backend root:
```yaml
services:
  - type: web
    name: banquoite-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: RESEND_API_KEY
        sync: false
      - key: JWT_SECRET
        sync: false
      - key: CHROMA_PERSIST_PATH
        value: ./chroma_data
```

**Critical:** ChromaDB on Render uses the filesystem. Chroma data is ephemeral on Render free tier. For the demo: run the ingestion script locally, then commit the `chroma_data/` folder to the repo or use Railway which has persistent storage.

---

## `.env.example`

```bash
# PostgreSQL on Neon.tech (use asyncpg version)
DATABASE_URL=postgresql+asyncpg://user:password@host.neon.tech/neondb

# Groq — free tier at console.groq.com
GROQ_API_KEY=gsk_your_key_here

# Resend — free tier at resend.com
RESEND_API_KEY=re_your_key_here

# JWT — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=your_32_character_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ChromaDB — local path
CHROMA_PERSIST_PATH=./chroma_data
```
