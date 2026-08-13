"""
backend/api/projects.py

Full project CRUD + BOM management — backed by AWS RDS PostgreSQL.
Calculation trigger lives in api/calculation.py to avoid router conflicts.
"""

from __future__ import annotations
import uuid
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from core.db import get_db_cursor
from api.models import ProjectCreateRequest
from engine.lcia_matrix import build_indicator_matrix, get_epd11017_reference_matrix, LCIAMatrixResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─────────────────────────────────────────────────────────────
# POST /projects — Create a full project
# ─────────────────────────────────────────────────────────────

def _ensure_schema_columns(cursor):
    cursor.execute("""
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS product_description JSONB;
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS manufacturing_narrative JSONB;
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS certifications_structured JSONB;
    """)


@router.post("", status_code=201)
async def create_project(
    payload: ProjectCreateRequest,
    cursor=Depends(get_db_cursor),
    authorization: Optional[str] = Header(None),
):
    """Create a new EPD project. Returns project_id."""
    _ensure_schema_columns(cursor)
    project_id = str(uuid.uuid4())
    p = payload.product
    cfg = payload.lca_config
    nav = payload.narrative
    user_id = (authorization or "anonymous").removeprefix("Bearer ").strip()[:128] or "anonymous"
    project_name = p.product_name

    p_desc_json = json.dumps(nav.product_description.model_dump() if nav and nav.product_description else {})
    m_desc_json = json.dumps(nav.manufacturing_narrative.model_dump() if nav and nav.manufacturing_narrative else {})
    certs_json = json.dumps([c.model_dump() for c in nav.certifications_structured] if nav and nav.certifications_structured else [])

    try:
        cursor.execute("""
            INSERT INTO projects (
                id, user_id, project_name,
                product_name, product_sku, product_lifetime_years,
                product_configuration, manufacturer_name, manufacturing_country,
                functional_unit_quantity, functional_unit_unit,
                epd_standard, system_boundary, lcia_method, lci_database, active_modules,
                company_description, product_narrative, csi_division_code, certifications,
                pcr_reviewer_names, lca_conductor_name, verifier_name, verifier_email,
                program_operator_name, program_operator_address, program_operator_website, program_operator_logo_url,
                product_description, manufacturing_narrative, certifications_structured
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            project_id, user_id, project_name,
            p.product_name, p.product_sku, p.product_lifetime_years,
            p.product_configuration, p.manufacturer_name, p.manufacturing_country,
            p.functional_unit_quantity, p.functional_unit_unit,
            cfg.epd_standard.value, cfg.system_boundary, cfg.lcia_method.value,
            cfg.lci_database, [m.value for m in cfg.active_modules],
            nav.company_description if nav else None,
            nav.product_narrative if nav else None,
            nav.csi_division_code if nav else None,
            nav.certifications if nav else [],
            nav.pcr_reviewer_names if nav else [],
            nav.lca_conductor_name if nav else None,
            nav.verifier_name if nav else None,
            nav.verifier_email if nav else None,
            nav.program_operator.name if nav and nav.program_operator else None,
            nav.program_operator.address if nav and nav.program_operator else None,
            nav.program_operator.website if nav and nav.program_operator else None,
            nav.program_operator.logo_url if nav and nav.program_operator else None,
            p_desc_json, m_desc_json, certs_json
        ))

        for item in payload.bom:
            cursor.execute("""
                INSERT INTO bom_items (
                    id, project_id, material_name, mass_kg, unit,
                    lc_module, lci_dataset_id, data_quality, is_cut_off, cut_off_reason
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, item.material_name, item.mass_kg, item.unit,
                item.lc_module.value, item.lci_dataset_id, item.data_quality.value,
                item.is_cut_off, item.cut_off_reason
            ))

        if payload.manufacturing:
            m = payload.manufacturing
            cursor.execute("""
                INSERT INTO manufacturing_data (
                    id, project_id, manufacturing_location, electricity_use_kwh,
                    electricity_grid_region, product_mass_kg, manufacturing_energy_mj,
                    assembly_process_desc, other_energy_sources
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, m.manufacturing_location, m.electricity_use_kwh,
                m.electricity_grid_region, m.product_mass_kg, m.manufacturing_energy_mj,
                m.assembly_process_desc, json.dumps(m.other_energy_sources or {})
            ))

        for leg in payload.transport_legs:
            cursor.execute("""
                INSERT INTO transportation_data (
                    id, project_id, lc_module, vehicle_type, product_weight_kg,
                    fuel_type, road_distance_km, ocean_freight_km,
                    capacity_utilization_pct, lci_dataset_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, leg.lc_module.value, leg.vehicle_type.value,
                leg.product_weight_kg, leg.fuel_type, leg.road_distance_km, leg.ocean_freight_km,
                leg.capacity_utilization_pct, leg.lci_dataset_id
            ))

        if payload.installation:
            i = payload.installation
            cursor.execute("""
                INSERT INTO installation_data (
                    id, project_id, diesel_crane_liters, packaging_waste_kg,
                    packaging_material, installation_assumptions
                ) VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, i.diesel_crane_liters, i.packaging_waste_kg,
                i.packaging_material, i.installation_assumptions
            ))

        if payload.use_phase:
            u = payload.use_phase
            cursor.execute("""
                INSERT INTO use_phase_data (
                    id, project_id, annual_electricity_kwh, electricity_grid_region,
                    electricity_per_func_unit, refrigerant_type, refrigerant_charge_kg,
                    annual_leakage_rate_pct, refrigerant_gwp,
                    maintenance_cycles, replacement_cycles, maintenance_notes
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, u.annual_electricity_kwh, u.electricity_grid_region,
                u.electricity_per_func_unit, u.refrigerant_type, u.refrigerant_charge_kg,
                u.annual_leakage_rate_pct, u.refrigerant_gwp,
                u.maintenance_cycles, u.replacement_cycles, u.maintenance_notes
            ))

        if payload.end_of_life:
            e = payload.end_of_life
            cursor.execute("""
                INSERT INTO end_of_life_data (
                    id, project_id, waste_to_landfill_pct, waste_to_recycling_pct,
                    waste_to_incineration_pct, waste_to_reuse_pct, disposal_transport_km,
                    disposal_vehicle_type, refrigerant_recovery_rate_pct,
                    recycling_credit_included, energy_recovery_mj
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(uuid.uuid4()), project_id, e.waste_to_landfill_pct, e.waste_to_recycling_pct,
                e.waste_to_incineration_pct, e.waste_to_reuse_pct, e.disposal_transport_km,
                e.disposal_vehicle_type, e.refrigerant_recovery_rate_pct,
                e.recycling_credit_included, e.energy_recovery_mj
            ))

        return {"project_id": project_id, "status": "created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
# GET /projects — List all projects
# ─────────────────────────────────────────────────────────────

@router.get("")
async def list_projects(cursor=Depends(get_db_cursor)):
    """List all EPD projects with summary data."""
    cursor.execute("""
        SELECT
            p.id, p.product_name, p.epd_standard, p.system_boundary, p.status,
            p.functional_unit_quantity, p.functional_unit_unit,
            p.created_at,
            (SELECT COUNT(*) FROM bom_items b WHERE b.project_id = p.id) AS bom_count,
            (SELECT carbon_footprint_kg_co2e FROM lca_results r
             WHERE r.project_id = p.id ORDER BY r.run_timestamp DESC LIMIT 1) AS gwp_total
        FROM projects p
        ORDER BY p.created_at DESC
    """)
    return [dict(row) for row in cursor.fetchall()]


def _invalidate_project_calculation(cursor, project_id: str):
    """Invalidate finalized calculation results whenever project inputs are updated."""
    cursor.execute("UPDATE lca_results SET is_final = FALSE WHERE project_id = %s", (project_id,))
    cursor.execute("UPDATE projects SET status = 'in_progress', updated_at = NOW() WHERE id = %s", (project_id,))


# ─────────────────────────────────────────────────────────────
# GET /projects/{id} — Single project detail
# ─────────────────────────────────────────────────────────────

@router.get("/{project_id}")
async def get_project(project_id: str, cursor=Depends(get_db_cursor)):
    """Get full project detail including BOM, manufacturing, use_phase, end_of_life, and transport."""
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    project = dict(row)

    # Fetch BOM items
    cursor.execute("SELECT material_name, mass_kg, unit, lc_module, data_quality, is_cut_off FROM bom_items WHERE project_id = %s ORDER BY lc_module, sort_order", (project_id,))
    project["bom"] = [dict(r) for r in cursor.fetchall()]

    # Fetch manufacturing data
    cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
    mfg = cursor.fetchone()
    project["manufacturing"] = dict(mfg) if mfg else {}

    # Fetch transport legs
    cursor.execute("SELECT * FROM transportation_data WHERE project_id = %s", (project_id,))
    project["transport"] = [dict(r) for r in cursor.fetchall()]

    # Fetch use phase data
    cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
    use = cursor.fetchone()
    project["use_phase"] = dict(use) if use else {}

    # Fetch end of life data
    cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
    eol = cursor.fetchone()
    project["end_of_life"] = dict(eol) if eol else {}

    # Fetch final LCA result if active
    cursor.execute("SELECT * FROM lca_results WHERE project_id = %s AND is_final = TRUE ORDER BY run_timestamp DESC LIMIT 1", (project_id,))
    res = cursor.fetchone()
    if res:
        res_dict = dict(res)
        project["gwp_total"] = res_dict.get("carbon_footprint_kg_co2e")
        project["lca_results"] = res_dict
    else:
        project["gwp_total"] = None
        project["lca_results"] = None

    return project


# ─────────────────────────────────────────────────────────────
# PUT /projects/{id} — Update project setup
# ─────────────────────────────────────────────────────────────

@router.put("/{project_id}", status_code=200)
async def update_project(
    project_id: str,
    payload: ProjectCreateRequest,
    cursor=Depends(get_db_cursor),
):
    """Update project setup data."""
    _ensure_schema_columns(cursor)
    cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")
        
    p = payload.product
    cfg = payload.lca_config
    nav = payload.narrative

    p_desc_json = json.dumps(nav.product_description.model_dump() if nav and nav.product_description else {})
    m_desc_json = json.dumps(nav.manufacturing_narrative.model_dump() if nav and nav.manufacturing_narrative else {})
    certs_json = json.dumps([c.model_dump() for c in nav.certifications_structured] if nav and nav.certifications_structured else [])

    cursor.execute("""
        UPDATE projects SET
            product_name = %s, product_sku = %s, product_lifetime_years = %s,
            product_configuration = %s, manufacturer_name = %s, manufacturing_country = %s,
            functional_unit_quantity = %s, functional_unit_unit = %s,
            epd_standard = %s, system_boundary = %s, lcia_method = %s, lci_database = %s, active_modules = %s,
            company_description = %s, product_narrative = %s, csi_division_code = %s, certifications = %s,
            pcr_reviewer_names = %s, lca_conductor_name = %s, verifier_name = %s, verifier_email = %s,
            program_operator_name = %s, program_operator_address = %s, program_operator_website = %s, program_operator_logo_url = %s,
            product_description = %s, manufacturing_narrative = %s, certifications_structured = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (
        p.product_name, p.product_sku, p.product_lifetime_years,
        p.product_configuration, p.manufacturer_name, p.manufacturing_country,
        p.functional_unit_quantity, p.functional_unit_unit,
        cfg.epd_standard.value, cfg.system_boundary, cfg.lcia_method.value,
        cfg.lci_database, [m.value for m in cfg.active_modules],
        nav.company_description if nav else None,
        nav.product_narrative if nav else None,
        nav.csi_division_code if nav else None,
        nav.certifications if nav else [],
        nav.pcr_reviewer_names if nav else [],
        nav.lca_conductor_name if nav else None,
        nav.verifier_name if nav else None,
        nav.verifier_email if nav else None,
        nav.program_operator.name if nav and nav.program_operator else None,
        nav.program_operator.address if nav and nav.program_operator else None,
        nav.program_operator.website if nav and nav.program_operator else None,
        nav.program_operator.logo_url if nav and nav.program_operator else None,
        p_desc_json, m_desc_json, certs_json,
        project_id
    ))
    _invalidate_project_calculation(cursor, project_id)
    return {"project_id": project_id, "status": "updated"}


# ─────────────────────────────────────────────────────────────
# DELETE /projects/{id} — Delete project and all associated data
# ─────────────────────────────────────────────────────────────

@router.delete("/{project_id}", status_code=200)
async def delete_project(
    project_id: str,
    cursor=Depends(get_db_cursor),
):
    """Delete a project and all associated records across all modules."""
    cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    # Cascade delete all related tables
    related_tables = [
        "bom_items",
        "manufacturing_data",
        "transportation_data",
        "transport_scenario",
        "installation_data",
        "installation_scenario",
        "installation_packaging",
        "installation_materials",
        "use_phase_data",
        "end_of_life_data",
        "lca_results",
        "nlp_audit_logs",
        "nlp_feedback",
    ]
    for table in related_tables:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE project_id = %s", (project_id,))
        except Exception:
            pass

    cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    return {"project_id": project_id, "status": "deleted"}



# ─────────────────────────────────────────────────────────────
# GET /projects/{id}/bom — Get BOM items
# ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/bom")
async def get_bom(project_id: str, cursor=Depends(get_db_cursor)):
    """Get all BOM items for a project."""
    cursor.execute(
        "SELECT * FROM bom_items WHERE project_id = %s ORDER BY lc_module, sort_order",
        (project_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────────────────────────
# POST /projects/{id}/bom — Add / replace BOM items
# ─────────────────────────────────────────────────────────────

class BomItemPayload(BaseModel):
    material_name: str
    mass_kg: float = Field(..., gt=0)
    unit: str = "kg"
    lc_module: str = "A1"
    lci_dataset_id: Optional[str] = None
    data_quality: str = "SECONDARY"
    is_cut_off: bool = False
    cut_off_reason: Optional[str] = None


@router.post("/{project_id}/bom", status_code=201)
async def add_bom_items(
    project_id: str,
    items: List[BomItemPayload],
    cursor=Depends(get_db_cursor),
):
    """Replace all BOM items for a project with the provided list."""
    cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete existing BOM and replace
    cursor.execute("DELETE FROM bom_items WHERE project_id = %s", (project_id,))
    for item in items:
        cursor.execute("""
            INSERT INTO bom_items (
                id, project_id, material_name, mass_kg, unit,
                lc_module, lci_dataset_id, data_quality, is_cut_off, cut_off_reason
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            str(uuid.uuid4()), project_id, item.material_name, item.mass_kg,
            item.unit, item.lc_module, item.lci_dataset_id, item.data_quality,
            item.is_cut_off, item.cut_off_reason
        ))

    # Update project status and invalidate prior calculation score
    _invalidate_project_calculation(cursor, project_id)
    return {"saved": len(items), "project_id": project_id}


# ─────────────────────────────────────────────────────────────
# GET /projects/{id}/results — Fetch computed LCA results
# ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/results")
async def get_results(
    project_id: str,
    run_id: Optional[str] = None,
    methodology: Optional[str] = "EN_15804_A2",
    cursor=Depends(get_db_cursor),
):
    """Retrieve the most recent LCA results for a project, including full LCIA Matrix."""
    sql = "SELECT * FROM lca_results WHERE project_id = %s AND is_final = TRUE"
    params: list = [project_id]
    if run_id:
        sql += " AND run_id = %s"
        params.append(run_id)
    sql += " ORDER BY run_timestamp DESC LIMIT 1"

    cursor.execute(sql, params)
    row = cursor.fetchone()
    if not row:
        return JSONResponse(status_code=200, content=None)
    
    res_dict = dict(row)

    # Fetch project context
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    p_row = cursor.fetchone()
    project_dict = dict(p_row) if p_row else {}

    # Fetch BOM items
    cursor.execute("SELECT material_name, mass_kg, lc_module FROM bom_items WHERE project_id = %s", (project_id,))
    bom_rows = cursor.fetchall()
    project_dict["bom"] = [dict(b) for b in bom_rows] if bom_rows else []

    # Fetch parameters (manufacturing, use_phase, end_of_life)
    cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
    mfg = cursor.fetchone()
    project_dict["manufacturing"] = dict(mfg) if mfg else {}

    cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
    use = cursor.fetchone()
    project_dict["use_phase"] = dict(use) if use else {}

    cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
    eol = cursor.fetchone()
    project_dict["end_of_life"] = dict(eol) if eol else {}

    # Generate multi-indicator LCIA matrix
    matrix = build_indicator_matrix(res_dict, project_dict, methodology or "EN_15804_A2")
    res_dict["matrix"] = matrix.model_dump()

    return res_dict


@router.get("/{project_id}/matrix")
async def get_project_matrix(
    project_id: str,
    methodology: Optional[str] = "EN_15804_A2",
    cursor=Depends(get_db_cursor),
):
    """Retrieve full LCIA Matrix for a project, with fallback to EPD11017 benchmark if uncalculated."""
    cursor.execute(
        "SELECT * FROM lca_results WHERE project_id = %s AND is_final = TRUE ORDER BY run_timestamp DESC LIMIT 1",
        (project_id,)
    )
    row = cursor.fetchone()
    if not row:
        # Provide verified reference benchmark for preview mode
        return get_epd11017_reference_matrix(methodology or "EN_15804_A2").model_dump()

    res_dict = dict(row)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    p_row = cursor.fetchone()
    project_dict = dict(p_row) if p_row else {}

    cursor.execute("SELECT material_name, mass_kg, lc_module FROM bom_items WHERE project_id = %s", (project_id,))
    bom_rows = cursor.fetchall()
    project_dict["bom"] = [dict(b) for b in bom_rows] if bom_rows else []

    cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
    mfg = cursor.fetchone()
    project_dict["manufacturing"] = dict(mfg) if mfg else {}

    cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
    use = cursor.fetchone()
    project_dict["use_phase"] = dict(use) if use else {}

    cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
    eol = cursor.fetchone()
    project_dict["end_of_life"] = dict(eol) if eol else {}

    matrix = build_indicator_matrix(res_dict, project_dict, methodology or "EN_15804_A2")
    return matrix.model_dump()


# ─────────────────────────────────────────────────────────────
# GET /projects/{id}/parameters & POST /projects/{id}/parameters
# ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/parameters")
async def get_project_parameters(project_id: str, cursor=Depends(get_db_cursor)):
    """Fetch manufacturing, use phase, and end-of-life parameters for a project."""
    cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
    mfg = cursor.fetchone()
    
    cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
    use = cursor.fetchone()
    
    cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
    eol = cursor.fetchone()
    
    return {
        "manufacturing": dict(mfg) if mfg else {},
        "use_phase": dict(use) if use else {},
        "end_of_life": dict(eol) if eol else {},
    }


@router.post("/{project_id}/parameters")
async def save_project_parameters(project_id: str, payload: dict, cursor=Depends(get_db_cursor)):
    """Upsert manufacturing, use phase, and end-of-life parameters for a project."""
    mfg = payload.get("manufacturing") or {}
    use = payload.get("use_phase") or {}
    eol = payload.get("end_of_life") or {}
    
    if mfg:
        cursor.execute("""
            INSERT INTO manufacturing_data (
                id, project_id, electricity_use_kwh, electricity_grid_region, manufacturing_energy_mj, assembly_process_desc
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                electricity_use_kwh = EXCLUDED.electricity_use_kwh,
                electricity_grid_region = EXCLUDED.electricity_grid_region,
                manufacturing_energy_mj = EXCLUDED.manufacturing_energy_mj,
                assembly_process_desc = EXCLUDED.assembly_process_desc
        """, (
            str(uuid.uuid4()), project_id,
            float(mfg.get("electricity_use_kwh") or 0),
            mfg.get("electricity_grid_region") or "GLO",
            float(mfg.get("manufacturing_energy_mj") or 0),
            mfg.get("assembly_process_desc") or ""
        ))
        
    if use:
        cursor.execute("""
            INSERT INTO use_phase_data (
                id, project_id, annual_electricity_kwh, electricity_grid_region,
                refrigerant_type, refrigerant_charge_kg, refrigerant_gwp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                annual_electricity_kwh = EXCLUDED.annual_electricity_kwh,
                electricity_grid_region = EXCLUDED.electricity_grid_region,
                refrigerant_type = EXCLUDED.refrigerant_type,
                refrigerant_charge_kg = EXCLUDED.refrigerant_charge_kg,
                refrigerant_gwp = EXCLUDED.refrigerant_gwp
        """, (
            str(uuid.uuid4()), project_id,
            float(use.get("annual_electricity_kwh") or 0),
            use.get("electricity_grid_region") or "US",
            use.get("refrigerant_type") or "R-1233zd(E)",
            float(use.get("refrigerant_charge_kg") or 0),
            float(use.get("refrigerant_gwp") or 1.0)
        ))
        
    if eol:
        cursor.execute("""
            INSERT INTO end_of_life_data (
                id, project_id, waste_to_landfill_pct, waste_to_recycling_pct,
                waste_to_incineration_pct, waste_to_reuse_pct, refrigerant_recovery_rate_pct
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                waste_to_landfill_pct = EXCLUDED.waste_to_landfill_pct,
                waste_to_recycling_pct = EXCLUDED.waste_to_recycling_pct,
                waste_to_incineration_pct = EXCLUDED.waste_to_incineration_pct,
                waste_to_reuse_pct = EXCLUDED.waste_to_reuse_pct,
                refrigerant_recovery_rate_pct = EXCLUDED.refrigerant_recovery_rate_pct
        """, (
            str(uuid.uuid4()), project_id,
            float(eol.get("waste_to_landfill_pct") or 30.0),
            float(eol.get("waste_to_recycling_pct") or 60.0),
            float(eol.get("waste_to_incineration_pct") or 10.0),
            float(eol.get("waste_to_reuse_pct") or 0.0),
            float(eol.get("refrigerant_recovery_rate_pct") or 95.0)
        ))
        
    _invalidate_project_calculation(cursor, project_id)
    return {"status": "success", "project_id": project_id}
