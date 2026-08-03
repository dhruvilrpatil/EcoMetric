"""
backend/scripts/ingest_lci_data.py

Ingests mock Ecoinvent v3.10 datasets into Firestore `lci_datasets`.
This provides the data for the PRD Step 2 (Inventory) material search.

PRD §9.2 requires:
 - name
 - activity (mapped to 'description' or 'category' in search)
 - geography
 - reference_year
 - data_quality_score
 - unit
 - gwp_factor (mocked impact per unit)
"""

import sys
import os
from pathlib import Path
from loguru import logger # Using structlog or loguru for scripts

# Add backend root to sys.path so we can import core
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from core.firebase import get_db

MOCK_ECOINVENT_DATA = [
    {
        "id": "mat-steel-1",
        "name": "Steel, low-alloyed",
        "activity": "steel production, converter, unalloyed",
        "geography": "RER",
        "reference_year": 2023,
        "data_quality_score": 1.2,
        "unit": "kg",
        "gwp_factor": 2.45,  # kg CO2e per kg
        "category": "Metals"
    },
    {
        "id": "mat-steel-2",
        "name": "Steel, electric, un- and low-alloyed",
        "activity": "steel production, electric, un- and low-alloyed",
        "geography": "GLO",
        "reference_year": 2023,
        "data_quality_score": 1.5,
        "unit": "kg",
        "gwp_factor": 1.12,
        "category": "Metals"
    },
    {
        "id": "mat-concrete-1",
        "name": "Concrete, normal",
        "activity": "concrete production, normal",
        "geography": "CH",
        "reference_year": 2023,
        "data_quality_score": 1.1,
        "unit": "m3",
        "gwp_factor": 250.0,
        "category": "Construction Materials"
    },
    {
        "id": "mat-elec-1",
        "name": "Electricity, medium voltage",
        "activity": "market for electricity, medium voltage",
        "geography": "US",
        "reference_year": 2023,
        "data_quality_score": 1.0,
        "unit": "kWh",
        "gwp_factor": 0.42,
        "category": "Energy"
    },
    {
        "id": "mat-elec-2",
        "name": "Electricity, from wind power",
        "activity": "electricity production, wind, 1-3MW turbine, onshore",
        "geography": "RER",
        "reference_year": 2023,
        "data_quality_score": 1.3,
        "unit": "kWh",
        "gwp_factor": 0.015,
        "category": "Energy"
    },
    {
        "id": "mat-glass-1",
        "name": "Flat glass, coated",
        "activity": "flat glass production, coated",
        "geography": "GLO",
        "reference_year": 2022,
        "data_quality_score": 1.8,
        "unit": "kg",
        "gwp_factor": 1.05,
        "category": "Materials"
    },
    {
        "id": "mat-trans-1",
        "name": "Transport, freight, lorry >32 metric ton, EURO5",
        "activity": "transport, freight, lorry >32 metric ton, EURO5",
        "geography": "RER",
        "reference_year": 2023,
        "data_quality_score": 1.4,
        "unit": "tkm",
        "gwp_factor": 0.089,
        "category": "Transport"
    }
]

def run_ingestion():
    db = get_db()
    batch = db.batch()
    
    collection_ref = db.collection("lci_datasets")
    
    print(f"Ingesting {len(MOCK_ECOINVENT_DATA)} LCI datasets into Firestore...")
    
    for item in MOCK_ECOINVENT_DATA:
        doc_ref = collection_ref.document(item["id"])
        batch.set(doc_ref, item)
    
    # Commit the batch
    batch.commit()
    print("✅ Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()
