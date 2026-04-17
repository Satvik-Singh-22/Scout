import os
import sys
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.db.session import get_sync_session
from sqlalchemy import text

def main():
    try:
        with get_sync_session() as session:
            result = session.execute(
                text("SELECT table_name, semantic_definition, columns_metadata FROM master_config WHERE is_active = TRUE")
            )
            rows = result.fetchall()
            
            output = []
            for row in rows:
                cols = row.columns_metadata
                if isinstance(cols, str):
                    try:
                        cols = json.loads(cols)
                    except:
                        pass
                
                output.append({
                    "table_name": row.table_name,
                    "description": row.semantic_definition,
                    "columns": cols
                })
                
            with open("schema_export.json", "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
                
            print(f"Successfully exported {len(output)} tables to schema_export.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
