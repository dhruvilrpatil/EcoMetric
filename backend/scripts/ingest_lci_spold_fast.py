"""
backend/scripts/ingest_lci_spold_fast.py

High-performance streaming indexer for 26,533 Ecoinvent 3.12 LCI ecoSpold2 files into AWS RDS PostgreSQL.
"""

import sys
import os
import json
import time
from pathlib import Path
from glob import glob
from concurrent.futures import ThreadPoolExecutor
from lxml import etree
import psycopg2
from psycopg2.extras import execute_batch

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

NS = {'es': 'http://www.EcoInvent.org/EcoSpold02'}

def parse_single_lci_file(xml_file_path: str) -> dict | None:
    """Parse a single raw ecoSpold2 LCI dataset file."""
    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()

        dataset = root.find('.//es:activityDescription', NS)
        if dataset is None:
            return None

        # Activity Name
        activity_name = "Unknown"
        for elem in dataset.findall('.//es:activity/es:activityName', NS):
            if elem.text:
                activity_name = elem.text.strip()
                break
        if activity_name == "Unknown":
            elem = dataset.find('.//es:activityName', NS)
            if elem is not None and elem.text:
                activity_name = elem.text.strip()

        # Geography
        geo_elem = dataset.find('.//es:geography/es:shortname', NS)
        geography = geo_elem.text.strip() if (geo_elem is not None and geo_elem.text) else "GLO"

        # Reference Year
        reference_year = 2023
        tp = dataset.find('.//es:timePeriod', NS)
        if tp is not None:
            start = tp.get('startDate') or tp.get('startYear', '')
            if start:
                try:
                    reference_year = int(start[:4])
                except ValueError:
                    pass

        # Elementary Exchanges
        elementary_exchanges: dict = {}
        for ex in root.findall('.//es:elementaryExchange', NS):
            name_elem = ex.find('es:name', NS)
            if name_elem is None or not name_elem.text:
                continue
            ex_name = name_elem.text.strip()
            amount_str = ex.get('amount', '0')
            try:
                amount = float(amount_str)
            except (ValueError, TypeError):
                amount = 0.0

            unit_elem = ex.find('es:unitName', NS)
            unit = unit_elem.text.strip() if (unit_elem is not None and unit_elem.text) else "kg"
            elementary_exchanges[ex_name] = {"amount": amount, "unit": unit}

        # Intermediate Exchanges
        intermediate_exchanges: dict = {}
        for ex in root.findall('.//es:intermediateExchange', NS):
            name_elem = ex.find('es:name', NS)
            if name_elem is None or not name_elem.text:
                continue
            ex_name = name_elem.text.strip()
            amount_str = ex.get('amount', '0')
            try:
                amount = float(amount_str)
            except (ValueError, TypeError):
                amount = 0.0
            intermediate_exchanges[ex_name] = amount

        filename = Path(xml_file_path).name
        doc_id = filename.replace('.spold', '')

        return {
            "id": doc_id,
            "activity_name": activity_name,
            "geography": geography,
            "reference_year": reference_year,
            "data_quality_score": 3,
            "xml_file": filename,
            "elementary_exchanges": json.dumps(elementary_exchanges),
            "intermediate_exchanges": json.dumps(intermediate_exchanges),
        }
    except Exception as e:
        return None

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"D:\db\ecoinvent 3.12_cutoff_lci_ecoSpold02\datasets"
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("[ERROR] DATABASE_URL missing from environment or backend/.env")
        sys.exit(1)

    xml_files = glob(os.path.join(target_dir, "*.spold"))
    total = len(xml_files)
    print(f"[INFO] Found {total} ecoSpold2 LCI dataset files in {target_dir}")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    insert_sql = """
    INSERT INTO lci_database (
        id, activity_name, geography, reference_year, data_quality_score,
        xml_file, elementary_exchanges, intermediate_exchanges
    ) VALUES (
        %(id)s, %(activity_name)s, %(geography)s, %(reference_year)s, %(data_quality_score)s,
        %(xml_file)s, %(elementary_exchanges)s::jsonb, %(intermediate_exchanges)s::jsonb
    )
    ON CONFLICT (id) DO UPDATE SET
        activity_name = EXCLUDED.activity_name,
        geography = EXCLUDED.geography,
        elementary_exchanges = EXCLUDED.elementary_exchanges,
        intermediate_exchanges = EXCLUDED.intermediate_exchanges;
    """

    batch_size = 500
    batch = []
    processed = 0

    t0 = time.time()
    workers = 32
    print(f"[INFO] Streaming parse & ingest using {workers} threads...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(parse_single_lci_file, xml_files, chunksize=50):
            if result:
                batch.append(result)
                processed += 1
                
                if len(batch) >= batch_size:
                    execute_batch(cursor, insert_sql, batch, page_size=batch_size)
                    conn.commit()
                    print(f"  [DB] Ingested {processed}/{total} rows into AWS RDS (Elapsed: {time.time() - t0:.1f}s)...")
                    batch = []

    if batch:
        execute_batch(cursor, insert_sql, batch, page_size=batch_size)
        conn.commit()
        print(f"  [DB] Final batch committed. Total: {processed}/{total}")

    cursor.close()
    conn.close()
    print(f"[DONE] Ingested {processed} unit process datasets into AWS RDS PostgreSQL in {time.time() - t0:.1f}s total!")

if __name__ == "__main__":
    main()
