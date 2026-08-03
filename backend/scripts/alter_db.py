import os
import sys
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except:
    pass

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL")
    sys.exit(1)

conn = psycopg2.connect(db_url)
conn.autocommit = True
cursor = conn.cursor()

alter_cmds = [
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS company_description TEXT;",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS product_narrative TEXT;",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS csi_division_code VARCHAR(100);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS certifications TEXT[];",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pcr_reviewer_names TEXT[];",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS lca_conductor_name VARCHAR(256);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS verifier_name VARCHAR(256);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS verifier_email VARCHAR(256);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS program_operator_name VARCHAR(256);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS program_operator_address TEXT;",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS program_operator_website VARCHAR(256);",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS program_operator_logo_url VARCHAR(512);"
]

for cmd in alter_cmds:
    try:
        cursor.execute(cmd)
        print("Success:", cmd)
    except Exception as e:
        print("Failed:", cmd, "Error:", e)

cursor.close()
conn.close()
