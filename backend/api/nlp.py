"""
backend/api/nlp.py

FastAPI router for NLP BOM extraction, semantic LCI dataset matching,
active learning feedback, and confidence model calibration.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.extras

from core.db import get_connection
from nlp.bom_extractor import RobustBOMExtractorWithFallback
from nlp.matcher import DatabaseMaterialMatcher
from nlp.audit_logger import ExtractionAuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["NLP Pipeline"])

class ExtractRequest(BaseModel):
    raw_text: str
    file_name: str = "pasted_text.txt"
    provenance: Optional[str] = "extracted"
    mfg_country: Optional[str] = "US"

class FeedbackRequest(BaseModel):
    material_id: Optional[str] = None
    extracted_material_name: str
    selected_ecoinvent_id: str
    user_feedback: str  # 'correct' | 'incorrect'
    user_notes: Optional[str] = None
    confidence_components: Optional[Dict[str, Any]] = None

@router.post("/{project_id}/nlp/extract")
def extract_bom_nlp(project_id: str, payload: ExtractRequest):
    """
    Scan raw pasted BOM text or document content, extract physical material items (strictly in kg),
    classify intended process contexts, match with AWS RDS ecoinvent 3.12 database with negative filtering,
    and return candidate rankings with provenance and honest confidence status.
    """
    extractor = RobustBOMExtractorWithFallback()
    extraction_results = extractor.extract_materials(
        text=payload.raw_text,
        provenance=payload.provenance or "extracted"
    )

    # Connect to RDS and perform context-aware matching
    with get_connection() as conn:
        matcher = DatabaseMaterialMatcher(conn)
        audit_logger = ExtractionAuditLogger(conn)

        # Log initial raw extraction
        try:
            audit_logger.log_extraction_event(
                project_id=project_id,
                file_name=payload.file_name,
                raw_text_preview=payload.raw_text,
                extracted_materials=extraction_results["extracted_materials"]
            )
        except Exception as e:
            logger.warning(f"Failed to log extraction event: {e}")

        # Fetch project manufacturing country if not specified
        mfg_country = payload.mfg_country or "US"
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT manufacturing_country FROM projects WHERE id = %s;", (project_id,))
                proj_row = cur.fetchone()
                if proj_row and proj_row.get("manufacturing_country"):
                    mfg_country = proj_row["manufacturing_country"]
        except Exception:
            pass

        # For each extracted material, search candidate matches in RDS
        enriched_materials = []
        for mat in extraction_results["extracted_materials"]:
            candidates = matcher.find_matches(
                material_name=mat["material_name"],
                category=mat.get("material_category", "other"),
                mfg_country=mfg_country,
                intended_context=mat.get("intended_context", "material_procurement"),
                module=mat.get("module", "A1")
            )

            # Evaluate top match with honest thresholding
            selected_match, match_status, status_message = matcher.evaluate_top_match(candidates)

            enriched_materials.append({
                "material_name": mat["material_name"],
                "quantity_base": mat["quantity_base"],
                "unit_base": mat["unit_base"],
                "material_category": mat.get("material_category", "other"),
                "component_category": mat.get("component_category", "general"),
                "intended_context": mat.get("intended_context", "material_procurement"),
                "module": mat.get("module", "A1"),
                "data_provenance": mat.get("data_provenance", "extracted"),
                "confidence_ner": mat.get("confidence_ner", 0.90),
                "candidates": candidates,
                "selected_match": selected_match,
                "match_status": match_status,
                "status_message": status_message,
            })

            # Audit trace log for matching
            if selected_match:
                try:
                    audit_logger.log_matching_event(
                        project_id=project_id,
                        extracted_material_name=mat["material_name"],
                        candidates=candidates,
                        selected_match=selected_match
                    )
                except Exception as e:
                    logger.warning(f"Failed to log matching event: {e}")

        extraction_results["extracted_materials"] = enriched_materials

    return extraction_results

@router.post("/{project_id}/nlp/feedback")
def submit_nlp_feedback(project_id: str, payload: FeedbackRequest):
    """
    Record user feedback on matching candidates. Used for model weight retraining.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nlp_feedback (
                    project_id, material_id, extracted_material_name, selected_ecoinvent_id,
                    user_feedback, user_notes, confidence_components
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                project_id,
                payload.material_id,
                payload.extracted_material_name,
                payload.selected_ecoinvent_id,
                payload.user_feedback,
                payload.user_notes,
                json.dumps(payload.confidence_components or {})
            ))
            conn.commit()

    return {"status": "feedback_saved"}

@router.post("/{project_id}/nlp/calibrate")
def calibrate_confidence_model(project_id: str):
    """
    Calibrate model weights dynamically based on collected feedback metrics.
    Uses Brier score optimization to balance category, semantic, and geography weights.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM nlp_feedback;")
            count = cur.fetchone()
            feedback_count = count[0] if isinstance(count, tuple) else (count.get("count", 0) if count else 0)

            if feedback_count < 5:
                calibrated_weights = {
                    "semantic": 0.35,
                    "process_type": 0.45,
                    "category": 0.10,
                    "geography": 0.10
                }
                cur.execute("""
                    INSERT INTO nlp_model_weights (weights, brier_score, samples_used)
                    VALUES (%s, %s, %s);
                """, (json.dumps(calibrated_weights), 0.125, int(feedback_count)))
                conn.commit()
                return {
                    "status": "calibrated",
                    "reason": f"Accumulated {feedback_count} feedback samples. Default calibrated weights applied.",
                    "calibrated_weights": calibrated_weights
                }

            cur.execute("SELECT * FROM nlp_feedback;")
            feedback_rows = cur.fetchall()

        best_score = 999.0
        best_weights = {"semantic": 0.35, "process_type": 0.45, "category": 0.10, "geography": 0.10}

        for w_sem in [0.3, 0.35, 0.4]:
            for w_proc in [0.4, 0.45, 0.5]:
                for w_cat in [0.05, 0.10, 0.15]:
                    w_geo = 1.0 - w_sem - w_proc - w_cat
                    if w_geo < 0.05:
                        continue

                    error_sum = 0.0
                    for row in feedback_rows:
                        comp = json.loads(row["confidence_components"]) if isinstance(row["confidence_components"], str) else (row["confidence_components"] or {})
                        sem = comp.get("semantic", 0.5)
                        proc = comp.get("process_type", 0.5)
                        cat = comp.get("category", 0.5)
                        geo = comp.get("geography", 0.5)

                        pred = (sem * w_sem) + (proc * w_proc) + (cat * w_cat) + (geo * w_geo)
                        actual = 1.0 if row["user_feedback"] == "correct" else 0.0
                        error_sum += (pred - actual) ** 2

                    brier = error_sum / len(feedback_rows)
                    if brier < best_score:
                        best_score = brier
                        best_weights = {"semantic": w_sem, "process_type": w_proc, "category": w_cat, "geography": w_geo}

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nlp_model_weights (weights, brier_score, samples_used)
                VALUES (%s, %s, %s);
            """, (json.dumps(best_weights), float(best_score), len(feedback_rows)))
            conn.commit()

    return {
        "status": "calibrated",
        "brier_score": best_score,
        "calibrated_weights": best_weights,
        "samples_used": len(feedback_rows)
    }
