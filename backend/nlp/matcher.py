"""
backend/nlp/matcher.py

Semantic, context-aware LCI material matcher for EcoMetric.
Maps BOM materials to ecoinvent 3.12 datasets with:
- Strict process-type classification (Material Production vs Market vs Manufacturing vs EOL/Scrap vs Transport)
- Negative semantic filtering (rejects welding, scrap, waste, used refrigerant in raw material A1 BOMs)
- Context awareness (permits welding/machining only when explicitly specified)
- Chemical/refrigerant validation (distinguishes exact refrigerants; flags missing datasets like R-1233zd(E))
- Honest confidence scoring and multi-candidate ranking.
"""

from __future__ import annotations
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Process type constants
PROCESS_MATERIAL_PROD = "Material Production"
PROCESS_MARKET = "Market / Procurement"
PROCESS_COMPONENT_PROD = "Component Production"
PROCESS_MANUFACTURING = "Manufacturing Process"
PROCESS_EOL_SCRAP = "End-of-Life / Scrap"
PROCESS_TRANSPORT = "Transport / Logistics"
PROCESS_OTHER = "Other Process"

# Canonical material synonym mappings to targeted database search stems
MATERIAL_SYNONYMS: Dict[str, Dict[str, Any]] = {
    "steel": {
        "category": "metals",
        "component_category": "structural",
        "stems": [
            "steel production, converter, low-alloyed",
            "market for steel, low-alloyed",
            "market for steel, unalloyed",
            "steel production, converter, unalloyed",
            "steel production, electric arc furnace",
            "market for steel, chromium steel 18/8, hot rolled",
            "steel production, chromium steel 18/8, hot rolled",
            "steel production"
        ]
    },
    "stainless steel": {
        "category": "metals",
        "component_category": "structural",
        "stems": [
            "market for steel, chromium steel 18/8, hot rolled",
            "steel production, chromium steel 18/8, hot rolled",
            "market for steel, chromium steel 18/8",
            "steel production"
        ]
    },
    "copper": {
        "category": "metals",
        "component_category": "piping / electrical",
        "stems": [
            "market for copper, cathode",
            "copper production, cathode, solvent extraction and electrowinning process",
            "market for copper concentrate, sulfide ore",
            "copper production"
        ]
    },
    "aluminum": {
        "category": "metals",
        "component_category": "structural / heat exchange",
        "stems": [
            "aluminium production, primary, ingot",
            "market for aluminium, primary, ingot",
            "aluminium production, primary, liquid, prebake",
            "aluminium production"
        ]
    },
    "aluminium": {
        "category": "metals",
        "component_category": "structural / heat exchange",
        "stems": [
            "aluminium production, primary, ingot",
            "market for aluminium, primary, ingot",
            "aluminium production, primary, liquid, prebake",
            "aluminium production"
        ]
    },
    "iron": {
        "category": "metals",
        "component_category": "structural / casting",
        "stems": [
            "market for pig iron",
            "pig iron production",
            "market for cast iron",
            "cast iron production"
        ]
    },
    "cast iron": {
        "category": "metals",
        "component_category": "structural / casting",
        "stems": [
            "market for cast iron",
            "cast iron production",
            "market for pig iron",
            "pig iron production"
        ]
    },
    "brass": {
        "category": "metals",
        "component_category": "fittings",
        "stems": [
            "market for brass",
            "brass production"
        ]
    },
    "electronics": {
        "category": "electronics",
        "component_category": "control / electrical",
        "stems": [
            "market for electronics, for control units",
            "electronics production, for control units",
            "market for electronic component, active, unspecified",
            "market for electronic component, passive",
            "electronics production"
        ]
    },
    "electronic": {
        "category": "electronics",
        "component_category": "control / electrical",
        "stems": [
            "market for electronics, for control units",
            "electronics production, for control units",
            "market for electronic component, active, unspecified",
            "market for electronic component, passive"
        ]
    },
    "circuit board": {
        "category": "electronics",
        "component_category": "control / electrical",
        "stems": [
            "market for printed wiring board, surface mount",
            "market for electronics, for control units",
            "electronics production, for control units"
        ]
    },
    "polyethylene": {
        "category": "plastics",
        "component_category": "insulation / casing",
        "stems": [
            "polyethylene production, high density, granulate",
            "polyethylene production, low density, granulate",
            "market for polyethylene, high density, granulate"
        ]
    },
    "polypropylene": {
        "category": "plastics",
        "component_category": "insulation / casing",
        "stems": [
            "polypropylene production, granulate",
            "market for polypropylene, granulate"
        ]
    },
    "pvc": {
        "category": "plastics",
        "component_category": "piping / insulation",
        "stems": [
            "market for polyvinylchloride, suspension polymerised",
            "polyvinylchloride production, suspension polymerisation",
            "market for polyvinylchloride, emulsion polymerised"
        ]
    },
    "rubber": {
        "category": "elastomers",
        "component_category": "gaskets / seals",
        "stems": [
            "market for synthetic rubber",
            "synthetic rubber production"
        ]
    },
    "glass wool": {
        "category": "mineral fibers",
        "component_category": "thermal insulation",
        "stems": [
            "market for glass wool mat",
            "glass wool mat production"
        ]
    },
    "mineral wool": {
        "category": "mineral fibers",
        "component_category": "thermal insulation",
        "stems": [
            "market for stone wool",
            "stone wool production"
        ]
    },
    "glass": {
        "category": "glass",
        "component_category": "panels",
        "stems": [
            "market for flat glass, uncoated",
            "flat glass production, uncoated"
        ]
    },
    "refrigerant r-134a": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "market for tetrafluoroethane, R134a",
            "tetrafluoroethane production"
        ]
    },
    "r-134a": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "market for tetrafluoroethane, R134a",
            "tetrafluoroethane production"
        ]
    },
    "r134a": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "market for tetrafluoroethane, R134a",
            "tetrafluoroethane production"
        ]
    },
    "r-1233zd(e)": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "1233zd",
            "r-1233zd",
            "1-chloro-3,3,3-trifluoropropene",
            "hfo-1233zd"
        ]
    },
    "r-1233zd": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "1233zd",
            "r-1233zd",
            "1-chloro-3,3,3-trifluoropropene",
            "hfo-1233zd"
        ]
    },
    "r1233zd": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "1233zd",
            "r-1233zd",
            "1-chloro-3,3,3-trifluoropropene"
        ]
    },
    "r-32": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "market for difluoromethane",
            "difluoromethane production"
        ]
    },
    "r-22": {
        "category": "refrigerant",
        "component_category": "working fluid",
        "stems": [
            "market for chlorodifluoromethane",
            "chlorodifluoromethane production"
        ]
    }
}


def classify_process_type(activity_name: str) -> str:
    """
    Classify an ecoinvent activity into its structural lifecycle role.
    """
    name = activity_name.lower().strip()

    # 1. End-of-Life / Scrap / Treatment / Waste
    eol_keywords = [
        'scrap', 'waste', 'treatment of', 'disposal', 'recycling', 'used refrigerant',
        'shredder residue', 'slag', 'tailings', 'bottom ash', 'dismantling', 'landfill',
        'incineration', 'leach residue', 'waste plastic', 'electronics scrap', 'copper cake'
    ]
    if any(kw in name for kw in eol_keywords):
        return PROCESS_EOL_SCRAP

    # 2. Manufacturing / Fabrication / Machining Process
    mfg_keywords = [
        'welding', 'removed by', 'machining', 'turning', 'milling', 'drilling',
        'cutting', 'stamping', 'impact extrusion', 'surface treatment', 'casting facility',
        'smelting facility', 'laser machining', 'coating,', 'flame cutting', 'soldering'
    ]
    if any(kw in name for kw in mfg_keywords):
        return PROCESS_MANUFACTURING

    # 3. Transport & Freight Logistics
    if name.startswith('transport,') or 'lorry with' in name or 'freight' in name:
        return PROCESS_TRANSPORT

    # 4. Market / Procurement
    if name.startswith('market for') or name.startswith('market group for'):
        if any(c in name for c in ['electronic', 'circuit board', 'control unit', 'capacitor', 'diode', 'sensor']):
            return PROCESS_COMPONENT_PROD
        return PROCESS_MARKET

    # 5. Production (Material or Component)
    if 'production' in name:
        if any(c in name for c in ['electronic', 'device', 'control unit', 'computer', 'sensor', 'switch']):
            return PROCESS_COMPONENT_PROD
        return PROCESS_MATERIAL_PROD

    return PROCESS_OTHER


class DatabaseMaterialMatcher:
    """
    Context-aware LCI material matcher backed by AWS RDS PostgreSQL (ecoinvent 3.12 cutoff).
    Performs negative semantic filtering, positive process-type boosting, and honest confidence assessment.
    """

    def __init__(self, conn):
        self.conn = conn

    def normalize_input(self, material_name: str, intended_context: str = "material_procurement") -> Tuple[str, List[str], str]:
        """
        Normalize material name, extract search stems, and determine default category.
        """
        clean_name = material_name.lower().strip()

        # If this is a manufacturing/fabrication process (e.g. welding, machining, turning, milling)
        if intended_context == "manufacturing_process" or any(w in clean_name for w in ["welding", "machining", "turning", "milling", "cutting", "drilling", "stamping", "extrusion"]):
            stems = []
            if "weld" in clean_name:
                if "alumin" in clean_name:
                    stems = ["welding, arc, aluminium", "welding, aluminium", "welding"]
                elif "steel" in clean_name:
                    stems = ["welding, arc, steel", "welding, gas, steel", "welding, steel", "welding"]
                else:
                    stems = ["welding"]
            elif any(w in clean_name for w in ["machining", "turning", "milling", "drilling"]):
                if "steel" in clean_name:
                    stems = ["steel removed by", "milling, steel", "turning, steel"]
                elif "alumin" in clean_name:
                    stems = ["aluminium removed by", "milling, aluminium", "turning, aluminium"]
                else:
                    stems = ["removed by", "machining"]
            else:
                stems = [clean_name]
            return clean_name, stems, "metals"

        # Check explicit synonym mapping for raw materials
        for syn_key, info in MATERIAL_SYNONYMS.items():
            pattern = r'\b' + re.escape(syn_key) + r'\b'
            if re.search(pattern, clean_name) or syn_key in clean_name:
                return syn_key, info["stems"], info["category"]

        # Default fallback stems
        stems = [clean_name]
        category = "other"
        if any(w in clean_name for w in ["metal", "alloy"]):
            category = "metals"
        elif any(w in clean_name for w in ["plastic", "polymer"]):
            category = "plastics"
        elif any(w in clean_name for w in ["gas", "fluid", "chemical"]):
            category = "chemicals"

        return clean_name, stems, category

    def find_matches(
        self,
        material_name: str,
        category: str = "other",
        mfg_country: str = "GLO",
        intended_context: str = "material_procurement",
        module: str = "A1"
    ) -> List[Dict[str, Any]]:
        """
        Search RDS ecoinvent database using context-aware semantic ranking.
        
        Args:
            material_name: Material string from BOM (e.g. "Steel Frame", "Copper tube", "Aluminum: 300kg")
            category: High-level material category (e.g. "metals", "plastics", "electronics", "refrigerant")
            mfg_country: Preferred manufacturing geography code (e.g. "US", "RER", "GLO")
            intended_context: "material_procurement" (A1 raw materials) vs "manufacturing_process" vs "end_of_life"
            module: Target LCA module ("A1", "A2", "A3", etc.)
        """
        geo_pref = (mfg_country or "GLO").upper()

        # Step 1: Detect explicit process or EOL context overrides from the input string itself
        input_lower = material_name.lower()
        if any(w in input_lower for w in ["welding", "machining", "turning", "milling", "cutting", "drilling", "stamping", "extrusion"]):
            intended_context = "manufacturing_process"
        elif any(w in input_lower for w in ["scrap", "waste", "recycling", "disposal", "used"]):
            intended_context = "end_of_life"

        # Step 2: Normalize and extract target stems
        canonical_key, stems, detected_category = self.normalize_input(material_name, intended_context)
        if category == "other" or not category:
            category = detected_category

        candidates: List[Dict[str, Any]] = []

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build search conditions combining trigram similarity and targeted stem lookups
            stem_conds = " OR ".join(["activity_name ILIKE %s" for _ in stems])
            params: List[Any] = [f"%{s}%" for s in stems]
            
            # Also include pg_trgm similarity search
            sql = f"""
                SELECT 
                    id, 
                    activity_name, 
                    geography, 
                    reference_year,
                    gwp_factor,
                    similarity(activity_name, %s) AS semantic_score
                FROM lci_database
                WHERE ({stem_conds}) OR similarity(activity_name, %s) > 0.35
                ORDER BY semantic_score DESC
                LIMIT 40;
            """
            cur.execute(sql, params + [material_name, material_name])
            rows = cur.fetchall()

            for row in rows:
                act_name = row["activity_name"]
                act_lower = act_name.lower()
                sem_score = float(row.get("semantic_score") or 0.0)
                p_type = classify_process_type(act_name)

                # Base score calculation
                base_score = sem_score

                # Direct stem hit boost
                stem_match = any(s.lower() in act_lower for s in stems)
                if stem_match:
                    base_score = max(base_score, 0.75)

                # Step 3: Strict Context & Process-Type Alignment Scoring
                process_score = 0.0

                if intended_context == "material_procurement":
                    # For A1 BOM, we strictly prioritize Material Production & Procurement Markets
                    if p_type in (PROCESS_MATERIAL_PROD, PROCESS_MARKET, PROCESS_COMPONENT_PROD):
                        process_score = 1.0
                        
                        # Extra boost for high-fidelity primary / cathode / control unit / ingot datasets
                        if any(kw in act_lower for kw in ['cathode', 'primary, ingot', 'low-alloyed', 'unalloyed', 'control units', 'granulate', 'tetrafluoroethane']):
                            process_score += 0.15
                    elif p_type == PROCESS_MANUFACTURING:
                        # HEAVY PENALTY: Do NOT map welding / machining into raw material BOM!
                        process_score = -0.80
                    elif p_type == PROCESS_EOL_SCRAP:
                        # HEAVY PENALTY: Do NOT map scrap / waste / used refrigerant into raw material BOM!
                        process_score = -0.90
                    elif p_type == PROCESS_TRANSPORT:
                        process_score = -0.80
                    else:
                        process_score = 0.20

                elif intended_context == "manufacturing_process":
                    # User explicitly requested a manufacturing/fabrication process (e.g. welding)
                    if p_type == PROCESS_MANUFACTURING:
                        process_score = 1.0
                    else:
                        process_score = -0.50

                elif intended_context == "end_of_life":
                    # User explicitly requested scrap/waste/disposal
                    if p_type == PROCESS_EOL_SCRAP:
                        process_score = 1.0
                    else:
                        process_score = -0.50

                # Category alignment score
                cat_score = 0.5
                if category != "other":
                    if category == "metals" and any(k in act_lower for k in ["steel", "copper", "aluminium", "aluminum", "iron", "metal", "brass"]):
                        cat_score = 1.0
                    elif category == "plastics" and any(k in act_lower for k in ["polyethylene", "polypropylene", "pvc", "plastic", "polymer"]):
                        cat_score = 1.0
                    elif category == "electronics" and any(k in act_lower for k in ["electronic", "circuit", "control unit"]):
                        cat_score = 1.0
                    elif category == "refrigerant" and any(k in act_lower for k in ["refrigerant", "tetrafluoroethane", "difluoromethane", "chlorodifluoromethane"]):
                        cat_score = 1.0

                # Geography alignment score
                geo_score = 0.5
                row_geo = (row.get("geography") or "GLO").upper()
                if row_geo == geo_pref:
                    geo_score = 1.0
                elif row_geo in ("GLO", "RER", "ROW"):
                    geo_score = 0.7

                # Composite score calculation
                # Weighted: Semantic (35%), Process Type Alignment (45%), Category (10%), Geography (10%)
                raw_confidence = (base_score * 0.35) + (process_score * 0.45) + (cat_score * 0.10) + (geo_score * 0.10)
                
                # Check for specific hard exclusions on A1:
                # E.g. "welding, gas, steel" when input was "steel"
                if intended_context == "material_procurement" and p_type in (PROCESS_MANUFACTURING, PROCESS_EOL_SCRAP, PROCESS_TRANSPORT):
                    raw_confidence = min(raw_confidence, 0.20)

                # If the material is a specific refrigerant (e.g. R-1233zd) and the candidate is "used R12", hard zero
                if "1233" in input_lower and ("r12" in act_lower or "r-12" in act_lower or "used" in act_lower):
                    raw_confidence = 0.0

                confidence_pct = round(max(0.0, min(100.0, raw_confidence * 100.0)), 1)

                # Filter out negative/near-zero candidates
                if confidence_pct < 15.0:
                    continue

                candidates.append({
                    "ecoinvent_id": str(row["id"]),
                    "ecoinvent_name": act_name,
                    "geography": row.get("geography") or "GLO",
                    "database_version": "ecoinvent 3.12 (cutoff)",
                    "reference_year": row.get("reference_year") or 2024,
                    "gwp_factor": float(row["gwp_factor"]) if row.get("gwp_factor") is not None else None,
                    "process_type": p_type,
                    "intended_module": module,
                    "match_confidence": confidence_pct,
                    "confidence_components": {
                        "semantic": round(base_score, 3),
                        "process_type": round(process_score, 3),
                        "category": round(cat_score, 3),
                        "geography": round(geo_score, 3)
                    }
                })

        # Sort candidates by match confidence descending
        candidates.sort(key=lambda x: x["match_confidence"], reverse=True)

        # Disambiguate top matches
        return candidates[:5]

    def evaluate_top_match(self, candidates: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """
        Evaluate the top candidate and assign compliance status.
        
        Returns:
            (selected_match, match_status, status_message)
            match_status: "valid_match" | "low_confidence" | "not_found"
        """
        if not candidates or candidates[0]["match_confidence"] < 40.0:
            return None, "not_found", "Dataset not found — manual mapping required"

        top = candidates[0]
        confidence = top["match_confidence"]

        if confidence >= 70.0:
            return top, "valid_match", "✓ Valid material match"
        else:
            return top, "low_confidence", "⚠ Manual verification recommended"
