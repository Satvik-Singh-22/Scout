"""
Scout — Full Schema Dump for LLM Testing
=========================================
Pulls two complementary views of the database:
  1. information_schema  – raw PostgreSQL table/column definitions
  2. master_config       – Scout's semantic overlay (descriptions, column metadata)

Outputs:
  - schema_full.json       (machine-readable, for structured LLM prompting)
  - schema_full_report.txt (human-readable text report)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ── resolve project root so imports work regardless of CWD ──────────────────
ROOT = Path(__file__).resolve().parent.parent.parent   # …/backend/scripts → …/src
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

import psycopg2
import psycopg2.extras

# ── connect using raw psycopg2 (no SQLAlchemy overhead) ─────────────────────
raw_url = os.getenv("DATABASE_URL", "")
# asyncpg URL → psycopg2 URL
raw_url = (
    raw_url.replace("postgresql+asyncpg://", "postgresql://")
           .replace("?ssl=require", "?sslmode=require")
           .replace("&ssl=require", "&sslmode=require")
)

print(f"Connecting to database…")
conn = psycopg2.connect(raw_url, cursor_factory=psycopg2.extras.RealDictCursor)
cur  = conn.cursor()

# ── 1. Pull every table in the 'public' schema ───────────────────────────────
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type   = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = [r["table_name"] for r in cur.fetchall()]
print(f"Found {len(tables)} tables: {tables}")

# ── 2. Pull column details for every table ───────────────────────────────────
cur.execute("""
    SELECT
        c.table_name,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.character_maximum_length,
        c.is_nullable,
        c.column_default,
        pgd.description AS column_comment
    FROM information_schema.columns c
    LEFT JOIN pg_catalog.pg_statio_all_tables st
           ON st.schemaname = c.table_schema
          AND st.relname    = c.table_name
    LEFT JOIN pg_catalog.pg_description pgd
           ON pgd.objoid   = st.relid
          AND pgd.objsubid = c.ordinal_position
    WHERE c.table_schema = 'public'
    ORDER BY c.table_name, c.ordinal_position;
""")
raw_cols = cur.fetchall()

# ── 3. Pull primary keys ─────────────────────────────────────────────────────
cur.execute("""
    SELECT
        tc.table_name,
        kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema    = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema    = 'public'
    ORDER BY tc.table_name, kcu.ordinal_position;
""")
pk_rows = cur.fetchall()
pks: dict[str, list[str]] = {}
for row in pk_rows:
    pks.setdefault(row["table_name"], []).append(row["column_name"])

# ── 4. Pull foreign keys ─────────────────────────────────────────────────────
cur.execute("""
    SELECT
        tc.table_name            AS from_table,
        kcu.column_name          AS from_col,
        ccu.table_name           AS to_table,
        ccu.column_name          AS to_col
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema    = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
     AND ccu.table_schema    = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema    = 'public'
    ORDER BY tc.table_name;
""")
fk_rows = cur.fetchall()
fks: dict[str, list[dict]] = {}
for row in fk_rows:
    fks.setdefault(row["from_table"], []).append({
        "column": row["from_col"],
        "references": f"{row['to_table']}({row['to_col']})"
    })

# ── 5. Pull check constraints ────────────────────────────────────────────────
cur.execute("""
    SELECT
        tc.table_name,
        cc.check_clause
    FROM information_schema.table_constraints tc
    JOIN information_schema.check_constraints cc
      ON tc.constraint_name = cc.constraint_name
     AND tc.constraint_schema = cc.constraint_schema
    WHERE tc.constraint_type = 'CHECK'
      AND tc.table_schema    = 'public'
      AND cc.check_clause NOT LIKE '%IS NOT NULL%'
    ORDER BY tc.table_name;
""")
chk_rows = cur.fetchall()
checks: dict[str, list[str]] = {}
for row in chk_rows:
    checks.setdefault(row["table_name"], []).append(row["check_clause"])

# ── 6. Pull row counts ───────────────────────────────────────────────────────
row_counts: dict[str, int] = {}
for tbl in tables:
    cur.execute(f'SELECT COUNT(*) AS cnt FROM "{tbl}";')
    row_counts[tbl] = cur.fetchone()["cnt"]

# ── 7. Pull master_config semantic overlay ───────────────────────────────────
cur.execute("""
    SELECT
        mc.table_name,
        mc.semantic_definition,
        mc.columns_metadata,
        mc.is_active,
        t.name AS team_name,
        dc.name AS db_connection_name,
        dc.db_type
    FROM master_config mc
    LEFT JOIN teams t  ON t.id  = mc.team_id
    LEFT JOIN database_connections dc ON dc.id = mc.db_connection_id
    ORDER BY mc.table_name;
""")
mc_rows = cur.fetchall()

master_config_map: dict[str, dict] = {}
for row in mc_rows:
    cols_meta = row["columns_metadata"]
    if isinstance(cols_meta, str):
        try:
            cols_meta = json.loads(cols_meta)
        except Exception:
            pass
    master_config_map[row["table_name"]] = {
        "semantic_definition": row["semantic_definition"],
        "columns_metadata":    cols_meta,
        "is_active":           row["is_active"],
        "team":                row["team_name"],
        "db_connection":       row["db_connection_name"],
        "db_type":             row["db_type"],
    }

cur.close()
conn.close()

# ── 8. Assemble the unified schema dict ──────────────────────────────────────
# Group columns by table
cols_by_table: dict[str, list[dict]] = {}
for col in raw_cols:
    tbl = col["table_name"]
    cols_by_table.setdefault(tbl, []).append({
        "name":               col["column_name"],
        "position":           col["ordinal_position"],
        "type":               col["data_type"],
        "max_length":         col["character_maximum_length"],
        "nullable":           col["is_nullable"] == "YES",
        "default":            col["column_default"],
        "comment":            col["column_comment"],
        "is_primary_key":     col["column_name"] in pks.get(tbl, []),
    })

schema: list[dict] = []
for tbl in tables:
    entry = {
        "table_name":    tbl,
        "row_count":     row_counts.get(tbl, 0),
        "primary_keys":  pks.get(tbl, []),
        "foreign_keys":  fks.get(tbl, []),
        "check_constraints": checks.get(tbl, []),
        "columns":       cols_by_table.get(tbl, []),
        "scout_semantic": master_config_map.get(tbl),   # None if not in master_config
    }
    schema.append(entry)

# ── 9. Write JSON ─────────────────────────────────────────────────────────────
out_dir   = Path(__file__).resolve().parent.parent
json_path = out_dir / "schema_full.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2, default=str)
print(f"✓ JSON written → {json_path}")

# ── 10. Write human-readable text report ─────────────────────────────────────
txt_path = out_dir / "schema_full_report.txt"
lines = []
lines.append("=" * 80)
lines.append("SCOUT DATABASE — FULL SCHEMA REPORT")
lines.append(f"Generated : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
lines.append(f"Tables    : {len(schema)}")
lines.append("=" * 80)

for entry in schema:
    tbl = entry["table_name"]
    lines.append("")
    lines.append(f"┌─ TABLE: {tbl}  (rows ≈ {entry['row_count']:,})")

    sem = entry.get("scout_semantic")
    if sem:
        lines.append(f"│  Scout Description : {sem['semantic_definition']}")
        lines.append(f"│  Team              : {sem['team']}  |  DB: {sem['db_connection']} ({sem['db_type']})")
        lines.append(f"│  Active in Scout   : {sem['is_active']}")

    if entry["primary_keys"]:
        lines.append(f"│  Primary Key(s)    : {', '.join(entry['primary_keys'])}")

    if entry["foreign_keys"]:
        for fk in entry["foreign_keys"]:
            lines.append(f"│  FK                : {fk['column']}  →  {fk['references']}")

    if entry["check_constraints"]:
        for ck in entry["check_constraints"]:
            lines.append(f"│  CHECK             : {ck}")

    lines.append("│")
    lines.append("│  COLUMNS")
    lines.append("│  " + "-" * 70)
    for col in entry["columns"]:
        pk_marker  = " [PK]" if col["is_primary_key"] else ""
        null_marker = " NOT NULL" if not col["nullable"] else ""
        type_str   = col["type"]
        if col["max_length"]:
            type_str += f"({col['max_length']})"
        default_str = f"  DEFAULT {col['default']}" if col["default"] else ""
        lines.append(f"│    {col['position']:2}. {col['name']:<35} {type_str:<30}{pk_marker}{null_marker}{default_str}")
        if col["comment"]:
            lines.append(f"│        ↳ {col['comment']}")

    # Scout column-level metadata
    if sem and isinstance(sem.get("columns_metadata"), list):
        lines.append("│")
        lines.append("│  SCOUT COLUMN METADATA (from master_config)")
        lines.append("│  " + "-" * 70)
        for cm in sem["columns_metadata"]:
            if isinstance(cm, dict):
                cname = cm.get("name", cm.get("column_name", "?"))
                cdesc = cm.get("description", cm.get("semantic_definition", ""))
                ctype = cm.get("type", cm.get("data_type", ""))
                lines.append(f"│    {cname:<35} [{ctype}]  {cdesc}")

    lines.append("└" + "─" * 75)

with open(txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"✓ Text report  → {txt_path}")
print("\nDone. Feed schema_full_report.txt to your LLM of choice.")
