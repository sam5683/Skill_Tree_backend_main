"""
Diagnostic and cleanup script for Alembic revision state in Supabase.
This script:
1. Connects to Supabase database
2. Checks alembic_version table content
3. Removes orphaned revisions safely
4. Verifies clean state
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

print("=" * 70)
print("ALEMBIC REVISION STATE DIAGNOSTIC & CLEANUP")
print("=" * 70)

try:
    # Connect to database
    print("\n[1/5] Connecting to Supabase PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        print("✅ Connected successfully")
        
        # Check if alembic_version table exists
        print("\n[2/5] Checking if alembic_version table exists...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "alembic_version" not in tables:
            print("⚠️  alembic_version table does NOT exist (will be created on first migration)")
            print(f"    Existing tables: {tables}")
        else:
            print("✅ alembic_version table exists")
            
            # Query current revisions
            print("\n[3/5] Checking current revision state in database...")
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            rows = result.fetchall()
            
            if not rows:
                print("✅ alembic_version table is EMPTY (clean state)")
            else:
                print(f"⚠️  Found {len(rows)} revision(s) in alembic_version:")
                orphaned_revisions = []
                for row in rows:
                    revision = row[0]
                    print(f"   - {revision}")
                    if revision == "cdd0c5902d73":
                        orphaned_revisions.append(revision)
                
                if orphaned_revisions:
                    print(f"\n[4/5] FOUND ORPHANED REVISION(S): {orphaned_revisions}")
                    print("      These migration files no longer exist in alembic/versions/")
                    
                    # Remove orphaned revisions
                    print("\n      Removing orphaned revisions...")
                    for orphan in orphaned_revisions:
                        connection.execute(
                            text("DELETE FROM alembic_version WHERE version_num = :revision"),
                            {"revision": orphan}
                        )
                        print(f"      ✅ Deleted: {orphan}")
                    
                    # Commit the transaction
                    connection.commit()
                    print("\n      ✅ Changes committed to database")
                else:
                    print("\n[4/5] No orphaned revisions found")
            
            # Final verification
            print("\n[5/5] Final verification - checking clean state...")
            result = connection.execute(text("SELECT COUNT(*) FROM alembic_version;"))
            count = result.scalar()
            print(f"✅ alembic_version table now has {count} rows")
            
            if count == 0:
                print("\n" + "=" * 70)
                print("✅ DATABASE STATE IS CLEAN - Ready for migration")
                print("=" * 70)
                print("\nNext steps:")
                print("1. Run: alembic revision --autogenerate -m 'initial_schema'")
                print("2. Review the generated migration file")
                print("3. Run: alembic upgrade head")
                print("4. Verify tables were created")
            else:
                print("\n" + "=" * 70)
                print("⚠️  DATABASE STILL HAS REVISIONS")
                print("=" * 70)
                print("This is normal if you had previous successful migrations.")
                print("Alembic will use these as the baseline.")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    sys.exit(1)

print("\nScript completed.\n")
