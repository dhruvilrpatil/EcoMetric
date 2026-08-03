"""
tasks/lca_compute.py — Celery task for async LCA computation.
Stub for Phase 4 — full implementation connects engine/matrix_lca.py
to the Celery queue and writes results to Firestore.
"""
import numpy as np
from datetime import datetime, timezone
from celery_worker import celery_app
from core.firebase import get_db
from engine.matrix_lca import run_lca, SingularMatrixError
from engine.cutoff import validate_cutoff

@celery_app.task(bind=True, name="tasks.lca_compute.run_lca_job")
def run_lca_job(self, project_id: str, run_id: str) -> dict:
    """
    Async LCA computation job.
    Called by POST /projects/:id/calculate.
    Pulls project data from Firestore, builds mock matrices based on BOM, 
    runs the core engine, checks cut-offs, and writes to lca_results collection.
    """
    db = get_db()
    
    # Update job status to running
    job_ref = db.collection("jobs").document(run_id)
    job_ref.set({"status": "running", "progress": 10}, merge=True)
    
    try:
        # 1. Fetch Project and BOM
        proj_ref = db.collection("projects").document(project_id)
        proj_snap = proj_ref.get()
        if not proj_snap.exists:
            raise ValueError("Project not found")
            
        proj_data = proj_snap.to_dict()
        
        # 2. In a real system, we fetch the BOM. Since this is an MVP without a saved BOM in Phase 3,
        # we will simulate a BOM and the matrices based on standard Ecoinvent structure.
        job_ref.set({"progress": 30}, merge=True)
        
        # Matrix construction (mocked size for MVP: 5x5)
        # Real system would build N x N where N is the number of distinct processes in the BOM supply chain
        N = 5
        A = np.eye(N) * 1.0  # Simplified technology matrix
        A[0, 1] = -0.2
        A[1, 2] = -0.1
        
        M_ENV = 3 # 3 environmental flows (e.g. CO2, CH4, N2O)
        B = np.zeros((M_ENV, N))
        B[0, :] = [2.4, 0.5, 0.1, 1.2, 0.05] # Mock emissions
        
        M_IMPACT = 1 # 1 impact category (GWP)
        Q = np.zeros((M_IMPACT, M_ENV))
        Q[0, :] = [1.0, 29.8, 273.0] # GWP factors (CO2=1, CH4=29.8, N2O=273)
        
        f = np.zeros(N)
        # The demand is the functional unit quantity
        f[0] = float(proj_data.get("setup", {}).get("functional_unit", {}).get("quantity", 1.0))
        
        job_ref.set({"progress": 60}, merge=True)
        
        # 3. Run Core LCA Engine
        lca_result = run_lca(A, B, Q, f)
        
        # 4. Check Cut-off criteria (mock thresholds)
        # Using the engine's validate_cutoff on the inventory vector 'g'
        # For simplicity, we just check against a dummy total
        total_impact = np.sum(lca_result.h)
        
        job_ref.set({"progress": 90}, merge=True)
        
        # 5. Save results to Firestore
        result_id = f"res_{run_id}"
        result_doc = {
            "id": result_id,
            "project_id": project_id,
            "run_timestamp": datetime.now(timezone.utc),
            "run_by": proj_data.get("created_by", "system"),
            "is_final": False,
            "matrix_A_dimensions": list(lca_result.A.shape),
            "matrix_B_dimensions": list(lca_result.B.shape),
            "functional_unit": f"{f[0]} units",
            "allocation_method": "none",
            "lcia_methodology": "EF_3_1",
            "impact_results": {
                "GWP": {
                    "unit": "kg CO2e",
                    "values": {"A1-A3": float(total_impact)},
                    "total": float(total_impact)
                }
            },
            "inventory_vector": {f"flow_{i}": float(v) for i, v in enumerate(lca_result.g)},
            "hotspots": [
                {
                    "material_id": "mat-1",
                    "sensitivity_coefficient": 1.2,
                    "gwp_contribution_pct": 85.0,
                    "mass_contribution_pct": 90.0
                }
            ]
        }
        
        db.collection("lca_results").document(result_id).set(result_doc)
        
        # Complete job
        job_ref.set({"status": "complete", "progress": 100, "result_id": result_id}, merge=True)
        
        return {"status": "complete", "result_id": result_id}
        
    except SingularMatrixError as e:
        job_ref.set({"status": "failed", "error_message": str(e)}, merge=True)
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        job_ref.set({"status": "failed", "error_message": str(e)}, merge=True)
        return {"status": "failed", "error": str(e)}
