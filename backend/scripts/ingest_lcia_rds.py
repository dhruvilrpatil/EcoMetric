"""
backend/scripts/ingest_lcia_rds.py

Parses ecoinvent 3.12 LCIA Implementation Excel workbook (LCIA Implementation 3.12.xlsx)
and populates characterization factors into AWS RDS PostgreSQL / local PostgreSQL database.

Usage:
    python backend/scripts/ingest_lcia_rds.py "D:\\db\\ecoinvent 3.12_LCIA_implementation\\LCIA Implementation 3.12.xlsx"
"""

import sys
import os
import time
from pathlib import Path
import pandas as pd

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass


def create_lcia_table_if_not_exists(conn):
    """Ensure the lcia_factors table and indexes exist."""
    create_sql = """
    DROP TABLE IF EXISTS lcia_factors;
    CREATE TABLE lcia_factors (
        id                      SERIAL PRIMARY KEY,
        method                  VARCHAR(256) NOT NULL,
        category                VARCHAR(256),
        indicator               VARCHAR(256) NOT NULL,
        flow_name               TEXT NOT NULL,
        compartment             VARCHAR(100),
        subcompartment          VARCHAR(100),
        unit                    VARCHAR(50),
        characterization_factor DOUBLE PRECISION NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_lcia_method ON lcia_factors (method);
    CREATE INDEX IF NOT EXISTS idx_lcia_flow ON lcia_factors (flow_name);
    CREATE INDEX IF NOT EXISTS idx_lcia_method_flow ON lcia_factors (method, flow_name);
    """
    with conn.cursor() as cur:
        cur.execute(create_sql)
    conn.commit()



def ingest_lcia(excel_path: str, db_url: str, batch_size: int = 10000):
    """Reads LCIA Implementation Excel file and loads CFs into PostgreSQL."""
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("❌ Error: psycopg2 is required. Run: pip install psycopg2-binary")
        return

    excel_p = Path(excel_path).resolve()
    if not excel_p.exists():
        print(f"❌ Error: Excel file not found at '{excel_path}'")
        return

    print(f"📖 Reading 'Indicators' sheet from {excel_p.name}...")
    df_ind = pd.read_excel(excel_p, sheet_name="Indicators")
    units_map = {}
    for _, row in df_ind.iterrows():
        key = (str(row.get("Method", "")).strip(), str(row.get("Category", "")).strip(), str(row.get("Indicator", "")).strip())
        units_map[key] = str(row.get("Indicator Unit", "")).strip()

    print(f"📖 Reading 'CFs' sheet from {excel_p.name} (this may take 15-30s)...")
    start_time = time.time()
    df_cfs = pd.read_excel(excel_p, sheet_name="CFs")
    elapsed = time.time() - start_time
    print(f"✅ Loaded {len(df_cfs):,} rows in {elapsed:.2f} seconds.")

    print("🔌 Connecting to PostgreSQL database...")
    conn = psycopg2.connect(db_url)
    create_lcia_table_if_not_exists(conn)

    print("Clearing existing lcia_factors table records for fresh ingestion...")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE lcia_factors RESTART IDENTITY;")
    conn.commit()

    insert_sql = """
    INSERT INTO lcia_factors (
        method, category, indicator, flow_name, compartment, subcompartment, unit, characterization_factor
    ) VALUES (
        %(method)s, %(category)s, %(indicator)s, %(flow_name)s, %(compartment)s, %(subcompartment)s, %(unit)s, %(cf)s
    );
    """

    print("Processing and preparing records for batch insertion...")
    records = []
    total = len(df_cfs)
    count = 0

    cursor = conn.cursor()

    for idx, row in df_cfs.iterrows():
        method = str(row.get("Method", "")).strip()
        category = str(row.get("Category", "")).strip() if pd.notna(row.get("Category")) else ""
        indicator = str(row.get("Indicator", "")).strip()
        flow_name = str(row.get("Name", "")).strip()
        compartment = str(row.get("Compartment", "")).strip() if pd.notna(row.get("Compartment")) else ""
        subcompartment = str(row.get("Subcompartment", "")).strip() if pd.notna(row.get("Subcompartment")) else ""
        
        try:
            cf_val = float(row.get("CF", 0.0))
        except (ValueError, TypeError):
            cf_val = 0.0

        unit = units_map.get((method, category, indicator), "")

        records.append({
            "method": method,
            "category": category,
            "indicator": indicator,
            "flow_name": flow_name,
            "compartment": compartment,
            "subcompartment": subcompartment,
            "unit": unit,
            "cf": cf_val
        })
        count += 1

        if len(records) >= batch_size:
            execute_batch(cursor, insert_sql, records, page_size=batch_size)
            conn.commit()
            print(f"  [OK] Ingested {count:,} / {total:,} characterization factors...")
            records = []

    if records:
        execute_batch(cursor, insert_sql, records, page_size=batch_size)
        conn.commit()
        print(f"  [OK] Final batch committed. Total ingested: {count:,} / {total:,}")

    cursor.close()
    conn.close()
    print("🎉 Ingestion of LCIA Characterization Factors completed successfully!")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL is missing in environment.")
        sys.exit(1)

    target_file = sys.argv[1] if len(sys.argv) > 1 else r"D:\db\ecoinvent 3.12_LCIA_implementation\LCIA Implementation 3.12.xlsx"
    ingest_lcia(target_file, db_url)
