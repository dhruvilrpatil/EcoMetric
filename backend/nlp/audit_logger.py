import logging
import json
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ExtractionAuditLogger:
    """
    Log every extraction, match, and user decision to PostgreSQL
    for third-party verification compliance and debugging.
    """

    def __init__(self, conn):
        self.conn = conn

    def log_extraction_event(
        self,
        project_id: str,
        file_name: str,
        raw_text_preview: str,
        extracted_materials: List[Dict[str, Any]]
    ):
        """Log the initial raw text extraction stage."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO nlp_audit_logs (
                        project_id, event_type, file_name, raw_text_preview, extracted_materials
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (
                    project_id,
                    "material_extraction",
                    file_name,
                    raw_text_preview[:1000],
                    json.dumps(extracted_materials)
                ))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log extraction event: {e}")

    def log_matching_event(
        self,
        project_id: str,
        extracted_material_name: str,
        candidates: List[Dict[str, Any]],
        selected_match: Dict[str, Any]
    ):
        """Log matching candidates and final selection."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO nlp_audit_logs (
                        project_id, event_type, file_name, raw_text_preview, extracted_materials, matching_details
                    ) VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    project_id,
                    "material_matching",
                    "live_match",
                    f"Match trigger for: {extracted_material_name}",
                    json.dumps([{"material_name": extracted_material_name}]),
                    json.dumps({
                        "candidates": candidates[:5],
                        "selected": selected_match
                    })
                ))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log matching event: {e}")
