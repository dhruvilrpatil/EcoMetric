"""
backend/scripts/ingest_spold_rds.py

Parses Ecoinvent .spold files and ingests datasets into AWS RDS PostgreSQL.
Supports direct database connection via DATABASE_URL or DB parameters.

Usage:
    python backend/scripts/ingest_spold_rds.py path/to/spold_files_dir
"""

import sys
import os
import glob
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

# Add backend root to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

def parse_spold_file(file_path: str) -> dict:
    """Parses a single .spold XML file into a structured dictionary."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    def strip_tag(tag: str) -> str:
        return tag.split('}')[-1] if '}' in tag else tag

    def find_text(element, tag_name, default=""):
        for elem in element.iter():
            if strip_tag(elem.tag) == tag_name and elem.text:
                return elem.text.strip()
        return default

    filename = Path(file_path).stem
    dataset_id = f"spold-{filename[:24]}-{uuid.uuid4().hex[:6]}"
    
    activity_name = ""
    product_name = ""
    geography = "GLO"
    reference_year = 2023
    unit = "kg"
    category = "Materials"
    gwp_factor = 1.0
    dqi_score = 1.2

    for elem in root.iter():
        t = strip_tag(elem.tag)
        if t == "activityName" and elem.text and not activity_name:
            activity_name = elem.text.strip()
        elif t == "shortname" and elem.text and len(elem.text.strip()) <= 5:
            geography = elem.text.strip()

    year_text = find_text(root, "startYear") or find_text(root, "startDate")
    if year_text:
        try:
            reference_year = int(year_text[:4])
        except ValueError:
            pass

    for elem in root.iter():
        if strip_tag(elem.tag) == "intermediateExchange":
            output_group = elem.attrib.get("outputGroup") or elem.attrib.get("outputGroupStr")
            if output_group in ["1", "Output"]:
                p_name = find_text(elem, "name")
                p_unit = find_text(elem, "unitName")
                p_cat = find_text(elem, "classificationValue")
                if p_name: product_name = p_name
                if p_unit: unit = p_unit
                if p_cat: category = p_cat
                break

    if not product_name:
        product_name = find_text(root, "name", filename)
    if not activity_name:
        activity_name = product_name

    calculated_gwp = 0.0
    has_emissions = False
    for elem in root.iter():
        if strip_tag(elem.tag) == "elementaryExchange":
            flow_name = find_text(elem, "name").lower()
            try:
                amount = float(find_text(elem, "amount", "0"))
            except ValueError:
                amount = 0.0

            if "carbon dioxide" in flow_name or "co2" in flow_name:
                calculated_gwp += amount * 1.0
                has_emissions = True
            elif "methane" in flow_name or "ch4" in flow_name:
                calculated_gwp += amount * 29.8
                has_emissions = True
            elif "dinitrogen monoxide" in flow_name or "nitrous oxide" in flow_name or "n2o" in flow_name:
                calculated_gwp += amount * 273.0
                has_emissions = True

    if has_emissions and calculated_gwp > 0:
        gwp_factor = round(calculated_gwp, 4)

    return {
        "id": dataset_id,
        "name": product_name,
        "activity": activity_name,
        "geography": geography,
        "reference_year": reference_year,
        "data_quality_score": dqi_score,
        "unit": unit,
        "gwp_factor": gwp_factor,
        "category": category,
        "source_file": filename
    }


def ingest_to_rds(spold_dir_or_file: str, db_url: str):
    """
    Parses .spold files and inserts datasets into AWS RDS PostgreSQL database.
    Requires psycopg2-binary or psycopg2 installed.
    """
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        print("❌ Error: psycopg2 is required for RDS ingestion. Run: pip install psycopg2-binary")
        return

    path = Path(spold_dir_or_file).resolve()
    spold_files = [path] if path.is_file() else list(path.glob("**/*.spold")) + list(path.glob("**/*.xml"))

    if not spold_files:
        print(f"⚠️ No .spold or .xml files found at '{spold_dir_or_file}'.")
        return

    print(f"🔍 Found {len(spold_files)} SPOLD dataset file(s). Connecting to AWS RDS...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO lci_datasets (
        id, name, activity, geography, reference_year, data_quality_score, unit, gwp_factor, category, source_file
    ) VALUES (
        %(id)s, %(name)s, %(activity)s, %(geography)s, %(reference_year)s, %(data_quality_score)s, %(unit)s, %(gwp_factor)s, %(category)s, %(source_file)s
    )
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        gwp_factor = EXCLUDED.gwp_factor;
    """

    records = []
    for file_p in spold_files:
        try:
            records.append(parse_spold_file(str(file_p)))
        except Exception as e:
            print(f"  ❌ Skipping {file_p.name}: {e}")

    execute_batch(cursor, insert_query, records, page_size=200)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Successfully loaded {len(records)} dataset(s) into AWS RDS PostgreSQL!")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL") or "postgresql://postgres:password@your-rds-endpoint.amazonaws.com:5432/ecometric"
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(backend_dir, "data", "spold")
    ingest_to_rds(target, db_url)
