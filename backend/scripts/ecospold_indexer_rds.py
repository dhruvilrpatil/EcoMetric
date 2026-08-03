"""
backend/scripts/ecospold_indexer_rds.py

Batch parses 18,000+ Ecoinvent 3.12 ecoSpold2 XML files and populates AWS RDS PostgreSQL.

Usage:
    python backend/scripts/ecospold_indexer_rds.py "D:\\db\\ecoinvent 3.12_cutoff_ecoSpold02\\datasets"
"""

import sys
import os
import json
import uuid
from pathlib import Path
from lxml import etree

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Load .env for local dev so DATABASE_URL is available
try:
    from dotenv import load_dotenv
    load_dotenv(backend_dir / ".env")
except ImportError:
    pass

# Ecoinvent 3.12 ecoSpold2 namespace (note capital E and I)
NS = {'es': 'http://www.EcoInvent.org/EcoSpold02'}

# GWP100 AR6 characterization factors (IPCC 2021)
GWP_FACTORS = {
    "carbon dioxide": 1.0,
    "co2": 1.0,
    "methane": 29.8,
    "ch4": 29.8,
    "dinitrogen monoxide": 273.0,
    "nitrous oxide": 273.0,
    "n2o": 273.0,
}


def parse_single_dataset(xml_file_path: str) -> dict | None:
    """Parse one ecoSpold2 XML file into structured dict for RDS insertion."""
    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()

        # The dataset is wrapped in either <activityDataset> or <childActivityDataset>
        dataset = root.find('.//es:activityDescription', NS)
        if dataset is None:
            return None

        # ── Activity name (child element text, lang=en preferred) ──
        activity_name = "Unknown"
        for elem in dataset.findall('.//es:activity/es:activityName', NS):
            if elem.text:
                activity_name = elem.text.strip()
                break
        # fallback: any activityName element
        if activity_name == "Unknown":
            elem = dataset.find('.//es:activityName', NS)
            if elem is not None and elem.text:
                activity_name = elem.text.strip()

        # ── Geography ──
        geo_elem = dataset.find('.//es:geography/es:shortname', NS)
        geography = geo_elem.text.strip() if (geo_elem is not None and geo_elem.text) else "GLO"

        # ── Reference year (from timePeriod attributes) ──
        reference_year = 2023
        tp = dataset.find('.//es:timePeriod', NS)
        if tp is not None:
            start = tp.get('startDate') or tp.get('startYear', '')
            if start:
                try:
                    reference_year = int(start[:4])
                except ValueError:
                    pass

        # ── Elementary exchanges (amount is an XML attribute, not element) ──
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

        # ── Intermediate exchanges ──
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

        # ── Build stable ID from activity UUID in filename ──
        filename = Path(xml_file_path).name
        # Ecoinvent filenames are: <activity-uuid>_<product-uuid>.spold
        parts = filename.replace('.spold', '').split('_')
        doc_id = parts[0] if parts else filename[:64]

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
        print(f"Error parsing {Path(xml_file_path).name}: {e}")
        return None


def index_all_to_rds(ecoinvent_dir: str, db_url: str, batch_size: int = 500):
    """Batch inserts all ecoSpold2 datasets into AWS RDS PostgreSQL."""
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("[ERROR] psycopg2 is required. Run: pip install psycopg2-binary")
        return

    ecoinvent_path = Path(ecoinvent_dir)
    xml_files = list(ecoinvent_path.glob("*.spold")) + list(ecoinvent_path.glob("*.xml"))

    if not xml_files:
        print(f"[WARN] No .spold or .xml files found in {ecoinvent_dir}")
        return

    total = len(xml_files)
    print(f"[INFO] Found {total} datasets. Connecting to AWS RDS PostgreSQL...")
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
        elementary_exchanges = EXCLUDED.elementary_exchanges,
        intermediate_exchanges = EXCLUDED.intermediate_exchanges;
    """

    records = []
    count = 0
    skipped = 0

    for xml_file in xml_files:
        data = parse_single_dataset(str(xml_file))
        if data:
            records.append(data)
            count += 1
        else:
            skipped += 1

        if len(records) >= batch_size:
            execute_batch(cursor, insert_sql, records, page_size=batch_size)
            conn.commit()
            print(f"  [OK] Indexed {count}/{total} datasets (skipped: {skipped})...")
            records = []

    if records:
        execute_batch(cursor, insert_sql, records, page_size=batch_size)
        conn.commit()
        print(f"  [OK] Final batch committed. Total indexed: {count}/{total}")

    cursor.close()
    conn.close()
    print(f"[DONE] Successfully indexed {count} datasets into AWS RDS PostgreSQL! ({skipped} skipped)")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL") or "postgresql://postgres:password@your-rds-endpoint.amazonaws.com:5432/ecometric"
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "backend/data/ecoinvent_v3.12"
    index_all_to_rds(target_dir, db_url)
