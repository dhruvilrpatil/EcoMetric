"""
backend/scripts/ingest_spold.py

Parses Ecoinvent .spold (EcoSpold v1/v2 XML) files and ingests datasets into 
Firestore `lci_datasets` collection for EcoMetric EPD calculations and LCI search.

Usage:
    python backend/scripts/ingest_spold.py [path_to_spold_file_or_directory]
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

from core.firebase import get_db

def parse_spold_file(file_path: str) -> dict:
    """
    Parses a single .spold XML file and extracts dataset metadata:
    - name, activity, geography, reference_year, unit, gwp_factor, category
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    def strip_tag(tag: str) -> str:
        return tag.split('}')[-1] if '}' in tag else tag

    def find_text_by_tag(element, tag_name, default=""):
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

    # --- 1. Extract Activity & Location ---
    for elem in root.iter():
        t = strip_tag(elem.tag)
        if t == "activityName":
            if elem.text and not activity_name:
                activity_name = elem.text.strip()
        elif t == "shortname" and len(elem.text or "") <= 5:
            if not geography or geography == "GLO":
                geography = elem.text.strip()

    geo_text = find_text_by_tag(root, "shortname")
    if geo_text and len(geo_text) <= 5:
        geography = geo_text

    year_text = find_text_by_tag(root, "startYear") or find_text_by_tag(root, "startDate")
    if year_text:
        try:
            reference_year = int(year_text[:4])
        except ValueError:
            pass

    # --- 2. Extract Reference Product Flow & Unit (EcoSpold v2) ---
    for elem in root.iter():
        if strip_tag(elem.tag) == "intermediateExchange":
            output_group = elem.attrib.get("outputGroup") or elem.attrib.get("outputGroupStr")
            if output_group in ["1", "Output"]:
                p_name = find_text_by_tag(elem, "name")
                p_unit = find_text_by_tag(elem, "unitName")
                p_cat = find_text_by_tag(elem, "classificationValue")
                if p_name:
                    product_name = p_name
                if p_unit:
                    unit = p_unit
                if p_cat:
                    category = p_cat
                break

    # --- 3. EcoSpold v1 Fallback ---
    if not product_name:
        for elem in root.iter():
            if strip_tag(elem.tag) == "referenceFunction":
                product_name = elem.attrib.get("name", filename)
                unit = elem.attrib.get("unit", unit)
                category = elem.attrib.get("category", category)
                activity_name = elem.attrib.get("subCategory", product_name)
                break

    if not product_name:
        product_name = find_text_by_tag(root, "name", filename)
    if not activity_name:
        activity_name = product_name

    # --- 4. Compute GWP Factor from Elementary Exchanges (CO2, CH4, N2O) ---
    calculated_gwp = 0.0
    has_emissions = False
    for elem in root.iter():
        if strip_tag(elem.tag) == "elementaryExchange":
            flow_name = find_text_by_tag(elem, "name").lower()
            amount_str = find_text_by_tag(elem, "amount", "0")
            try:
                amount = float(amount_str)
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


def ingest_spold_target(target_path: str):
    """
    Ingests single .spold file or all .spold files in a folder into Firestore.
    """
    path = Path(target_path).resolve()
    spold_files = []

    if path.is_file():
        spold_files.append(path)
    elif path.is_dir():
        spold_files = list(path.glob("**/*.spold")) + list(path.glob("**/*.xml"))
    else:
        print(f"❌ Error: Path '{target_path}' does not exist.")
        return

    if not spold_files:
        print(f"⚠️ No .spold or .xml files found in '{target_path}'.")
        return

    print(f"🔍 Found {len(spold_files)} SPOLD dataset file(s). Ingesting into database...")

    db = get_db()
    batch = db.batch()
    collection_ref = db.collection("lci_datasets")

    parsed_count = 0

    for file_p in spold_files:
        try:
            item = parse_spold_file(str(file_p))
            doc_ref = collection_ref.document(item["id"])
            batch.set(doc_ref, item)
            parsed_count += 1
            print(f"  ✓ Parsed: [{item['id']}] {item['name']} ({item['geography']}) — GWP: {item['gwp_factor']} {item['unit']}")
            
            # Commit in batches of 400 (Firestore batch max is 500)
            if parsed_count % 400 == 0:
                batch.commit()
                batch = db.batch()
                print(f"  💾 Batch committed ({parsed_count}/{len(spold_files)}).")

        except Exception as e:
            print(f"  ❌ Failed to parse {file_p.name}: {e}")

    if parsed_count % 400 != 0:
        batch.commit()

    print(f"\n✅ Successfully ingested {parsed_count} .spold dataset(s) into Firestore 'lci_datasets' collection!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default directory check
        default_dir = os.path.join(backend_dir, "data", "spold")
        if os.path.exists(default_dir):
            ingest_spold_target(default_dir)
        else:
            print("Usage: python backend/scripts/ingest_spold.py <path_to_spold_file_or_directory>")
            print(f"Or create a directory at '{default_dir}' and place your .spold files there.")
    else:
        ingest_spold_target(sys.argv[1])
