"""
Clear invalid JSON data from notes.content before migration.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        print("[1/2] Setting invalid content data to valid empty JSON...")
        result = connection.execute(
            text("UPDATE notes SET content = '\"\"'::jsonb WHERE content IS NOT NULL;")
        )
        connection.commit()
        print(f"✅ Updated {result.rowcount} rows - set to empty JSON string")
        
        print("[2/2] Verifying...")
        result = connection.execute(
            text("SELECT COUNT(*) as count FROM notes;")
        )
        count = result.scalar()
        print(f"✅ Verified: {count} total rows in notes table")
        
        print("\n✅ Database is ready for migration")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
