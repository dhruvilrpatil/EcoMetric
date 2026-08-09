"""
backend/api/calculation.py

LCA calculation trigger and job status endpoints — backed by AWS RDS PostgreSQL.
Runs LCA synchronously (or via Celery if available) and returns run_id.
"""

from __future__ import annotations
import uuid
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from core.db import get_db_cursor

router = APIRouter(prefix="/projects", tags=["Calculation"])


JOB_ERRORS: dict[str, str] = {}


# ─────────────────────────────────────────────────────────────
# POST /projects/{id}/calculate — Trigger LCA computation
# ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/calculate")
async def start_calculation(
    project_id: str,
    background_tasks: BackgroundTasks,
    cursor=Depends(get_db_cursor),
):
    """
    Trigger EN 15804+A2 LCA calculation for the given project.
    Runs synchronously and stores results in lca_results table.
    Returns run_id for polling.
    """
    # Verify project exists
    cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    run_id = str(uuid.uuid4())
    JOB_ERRORS.pop(run_id, None)

    # Write an initial "running" record so the frontend can poll
    cursor.execute(
        """
        INSERT INTO lca_results (id, project_id, run_id, lcia_method, is_final, functional_unit)
        VALUES (%s, %s, %s, 'EF_3_1', FALSE, 'pending')
        ON CONFLICT DO NOTHING
        """,
        (str(uuid.uuid4()), project_id, run_id),
    )

    use_celery = os.getenv("USE_CELERY", "false").lower() == "true"
    if use_celery:
        try:
            from tasks.lca_compute_v2 import run_full_lca
            run_full_lca.delay(project_id, run_id)
            dispatch_mode = "celery"
        except Exception:
            background_tasks.add_task(_run_lca_sync, project_id, run_id)
            dispatch_mode = "background"
    else:
        background_tasks.add_task(_run_lca_sync, project_id, run_id)
        dispatch_mode = "background"

    return {"job_id": run_id, "run_id": run_id, "status": "queued", "dispatch_mode": dispatch_mode}


def _run_lca_sync(project_id: str, run_id: str):
    """Synchronous fallback — called from FastAPI BackgroundTasks."""
    try:
        from tasks.lca_compute_v2 import run_full_lca
        run_full_lca(project_id, run_id)
    except Exception as e:
        import structlog
        log = structlog.get_logger()
        log.error("Background LCA task failed", project_id=project_id, run_id=run_id, error=str(e))
        JOB_ERRORS[run_id] = str(e)


# ─────────────────────────────────────────────────────────────
# GET /projects/{id}/jobs/{job_id} — Poll job status
# ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/jobs/{job_id}")
async def get_job_status(
    project_id: str,
    job_id: str,
    cursor=Depends(get_db_cursor),
):
    """
    Poll the status of an LCA calculation job by run_id.
    Returns status + carbon_footprint if complete.
    """
    if job_id in JOB_ERRORS:
        return {
            "status": "failed",
            "progress": 0,
            "job_id": job_id,
            "error_message": JOB_ERRORS[job_id],
        }

    cursor.execute(
        """
        SELECT run_id, is_final, functional_unit, carbon_footprint_kg_co2e,
               gwp_total_kg_co2e, compliance_summary
        FROM lca_results
        WHERE project_id = %s AND run_id = %s
        ORDER BY run_timestamp DESC
        LIMIT 1
        """,
        (project_id, job_id),
    )
    row = cursor.fetchone()

    if not row:
        # Job may still be initializing
        return {"status": "queued", "progress": 5, "job_id": job_id}

    row_dict = dict(row)

    if row_dict.get("is_final"):
        return {
            "status": "complete",
            "progress": 100,
            "job_id": job_id,
            "carbon_footprint_kg_co2e": row_dict.get("carbon_footprint_kg_co2e"),
            "gwp_total": row_dict.get("gwp_total_kg_co2e"),
        }

    # Still running (is_final = False means computation wrote initial row but hasn't finished)
    return {"status": "running", "progress": 50, "job_id": job_id}

    # Still running (is_final = False means computation wrote initial row but hasn't finished)
    return {"status": "running", "progress": 50, "job_id": job_id}

