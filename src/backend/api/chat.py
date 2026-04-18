# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Banquoite — Chat API

ELI5 (What does this file do?):
This is the most critical file—it's the telephone wire between the user's screen and our AI factory.
When a user types a question and hits send, this file receives it, saves it to the chat history, 
and hands it over to the AI Agents (the pipeline). As the AI figures out the answer, 
this file continuously streams the words back to the user's screen letter-by-letter so it feels fast and interactive.

Endpoints:
  GET  /chatrooms                        — list user's chatrooms
  POST /chatrooms                        — create a new chatroom
  GET  /chatrooms/{chatroom_id}/messages — retrieve message history
  POST /chatrooms/{chatroom_id}/message  — run pipeline, stream response via SSE
"""

import asyncio
import concurrent.futures
import json
import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.db.models import Chatroom, Message, User, UserTeamAccess
from backend.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pipeline execution infrastructure
# ---------------------------------------------------------------------------
# Dedicated pool so heavy LLM work doesn't starve FastAPI's default executor
_PIPELINE_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=16, thread_name_prefix="pipeline"
)
# Cap concurrent pipeline invocations to avoid Groq rate-limit storms
_PIPELINE_SEMAPHORE = asyncio.Semaphore(8)

import decimal, datetime, uuid

class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)
def _dumps(obj) -> str:
    return json.dumps(obj, cls=_JSONEncoder)

def _sanitize_for_json(obj):
    """Recursively convert non-JSON-serializable types in a dict/list."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(i) for i in obj]
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj
# ---------------------------------------------------------------------------
# Try to import the real pipeline; fall back to a mock for independent testing
# ---------------------------------------------------------------------------
try:
    from backend.agents.pipeline import pipeline as _real_pipeline

    PIPELINE_AVAILABLE = True
except Exception as exc:
    logger.warning("Agent pipeline not available — using mock fallback: %s", exc)
    PIPELINE_AVAILABLE = False
    _real_pipeline = None


def _mock_pipeline_invoke(state: dict) -> dict:
    """
    Mock fallback when the real agent pipeline is unavailable.
    Returns a canned response so the backend can be tested independently.
    """
    return {
        **state,
        "final_answer": (
            f"[Mock Response] I received your question: \"{state['user_query']}\". "
            "The agent pipeline is not yet connected. Once Person 1's agents are "
            "integrated, this will return real AI-generated answers with full "
            "Chain of Thought transparency."
        ),
        "chain_of_thought": {
            "sources": [],
            "sql_executed": None,
            "rag_chunks_used": 0,
            "agent_path": ["mock_fallback"],
            "query_intent": "MOCK",
            "confidence": "low",
            "tables_searched": [],
            "tables_used": [],
            "teams_accessed": state.get("allowed_team_ids", []),
        },
    }


router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class CreateChatroomRequest(BaseModel):
    """Request body for creating a new chatroom."""

    name: str = Field(..., min_length=1, max_length=255)
    agent_mode: str = Field("DATABASE", pattern="^(DATABASE|SLACK_JIRA)$")


class ChatroomResponse(BaseModel):
    """Response shape for a chatroom."""

    id: str
    name: str | None
    agent_mode: str = "DATABASE"
    created_at: str
    last_message_preview: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Response shape for a single message."""

    id: str
    role: str
    content: str
    chain_of_thought: dict | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    """Request body for sending a message to the pipeline."""

    query: str = Field(..., min_length=1, max_length=5000)
    persona: str | None = Field(None, pattern="^(EXECUTIVE|TECHNICAL)$")


# ---------------------------------------------------------------------------
# GET /chatrooms — list user's chatrooms
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ChatroomResponse])
async def list_chatrooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return all chatrooms belonging to the authenticated user.

    Uses 2 queries instead of N+1: one for chatrooms, one batch for latest messages.
    """
    # Query 1: All chatrooms for this user
    result = await db.execute(
        select(Chatroom)
        .where(Chatroom.user_id == current_user.id)
        .order_by(Chatroom.created_at.desc())
    )
    chatrooms = result.scalars().all()

    if not chatrooms:
        return []

    # Query 2: Latest message per chatroom in a single batch query
    # Use a subquery to find the max created_at per chatroom, then join to get content
    chatroom_ids = [cr.id for cr in chatrooms]

    # Subquery: get the latest message timestamp per chatroom
    latest_ts = (
        select(
            Message.chatroom_id,
            func.max(Message.created_at).label("max_created_at"),
        )
        .where(Message.chatroom_id.in_(chatroom_ids))
        .group_by(Message.chatroom_id)
        .subquery()
    )

    # Main query: join back to get the actual message content
    msg_result = await db.execute(
        select(Message.chatroom_id, Message.content)
        .join(
            latest_ts,
            (Message.chatroom_id == latest_ts.c.chatroom_id)
            & (Message.created_at == latest_ts.c.max_created_at),
        )
    )
    preview_map: dict = {}
    for row in msg_result.all():
        content = row.content
        preview_map[row.chatroom_id] = (
            content[:100] + "..." if content and len(content) > 100 else content
        )

    return [
        ChatroomResponse(
            id=str(cr.id),
            name=cr.name,
            agent_mode=cr.agent_mode,
            created_at=cr.created_at.isoformat(),
            last_message_preview=preview_map.get(cr.id),
        )
        for cr in chatrooms
    ]


# ---------------------------------------------------------------------------
# POST /chatrooms — create a new chatroom
# ---------------------------------------------------------------------------
@router.post("", response_model=ChatroomResponse, status_code=status.HTTP_201_CREATED)
async def create_chatroom(
    body: CreateChatroomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new isolated chatroom for the authenticated user."""
    chatroom = Chatroom(
        user_id=current_user.id,
        name=body.name,
        agent_mode=body.agent_mode,
    )
    db.add(chatroom)
    await db.commit()
    await db.refresh(chatroom)

    return ChatroomResponse(
        id=str(chatroom.id),
        name=chatroom.name,
        agent_mode=chatroom.agent_mode,
        created_at=chatroom.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# PATCH /chatrooms/{chatroom_id} — rename a chatroom
# ---------------------------------------------------------------------------
class RenameChatroomRequest(BaseModel):
    """Request body for renaming a chatroom."""
    name: str = Field(..., min_length=1, max_length=255)


@router.patch("/{chatroom_id}", response_model=ChatroomResponse)
async def rename_chatroom(
    chatroom_id: str,
    body: RenameChatroomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Rename an existing chatroom owned by the authenticated user."""
    try:
        cr_uuid = uuid.UUID(chatroom_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chatroom ID")

    result = await db.execute(select(Chatroom).where(Chatroom.id == cr_uuid))
    chatroom = result.scalar_one_or_none()

    if not chatroom or chatroom.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")

    chatroom.name = body.name
    await db.commit()
    await db.refresh(chatroom)

    return ChatroomResponse(
        id=str(chatroom.id),
        name=chatroom.name,
        created_at=chatroom.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# DELETE /chatrooms/{chatroom_id} — delete a chatroom and its history
# ---------------------------------------------------------------------------
@router.delete("/{chatroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatroom(
    chatroom_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a chatroom and all its associated messages."""
    try:
        cr_uuid = uuid.UUID(chatroom_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chatroom ID")

    # Verify ownership
    result = await db.execute(select(Chatroom).where(Chatroom.id == cr_uuid))
    chatroom = result.scalar_one_or_none()

    if not chatroom or chatroom.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found or unauthorized")

    # Explicitly delete associated messages (to ensure integrity if CASCADE is missing)
    from backend.db.models import Message as DbMessage
    from sqlalchemy import delete
    await db.execute(delete(DbMessage).where(DbMessage.chatroom_id == cr_uuid))
    
    # Delete the chatroom
    await db.delete(chatroom)
    await db.commit()

    return None


# ---------------------------------------------------------------------------
# GET /chatrooms/{chatroom_id}/messages — retrieve message history
# ---------------------------------------------------------------------------
@router.get("/{chatroom_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    chatroom_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return all messages in a chatroom, ordered by creation time."""
    # Validate chatroom ownership
    try:
        cr_uuid = uuid.UUID(chatroom_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chatroom ID")

    result = await db.execute(select(Chatroom).where(Chatroom.id == cr_uuid))
    chatroom = result.scalar_one_or_none()

    if not chatroom or chatroom.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.chatroom_id == cr_uuid)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            chain_of_thought=m.chain_of_thought,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


# ---------------------------------------------------------------------------
# POST /chatrooms/{chatroom_id}/message — run pipeline, stream via SSE
# ---------------------------------------------------------------------------
@router.post("/{chatroom_id}/message")
async def send_message(
    chatroom_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Send a user message, invoke the AI pipeline, and stream the response
    back as Server-Sent Events (SSE).

    SSE event types:
      - {"type": "chunk", "content": "word "}  — streamed answer fragment
      - {"type": "done", "chain_of_thought": {...}}  — final CoT payload
      - {"type": "error", "message": "..."}  — error notification
    """
    # Validate chatroom ownership
    try:
        cr_uuid = uuid.UUID(chatroom_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chatroom ID")

    result = await db.execute(select(Chatroom).where(Chatroom.id == cr_uuid))
    chatroom = result.scalar_one_or_none()

    if not chatroom or chatroom.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")

    user_query = body.query.strip()

    # Save user message to DB
    user_msg = Message(
        chatroom_id=cr_uuid,
        role="USER",
        content=user_query,
    )
    db.add(user_msg)
    await db.commit()

    # Fetch allowed_team_ids from user_team_access for this user
    access_result = await db.execute(
        select(UserTeamAccess.team_id).where(
            UserTeamAccess.user_id == current_user.id
        )
    )
    allowed_team_ids = [str(row[0]) for row in access_result.fetchall()]

    # Fallback: if no explicit access rows, use the user's own team
    if not allowed_team_ids and current_user.team_id:
        allowed_team_ids = [str(current_user.team_id)]

    # Final fallback: if user has no team at all, grant access to ALL teams
    # so the pipeline can still find tables (important for demo / new users)
    if not allowed_team_ids:
        from backend.db.models import Team
        all_teams_result = await db.execute(select(Team.id))
        allowed_team_ids = [str(row[0]) for row in all_teams_result.fetchall()]
        logger.info("User %s has no team — granting access to all %d teams for pipeline", current_user.email, len(allowed_team_ids))

    logger.info("[CHAT DEBUG] user=%s, team_id=%s, allowed_team_ids=%s", current_user.email, current_user.team_id, allowed_team_ids)

    # Fetch last 3 messages to find the previous complete turn (1 user + 1 assistant)
    # We fetch 3 because the current user message is already saved in the DB.
    history_result = await db.execute(
        select(Message)
        .where(Message.chatroom_id == cr_uuid)
        .order_by(Message.created_at.desc())
        .limit(3)
    )
    recent_messages = history_result.scalars().all()
    recent_messages.reverse()  # oldest first

    # Extract the most recent user+assistant pair
    previous_query = ""
    previous_answer = ""
    previous_sql = ""
    previous_tables_used = []

    # Walk pairs to find the last complete turn
    i = 0
    msgs = [m for m in recent_messages]
    while i < len(msgs) - 1:
        if msgs[i].role == "USER" and msgs[i+1].role == "ASSISTANT":
            last_user_msg = msgs[i]
            last_assistant_msg = msgs[i+1]
            previous_query = last_user_msg.content
            previous_answer = last_assistant_msg.content
            cot = last_assistant_msg.chain_of_thought or {}
            previous_sql = cot.get("sql_executed", "")
            previous_tables_used = cot.get("tables_used", [])
        i += 1

    async def generate():
        try:
            # Build the pipeline state from the Master Context spec
            initial_state = {
                "user_query": user_query,
                "user_id": str(current_user.id),
                "user_persona": body.persona or current_user.persona,
                "team_id": str(current_user.team_id) if current_user.team_id else "",
                "allowed_team_ids": allowed_team_ids,
                "current_date": date.today().isoformat(),
                "query_intent": "",
                "routing_decision": {},
                "relevant_tables": [],
                "generated_sql": "",
                "sql_results": [],
                "rag_chunks": [],
                "synthesized_context": "",
                "final_answer": "",
                "chain_of_thought": {},
                "sql_tables_used": [],
                "sql_retry_count": 0,
                "sql_error": "",
                "previous_query": previous_query,
                "previous_answer": previous_answer,
                "previous_sql": previous_sql,
                "previous_tables_used": previous_tables_used,
                "agent_mode": chatroom.agent_mode,
            }


            # Choose real pipeline or mock fallback
            if PIPELINE_AVAILABLE and _real_pipeline is not None:
                invoke_fn = _real_pipeline.invoke
            else:
                invoke_fn = _mock_pipeline_invoke

            # Run pipeline in dedicated pool with concurrency cap and timeout.
            async with _PIPELINE_SEMAPHORE:
                loop = asyncio.get_event_loop()
                pipeline_result = await asyncio.wait_for(
                    loop.run_in_executor(_PIPELINE_POOL, invoke_fn, initial_state),
                    timeout=120.0,
                )

            final_answer = pipeline_result.get("final_answer", "")
            cot = _sanitize_for_json(pipeline_result.get("chain_of_thought", {}))

            # Stream answer word-by-word for smooth typing effect
            words = final_answer.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {_dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)

            # Send final event with full Chain of Thought
            yield f"data: {_dumps({'type': 'done', 'chain_of_thought': cot})}\n\n"

            # Save assistant message to DB
            assistant_msg = Message(
                chatroom_id=cr_uuid,
                role="ASSISTANT",
                content=final_answer,
                chain_of_thought=cot,
            )
            db.add(assistant_msg)
            await db.commit()

        except asyncio.TimeoutError:
            logger.warning("Pipeline timed out for chatroom %s after 120s", chatroom_id)
            yield f"data: {_dumps({'type': 'error', 'message': 'Request timed out. Please try again.'})}\n\n"
        except Exception as exc:
            logger.exception("Pipeline error for chatroom %s", chatroom_id)
            yield f"data: {_dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
