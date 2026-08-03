"""
backend/api/transportation.py

Transportation module API endpoints.
Supports saving/fetching A2, A4, C2 transport segments and pre-populating A2 segments from BOM materials.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import get_db_cursor
from engine.transport_module import TransportModule, TransportSegment

router = APIRouter(prefix="/projects", tags=["Transportation"])
logger = logging.getLogger(__name__)


class TransportSegmentInput(BaseModel):
    material_name: Optional[str] = None
    origin_location: str = ""
    destination_location: str = ""
    transport_mode: str = "heavy_truck"
    distance_km: float = 0.0
    weight_tons: float = 0.0
    capacity_utilization_pct: float = 65.0


class TransportationSaveRequest(BaseModel):
    a2_segments: List[TransportSegmentInput] = Field(default_factory=list)
    a4_segment: TransportSegmentInput
    c2_segment: Optional[TransportSegmentInput] = None


@router.post("/{project_id}/transportation/save")
async def save_transportation(
    project_id: str,
    body: TransportationSaveRequest,
    cursor=Depends(get_db_cursor)
):
    """
    Save transportation inputs and return pre-calculated per-module impacts.
    """
    try:
        data_to_store = {
            'a2_segments': [s.dict() for s in body.a2_segments],
            'a4_segment': body.a4_segment.dict(),
            'c2_segment': body.c2_segment.dict() if body.c2_segment else None,
            'saved_at': datetime.now(timezone.utc).isoformat(),
        }

        cursor.execute("""
            UPDATE projects
            SET transportation_data = %s,
                status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (json.dumps(data_to_store), project_id))

        cursor.execute("UPDATE lca_results SET is_final = FALSE WHERE project_id = %s", (project_id,))

        engine = TransportModule()
        a2_segs = [TransportSegment(**s.dict()) for s in body.a2_segments]
        a4_seg = TransportSegment(**body.a4_segment.dict())
        c2_seg = TransportSegment(**body.c2_segment.dict()) if body.c2_segment else None

        totals = engine.calculate_module_totals(a2_segs, a4_seg, c2_seg)

        return {"status": "success", "module_totals": totals}

    except Exception as e:
        logger.exception(f"Failed to save transportation for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/transportation")
async def get_transportation(project_id: str, cursor=Depends(get_db_cursor)):
    """Fetch existing transportation data for the edit form."""
    cursor.execute("SELECT transportation_data FROM projects WHERE id = %s", (project_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    t_data = row.get('transportation_data')
    if isinstance(t_data, str):
        t_data = json.loads(t_data)
    return t_data or {}


@router.get("/{project_id}/materials")
async def get_project_materials(project_id: str, cursor=Depends(get_db_cursor)):
    """Fetch materials for pre-populating A2 transportation rows."""
    cursor.execute("""
        SELECT id, material_name, mass_kg, lc_module, lci_dataset_id
        FROM bom_items
        WHERE project_id = %s
        ORDER BY sort_order ASC, created_at ASC
    """, (project_id,))
    rows = cursor.fetchall()
    
    formatted = []
    for r in rows:
        formatted.append({
            "material_name": r["material_name"],
            "quantity_base": float(r["mass_kg"]) if r["mass_kg"] is not None else 0.0,
            "lc_module": r["lc_module"],
            "lci_dataset_id": r["lci_dataset_id"]
        })
    return formatted
