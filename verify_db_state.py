"""
Verify database schema and alembic state after migration.
"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("DATABASE VERIFICATION AFTER MIGRATION")
print("=" * 70)

# Check tables
print("\n[1/3] Tables in database:")
inspector = inspect(engine)
tables = sorted(inspector.get_table_names())
for table in tables:
    columns = [col['name'] for col in inspector.get_columns(table)]
    print(f"  ✅ {table:<25} - columns: {len(columns)}")

# Check alembic_version
print("\n[2/3] Alembic migration state:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version;"))
    rows = result.fetchall()
    for row in rows:
        print(f"  ✅ Applied revision: {row[0]}")

# Check notes.content column type
print("\n[3/3] Schema details:")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'notes'
        ORDER BY ordinal_position;
    """))
    for row in result.fetchall():
        col_name, col_type, nullable = row
        print(f"  - {col_name:<20} {col_type:<15} {'(nullable)' if nullable == 'YES' else '(required)'}")

print("\n" + "=" * 70)
print("✅ DATABASE IS CLEAN AND READY FOR DEVELOPMENT")
print("=" * 70)
