import json
import logging
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DatabaseMaterialMatcher:
    """
    Search AWS RDS PostgreSQL database for the closest matching Ecoinvent 3.12 process,
    computing confidence scores and weights based on pg_trgm similarity, category alignment,
    and manufacturing geography.
    """

    def __init__(self, conn):
        self.conn = conn

    def get_calibrated_weights(self) -> Dict[str, float]:
        """Fetch custom weights from database, otherwise fall back to defaults."""
        default_weights = {
            "semantic": 0.50,
            "category": 0.30,
            "geography": 0.20
        }
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT weights FROM nlp_model_weights ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                if row and row.get("weights"):
                    weights = row["weights"]
                    # Ensure they add up to 1
                    total = sum(weights.values())
                    if total > 0:
                        return {k: v / total for k, v in weights.items()}
        except Exception as e:
            logger.warning(f"Failed to load calibrated weights: {e}")
        return default_weights

    def find_matches(self, material_name: str, category: str = "other", mfg_country: str = "GLO") -> List[Dict[str, Any]]:
        """
        Query the database using trigram similarity and filter candidate matches.
        """
        weights = self.get_calibrated_weights()
        w_sem = weights.get("semantic", 0.50)
        w_cat = weights.get("category", 0.30)
        w_geo = weights.get("geography", 0.20)

        # Standardize geography codes
        geo_pref = "GLO"
        if mfg_country:
            geo_pref = mfg_country.upper()

        candidates = []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # We use pg_trgm similarity index to score database activity names
            cur.execute("""
                SELECT 
                    id, 
                    activity_name, 
                    geography, 
                    reference_year,
                    gwp_factor,
                    similarity(activity_name, %s) AS semantic_score
                FROM lci_database
                ORDER BY semantic_score DESC
                LIMIT 15;
            """, (material_name,))
            rows = cur.fetchall()

            for row in rows:
                sem_score = float(row["semantic_score"] or 0.0)
                
                # Category score boost if keyword alignment is high
                cat_alignment = 0.0
                row_name_lower = row["activity_name"].lower()
                
                if category != "other" and category in row_name_lower:
                    cat_alignment = 1.0
                elif any(kw in row_name_lower for kw in ["steel", "iron", "copper", "aluminum", "metal"] if category == "metals"):
                    cat_alignment = 0.8
                elif any(kw in row_name_lower for kw in ["plastic", "polyethylene", "pvc", "pet"] if category == "plastics"):
                    cat_alignment = 0.8
                elif "refrigerant" in row_name_lower if category == "refrigerant" else False:
                    cat_alignment = 1.0

                # Geography alignment score
                geo_alignment = 0.0
                row_geo = (row["geography"] or "GLO").upper()
                if row_geo == geo_pref:
                    geo_alignment = 1.0
                elif row_geo == "GLO" or row_geo == "RER":
                    geo_alignment = 0.5

                # Compute final composite confidence score
                final_score = (sem_score * w_sem) + (cat_alignment * w_cat) + (geo_alignment * w_geo)
                final_confidence = round(final_score * 100.0, 2)

                candidates.append({
                    "ecoinvent_id": row["id"],
                    "ecoinvent_name": row["activity_name"],
                    "geography": row["geography"],
                    "reference_year": row["reference_year"],
                    "gwp_factor": float(row["gwp_factor"]) if row["gwp_factor"] is not None else None,
                    "similarity_score": round(sem_score, 4),
                    "match_confidence": final_confidence,
                    "confidence_components": {
                        "semantic": round(sem_score, 4),
                        "category": cat_alignment,
                        "geography": geo_alignment
                    }
                })

        # Sort candidate matches by confidence score descending
        candidates.sort(key=lambda x: x["match_confidence"], reverse=True)
        return candidates
