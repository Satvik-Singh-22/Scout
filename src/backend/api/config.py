"""
Banquoite — Configuration API (Data Owner)

ELI5 (What does this file do?):
Think of this file as the IT setup department for data owners.
It allows data owners to securely plug their company's database into our app. 
Once plugged in, it scans the database and lets the owner pick and choose exactly which tables 
the AI is allowed to look at. This creates a strict boundary so the AI never sees private or off-limits data.

Endpoints:
  POST  /config/connections        — register a new DB connection
  GET   /config/scan/{conn_id}     — scan INFORMATION_SCHEMA of registered DB
  POST  /config/tables             — save a table to master_config
  GET   /config/tables             — list active master_config entries for the team
  PATCH /config/tables/{id}        — update is_active or semantic_definition
"""

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_data_owner
from backend.db.models import DatabaseConnection, MasterConfig, User
from backend.db.session import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class CreateConnectionRequest(BaseModel):
    """Request body for registering a new database connection."""

    name: str = Field(..., min_length=1, max_length=255)
    db_type: str = Field(..., pattern="^(POSTGRES|MYSQL)$")
    connection_string: str = Field(..., min_length=1)


class ConnectionResponse(BaseModel):
    """Response shape for a database connection."""

    id: str
    name: str
    db_type: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ColumnMetadata(BaseModel):
    """Schema for a single column's metadata."""

    name: str
    type: str
    description: str = ""


class CreateTableRequest(BaseModel):
    """Request body for saving a table to master_config."""

    db_connection_id: str
    table_name: str = Field(..., min_length=1, max_length=255)
    semantic_definition: str = Field(..., min_length=1)
    columns_metadata: list[ColumnMetadata]


class TableResponse(BaseModel):
    """Response shape for a master_config entry."""

    id: str
    table_name: str
    semantic_definition: str
    columns_metadata: list | dict | None = None
    is_active: bool
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UpdateTableRequest(BaseModel):
    """Request body for updating a master_config entry."""

    is_active: bool | None = None
    semantic_definition: str | None = None


class ScanResult(BaseModel):
    """Result shape from scanning a database's INFORMATION_SCHEMA."""

    table_name: str
    column_count: int


# ---------------------------------------------------------------------------
# POST /config/connections — register a new DB connection
# ---------------------------------------------------------------------------
@router.post(
    "/connections",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    body: CreateConnectionRequest,
    current_user: User = Depends(require_data_owner),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Register a new database connection for the Data Owner's team.
    The connection string is stored encrypted (encryption at rest via DB-level
    encryption; application-level encryption is a production enhancement).
    """
    conn = DatabaseConnection(
        team_id=current_user.team_id,
        name=body.name,
        db_type=body.db_type,
        connection_string_enc=body.connection_string,  # encrypted in production
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    return ConnectionResponse(
        id=str(conn.id),
        name=conn.name,
        db_type=conn.db_type,
        created_at=conn.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# GET /config/scan/{connection_id} — scan database schema
# ---------------------------------------------------------------------------
@router.get("/scan/{connection_id}", response_model=list[ScanResult])
async def scan_database(
    connection_id: str,
    current_user: User = Depends(require_data_owner),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Scan the INFORMATION_SCHEMA of a registered database connection.

    For the hackathon demo: scans the Neon DB for mock_ tables instead of
    connecting to an external database. In production, this would decrypt
    the connection string and connect to the external DB.
    """
    try:
        conn_uuid = uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid connection ID"
        )

    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_uuid)
    )
    conn = result.scalar_one_or_none()

    if not conn or conn.team_id != current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )

    # Scan our Neon DB for mock_ tables (hackathon demo)
    scan_result = await db.execute(
        text("""
            SELECT t.table_name,
                   (SELECT COUNT(*)
                    FROM information_schema.columns c
                    WHERE c.table_name = t.table_name
                      AND c.table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
              AND t.table_name LIKE 'mock_%'
            ORDER BY t.table_name
        """)
    )
    tables = [
        ScanResult(table_name=row[0], column_count=row[1])
        for row in scan_result.fetchall()
    ]

    return tables


# ---------------------------------------------------------------------------
# POST /config/tables — save a table to master_config
# ---------------------------------------------------------------------------
@router.post(
    "/tables",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_table_config(
    body: CreateTableRequest,
    current_user: User = Depends(require_data_owner),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Register a table in the master_config security boundary.
    Once registered, the AI pipeline can access this table for the owner's team.
    """
    try:
        conn_uuid = uuid.UUID(body.db_connection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid db_connection_id",
        )

    # Verify the connection belongs to the user's team
    conn_result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_uuid)
    )
    conn = conn_result.scalar_one_or_none()

    if not conn or conn.team_id != current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found for your team",
        )

    config = MasterConfig(
        db_connection_id=conn_uuid,
        team_id=current_user.team_id,
        table_name=body.table_name,
        semantic_definition=body.semantic_definition,
        columns_metadata=[col.model_dump() for col in body.columns_metadata],
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return TableResponse(
        id=str(config.id),
        table_name=config.table_name,
        semantic_definition=config.semantic_definition,
        columns_metadata=config.columns_metadata,
        is_active=config.is_active,
        created_at=config.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# GET /config/tables — list active master_config entries for the team
# ---------------------------------------------------------------------------
@router.get("/tables", response_model=list[TableResponse])
async def list_table_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return all active master_config entries for the authenticated user's team.
    """
    if not current_user.team_id:
        return []

    result = await db.execute(
        select(MasterConfig)
        .where(
            MasterConfig.team_id == current_user.team_id,
            MasterConfig.is_active == True,
        )
        .order_by(MasterConfig.table_name)
    )
    configs = result.scalars().all()

    return [
        TableResponse(
            id=str(c.id),
            table_name=c.table_name,
            semantic_definition=c.semantic_definition,
            columns_metadata=c.columns_metadata,
            is_active=c.is_active,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in configs
    ]


# ---------------------------------------------------------------------------
# PATCH /config/tables/{id} — update is_active or semantic_definition
# ---------------------------------------------------------------------------
@router.patch("/tables/{table_id}", response_model=TableResponse)
async def update_table_config(
    table_id: str,
    body: UpdateTableRequest,
    current_user: User = Depends(require_data_owner),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update a master_config entry's activation status or semantic definition.
    Only the owning team's Data Owner can modify their entries.
    """
    try:
        config_uuid = uuid.UUID(table_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid table config ID"
        )

    result = await db.execute(
        select(MasterConfig).where(MasterConfig.id == config_uuid)
    )
    config = result.scalar_one_or_none()

    if not config or config.team_id != current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table configuration not found",
        )

    if body.is_active is not None:
        config.is_active = body.is_active
    if body.semantic_definition is not None:
        config.semantic_definition = body.semantic_definition

    await db.commit()
    await db.refresh(config)

    return TableResponse(
        id=str(config.id),
        table_name=config.table_name,
        semantic_definition=config.semantic_definition,
        is_active=config.is_active,
    )
