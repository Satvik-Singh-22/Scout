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
seed_pinecone.py — One-time Pinecone Index Seeder

ELI5 (What does this file do?):
Instead of cramming every table's description into every AI prompt (which is slow and wasteful),
we first store all the descriptions in a super-fast searchable "library" called Pinecone.
This script builds that library once. After that, the AI can search for only the 3-5 relevant
table descriptions it actually needs — cutting context by ~90%.

Run once:
    python -m backend.scripts.seed_pinecone
    # or directly:
    cd src && python backend/scripts/seed_pinecone.py

This script is idempotent — running it twice will NOT corrupt data.
Pinecone upserts are naturally idempotent by vector ID.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so `backend.*` imports work when
# this script is executed directly (not via `python -m`).
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # src/
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables — same mechanism as the rest of the project
from dotenv import load_dotenv
load_dotenv(override=True)

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # Upsert in batches of 50 — Pinecone recommended pattern


def main():
    # ──────────────────────────────────────────────────────────────────────
    # Step 1: Load Pinecone credentials from environment
    # ──────────────────────────────────────────────────────────────────────
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "").strip()
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "").strip()

    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)
    if not pinecone_index_name:
        logger.error("PINECONE_INDEX_NAME is not set. Add it to your .env file.")
        sys.exit(1)

    # ──────────────────────────────────────────────────────────────────────
    # Step 2: Connect to the database using the existing project pattern
    # ──────────────────────────────────────────────────────────────────────
    try:
        from backend.db.session import get_sync_session
        from sqlalchemy import text
    except ImportError as e:
        logger.error("Failed to import DB session: %s", e)
        sys.exit(1)

    # ──────────────────────────────────────────────────────────────────────
    # Step 3: Fetch all rows from master_config that have a semantic_definition
    # Columns read from the actual MasterConfig model:
    #   - table_name (String, unique identifier per team)
    #   - semantic_definition (Text, the searchable description)
    #   - team_id (UUID, stored as metadata for access control during retrieval)
    # ──────────────────────────────────────────────────────────────────────
    rows = []
    try:
        with get_sync_session() as session:
            result = session.execute(
                text(
                    "SELECT table_name, semantic_definition, CAST(team_id AS TEXT) AS team_id "
                    "FROM master_config "
                    "WHERE semantic_definition IS NOT NULL "
                    "  AND semantic_definition != '' "
                    "  AND is_active = TRUE"
                )
            )
            rows = result.fetchall()
    except Exception as db_exc:
        logger.error("Database error while fetching master_config rows: %s", db_exc)
        sys.exit(1)

    if not rows:
        logger.warning("No active rows with semantic_definition found in master_config. Exiting.")
        sys.exit(0)

    logger.info("Fetched %d rows from master_config.", len(rows))

    # ──────────────────────────────────────────────────────────────────────
    # Step 4: Load the sentence-transformers model ONCE before the loop
    # Using 'all-MiniLM-L6-v2' — fast, lightweight, 384-dim embeddings
    # ──────────────────────────────────────────────────────────────────────
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("sentence-transformers is not installed. Run: pip install sentence-transformers")
        sys.exit(1)

    logger.info("Loading sentence-transformers model 'all-MiniLM-L6-v2'...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Model loaded.")

    # ──────────────────────────────────────────────────────────────────────
    # Step 5: Initialize the Pinecone client
    # ──────────────────────────────────────────────────────────────────────
    try:
        from pinecone import Pinecone
    except ImportError:
        logger.error("pinecone-client is not installed. Run: pip install pinecone-client>=3.0.0")
        sys.exit(1)

    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_index_name)
        logger.info("Connected to Pinecone index '%s'.", pinecone_index_name)
    except Exception as pc_exc:
        logger.error("Pinecone connection error: %s", pc_exc)
        sys.exit(1)

    # ──────────────────────────────────────────────────────────────────────
    # Step 6: Build vectors and upsert in batches of 50
    # ──────────────────────────────────────────────────────────────────────
    total_upserted = 0
    batch = []

    try:
        for row in rows:
            table_name = row.table_name
            semantic_def = row.semantic_definition
            team_id_str = row.team_id  # already cast to TEXT in SQL

            # Generate embedding from the semantic definition text
            embedding = embed_model.encode(semantic_def, convert_to_numpy=True).tolist()

            # Construct the Pinecone vector record
            vector = {
                "id": table_name,  # table_name is unique within a team; use as ID
                "values": embedding,
                "metadata": {
                    "table_name": table_name,
                    "semantic_definition": semantic_def,
                    "team_id": team_id_str,
                },
            }
            batch.append(vector)

            # Flush when we hit BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                index.upsert(vectors=batch)
                total_upserted += len(batch)
                logger.info("Upserted batch of %d vectors (total so far: %d).", len(batch), total_upserted)
                batch = []

        # Flush any remaining vectors
        if batch:
            index.upsert(vectors=batch)
            total_upserted += len(batch)
            logger.info("Upserted final batch of %d vectors.", len(batch))

    except Exception as pc_exc:
        logger.error("Pinecone upsert error: %s", pc_exc)
        sys.exit(1)

    logger.info(
        "✅ Seeding complete. %d vectors upserted to Pinecone index '%s'.",
        total_upserted,
        pinecone_index_name,
    )


if __name__ == "__main__":
    main()
