"""
backend/scripts/init_db.py

Initializes the AWS RDS PostgreSQL database schema without requiring psql CLI.
Reads DATABASE_URL from environment or command line argument and applies schema_v312.sql.

Usage:
    python backend/scripts/init_db.py
    python backend/scripts/init_db.py "postgresql://postgres:password@ecometric-db.xxx.rds.amazonaws.com:5432/ecometric"
"""

import sys
import os
from pathlib import Path

# Ensure stdout can print UTF-8 characters on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


# Try loading dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

try:
    import psycopg2
except ImportError:
    print("❌ Error: psycopg2-binary is required. Run: pip install psycopg2-binary")
    sys.exit(1)


def init_database():
    db_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DATABASE_URL")
    
    if not db_url or "your-rds-endpoint" in db_url:
        print("❌ Error: DATABASE_URL is missing or invalid.")
        print("   Set DATABASE_URL in backend/.env or pass it as an argument:")
        print("   python backend/scripts/init_db.py \"postgresql://postgres:password@host:5432/postgres\"")
        sys.exit(1)

    schema_file = Path(__file__).parent / "schema_v312.sql"
    if not schema_file.exists():
        print(f"❌ Error: Schema file not found at {schema_file}")
        sys.exit(1)

    print("Connecting to PostgreSQL database...")
    
    try:
        # Connect to target database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print(f"Reading schema from {schema_file.name}...")
        with open(schema_file, "r", encoding="utf-8") as f:
            sql_script = f.read()

        print("Executing schema initialization script...")
        cursor.execute(sql_script)
        
        print("Database schema initialized successfully! All tables, indexes, and extensions created.")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database Initialization Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
