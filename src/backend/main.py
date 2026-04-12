"""
Scout — FastAPI Application Entry Point

ELI5 (What does this file do?):
Think of this file as the front door and the receptionist of our application. 
When anyone (like the frontend web app) wants to talk to our backend services, they knock here first. 
This file sets up the main application, turns on the background workers (like taking out the trash on a schedule), 
opens up the communication channels so the web app can safely talk to the backend, 
and organizes all the different "departments" (like authentication, chat, and admin) so requests go to the right place. 
It also keeps a quick health check to let the outside world know, "Hey, I'm alive and working!"
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables before any other imports.
# Override existing env vars so the local backend/.env is authoritative in dev.
load_dotenv(override=True)

# Ensure absolute imports like `backend.*` work when starting from the backend folder.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.api import admin, alerts, auth, chat, config, dashboard, scheduled, users
from backend.services.scheduler_service import shutdown_scheduler, start_scheduler

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — manages background scheduler lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background scheduler on startup, shut it down on exit."""
    logger.info("Starting Scout API — initialising background services")
    start_scheduler()
    yield
    logger.info("Shutting down Scout API — stopping background services")
    shutdown_scheduler()


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Scout API",
    description=(
        "Enterprise AI Data Intelligence Platform. "
        "Natural language queries against segregated enterprise data "
        "with Chain of Thought transparency."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chatrooms", tags=["Chat"])
app.include_router(config.router, prefix="/config", tags=["Configuration"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(scheduled.router, prefix="/scheduled", tags=["Scheduled Queries"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(users.router, prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok", "service": "scout-api", "version": "1.0.0"}


@app.get("/health/llm", tags=["System"])
def health_llm():
    """LLM key pool status — shows available/cooling-down keys and usage stats."""
    from backend.agents.llm import _pool
    return {
        "total_keys": len(_pool.keys),
        "current_index": _pool._index,
    }

