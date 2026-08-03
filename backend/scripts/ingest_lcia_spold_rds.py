"""
backend/scripts/ingest_lcia_spold_rds.py

Parses 26,533 pre-calculated LCIA ecoSpold2 XML files (from ecoinvent 3.12_cutoff_lcia_ecoSpold02)
and updates the AWS RDS / PostgreSQL lci_database table with official pre-calculated GWP factors and LCIA indicator results.

Usage:
    python backend/scripts/ingest_lcia_spold_rds.py "D:\\db\\ecoinvent 3.12_cutoff_lcia_ecoSpold02\\datasets"
"""

import sys
import os
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from lxml import etree

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

NS = {'es': 'http://www.EcoInvent.org/EcoSpold02'}


def ensure_lci_lcia_columns(conn):
    """Add gwp_factor and lcia_results columns to lci_database if missing."""
    sql = """
    ALTER TABLE lci_database ADD COLUMN IF NOT EXISTS gwp_factor DOUBLE PRECISION;
    ALTER TABLE lci_database ADD COLUMN IF NOT EXISTS lcia_results JSONB;
    CREATE INDEX IF NOT EXISTS idx_lci_gwp ON lci_database (gwp_factor);
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def parse_lcia_spold_file(file_path: str) -> dict | None:
    """Parse one LCIA .spold XML file to extract pre-calculated GWP and LCIA indicators."""
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        flowData = root[0].find('.//es:flowData', NS)
        if flowData is None:
            return None

        gwp_factor = None
        lcia_indicators = {}

        for ii in flowData.findall('.//es:impactIndicator', NS):
            amount_str = ii.get('amount')
            if not amount_str:
                continue
            try:
                val = float(amount_str)
            except (ValueError, TypeError):
                continue

            method_elem = ii.find('es:impactMethodName', NS)
            method = method_elem.text.strip() if (method_elem is not None and method_elem.text) else ""
            
            cat_elem = ii.find('es:impactCategoryName', NS)
            category = cat_elem.text.strip() if (cat_elem is not None and cat_elem.text) else ""

            name_elem = ii.find('es:name', NS)
            indicator_name = name_elem.text.strip() if (name_elem is not None and name_elem.text) else ""

            unit_elem = ii.find('es:unitName', NS)
            unit = unit_elem.text.strip() if (unit_elem is not None and unit_elem.text) else ""

            # Standardize key for storage
            key = f"{method} | {category} | {indicator_name}"
            lcia_indicators[key] = {"value": val, "unit": unit}

            # Check for GWP100 under EF, IPCC, CML, TRACI, ReCiPe
            if gwp_factor is None:
                m_low = method.lower()
                cat_low = category.lower()
                ind_low = indicator_name.lower()
                if "ef" in m_low or "ipcc" in m_low or "cml" in m_low or "traci" in m_low or "recipe" in m_low or "en15804" in m_low:
                    if "climate change: total" in cat_low or "climate change" in cat_low or "global warming" in ind_low or "gwp" in ind_low:
                        gwp_factor = val


        filename = Path(file_path).name
        # Activity ID is the first part before underscore
        activity_id = filename.split('_')[0] if '_' in filename else filename.replace('.spold', '')

        return {
            "id": activity_id,
            "filename": filename,
            "gwp_factor": gwp_factor,
            "lcia_results": lcia_indicators
        }
    except Exception:
        return None


def ingest_all_lcia_spold(datasets_dir: str, batch_size: int = 1000):
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("❌ psycopg2-binary is required.")
        return

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL is missing.")
        return

    p = Path(datasets_dir).resolve()
    if not p.exists():
        print(f"❌ Path not found: {datasets_dir}")
        return

    spold_files = list(p.glob("*.spold"))
    total_files = len(spold_files)
    print(f"📦 Found {total_files:,} LCIA .spold XML files in {p}")

    print("🔌 Connecting to PostgreSQL...")
    conn = psycopg2.connect(db_url)
    ensure_lci_lcia_columns(conn)

    update_sql = """
    UPDATE lci_database
    SET gwp_factor = COALESCE(%(gwp_factor)s, gwp_factor),
        lcia_results = %(lcia_results)s
    WHERE id = %(id)s OR xml_file = %(filename)s;
    """

    num_workers = min(16, (os.cpu_count() or 4) * 2)
    print(f"⚡ Parsing XML files with {num_workers} parallel workers...")
    
    start_time = time.time()
    records = []
    processed = 0
    cur = conn.cursor()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(parse_lcia_spold_file, str(f)) for f in spold_files]
        for future in as_completed(futures):
            res = future.result()
            if res:
                records.append({
                    "id": res["id"],
                    "filename": res["filename"],
                    "gwp_factor": res["gwp_factor"],
                    "lcia_results": json.dumps(res["lcia_results"])
                })
            processed += 1

            if len(records) >= batch_size:
                execute_batch(cur, update_sql, records, page_size=batch_size)
                conn.commit()
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"  [OK] Processed {processed:,} / {total_files:,} ({rate:.0f} files/sec)...")
                records = []

    if records:
        execute_batch(cur, update_sql, records, page_size=batch_size)
        conn.commit()

    cur.close()
    conn.close()
    total_time = time.time() - start_time
    print(f"🎉 Fully updated {processed:,} LCIA dataset records in {total_time:.2f} seconds!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\db\ecoinvent 3.12_cutoff_lcia_ecoSpold02\datasets"
    ingest_all_lcia_spold(target)
