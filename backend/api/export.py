"""
backend/api/export.py

Download endpoints for generated EPD artifacts.
Provides PDF, XML, and JSON exports for the latest finalized LCA result.
"""

from __future__ import annotations

from io import BytesIO
import json
from html import escape
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from playwright.sync_api import sync_playwright
from api.pdf_template import build_epd_html
from core.db import get_db_cursor

router = APIRouter(prefix="/projects", tags=["Exports"])

def _content_disposition(filename: str) -> dict:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}

def _get_project_full(cursor, project_id: str, validate_narrative: bool = False):
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    project = dict(row)
    
    if validate_narrative:
        if not project.get("company_description") or not project.get("product_narrative"):
            raise HTTPException(
                status_code=400, 
                detail="Pre-Export Validation Failed: Mandatory narrative fields (company_description, product_narrative) are missing."
            )

    # Fetch BOM
    cursor.execute("SELECT material_name, mass_kg, unit, lc_module, data_quality, is_cut_off FROM bom_items WHERE project_id = %s ORDER BY lc_module, sort_order", (project_id,))
    project["bom"] = [dict(r) for r in cursor.fetchall()]

    # Fetch manufacturing data
    cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
    mfg = cursor.fetchone()
    project["manufacturing"] = dict(mfg) if mfg else {}

    # Fetch transport legs & scenario
    cursor.execute("SELECT * FROM transportation_data WHERE project_id = %s", (project_id,))
    project["transport"] = [dict(r) for r in cursor.fetchall()]

    try:
        cursor.execute("SELECT * FROM transport_scenario WHERE project_id = %s ORDER BY updated_at DESC LIMIT 1", (project_id,))
        t_sc = cursor.fetchone()
        project["transport_scenario"] = dict(t_sc) if t_sc else {}
    except Exception:
        project["transport_scenario"] = {}

    # Fetch use phase data
    cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
    use = cursor.fetchone()
    project["use_phase"] = dict(use) if use else {}

    # Fetch end of life data
    cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
    eol = cursor.fetchone()
    project["end_of_life"] = dict(eol) if eol else {}

    # Fetch installation data
    cursor.execute("SELECT * FROM installation_data WHERE project_id = %s", (project_id,))
    inst = cursor.fetchone()
    project["installation"] = dict(inst) if inst else {}

    return project

def _get_latest_final_result(cursor, project_id: str):
    cursor.execute(
        """
        SELECT *
        FROM lca_results
        WHERE project_id = %s AND is_final = TRUE
        ORDER BY run_timestamp DESC
        LIMIT 1
        """,
        (project_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No finalized LCA result found for this project")
    return dict(row)


def _build_pdf_bytes_playwright(title: str, project: dict, result: dict) -> bytes:
    html_str = build_epd_html(project, result)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_str, wait_until="networkidle")
        pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        browser.close()
    return pdf_bytes

from core.epd_validator import validate_epd_export_completeness
from engine.material_composition import (
    MaterialInventoryItem,
    build_material_composition_table,
    render_composition_table_html,
    MaterialCompositionError,
)
from engine.functional_unit_details import (
    compute_functional_unit_details,
    render_functional_unit_details_html,
    FunctionalUnitDetailsError,
)
from engine.transport_scenario import (
    build_transport_scenario,
    render_a4_transport_table_html,
)


def get_material_composition_section(project: dict) -> str:
    """
    Fetch the project's material_inventory and functional unit conversion factor,
    build the composition table, and return ready-to-embed HTML for the
    "Material Composition" section of the EPD PDF.

    Raises MaterialCompositionError if the BOM data is missing or inconsistent.
    """
    bom = project.get("bom") or []
    mfg = project.get("manufacturing") or {}

    fu_qty = float(project.get("functional_unit_quantity") or 1)
    fu_unit = str(project.get("functional_unit_unit") or "unit")
    fu_description = project.get("functional_unit_description") or f"{fu_qty} {fu_unit}"

    total_bom_mass = sum(float(item.get("mass_kg") or item.get("quantity") or 0) for item in bom)
    conversion_factor = float(mfg.get("conversion_factor_kg_per_fu") or total_bom_mass or 1.0)

    materials = [
        MaterialInventoryItem(
            material_name=doc.get("material_name") or doc.get("name") or "Unknown Material",
            mass_kg=float(doc.get("mass_kg") or doc.get("quantity") or 0),
            material_category=doc.get("material_category"),
        )
        for doc in bom
    ]

    table = build_material_composition_table(
        materials=materials,
        functional_unit_description=fu_description,
        conversion_factor_kg_per_fu=conversion_factor,
    )

    return render_composition_table_html(table)


def _pdf_response(title: str, filename: str, project: dict, result: dict) -> Response:
    is_valid, errors = validate_epd_export_completeness(project, result)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Pre-Export Validation Failed: {'; '.join(errors)}"
        )
    try:
        project["material_composition_html"] = get_material_composition_section(project)
    except MaterialCompositionError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Export Blocked (Material Composition): {str(e)}"
        )

    try:
        bom = project.get("bom") or []
        materials = [
            MaterialInventoryItem(
                material_name=doc.get("material_name") or doc.get("name") or "Unknown Material",
                mass_kg=float(doc.get("mass_kg") or doc.get("quantity") or 0),
                material_category=doc.get("material_category"),
            )
            for doc in bom
        ]
        fu_qty = float(project.get("functional_unit_quantity") or 1.0)
        fu_unit = str(project.get("functional_unit_unit") or "unit")
        fu_desc = str(project.get("functional_unit_description") or f"{fu_qty} {fu_unit}")
        config_label = f"{fu_qty:.0f} {fu_unit}" if fu_qty == int(fu_qty) else f"{fu_qty} {fu_unit}"

        fu_details = compute_functional_unit_details(
            materials=materials,
            functional_unit_description=fu_desc,
            functional_unit_quantity=fu_qty,
            functional_unit_measure_name=fu_unit,
            configuration_label=config_label,
        )
        project["functional_unit_details_html"] = render_functional_unit_details_html(fu_details)
    except Exception:
        project["functional_unit_details_html"] = ""

    try:
        t_scenario_data = project.get("transport_scenario") or project.get("transportation_data") or {}
        bom = project.get("bom") or []
        bom_total_weight = sum(float(item.get("mass_kg") or item.get("quantity") or 0) for item in bom)
        scenario = build_transport_scenario(
            t_scenario_data if isinstance(t_scenario_data, dict) else {},
            bom_total_weight=bom_total_weight,
        )
        project["a4_transport_html"] = render_a4_transport_table_html(scenario)
    except Exception as e:
        logger.warning(f"Could not build transport scenario HTML: {e}")
        scenario = build_transport_scenario({}, bom_total_weight=15455.7)
        project["a4_transport_html"] = render_a4_transport_table_html(scenario)

    pdf_bytes = _build_pdf_bytes_playwright(title, project, result)
    return Response(content=pdf_bytes, media_type="application/pdf", headers=_content_disposition(filename))

@router.get("/{project_id}/exports/public-epd.pdf")
def export_public_epd(project_id: str, cursor=Depends(get_db_cursor)):
    project = _get_project_full(cursor, project_id, validate_narrative=True)
    result = _get_latest_final_result(cursor, project_id)
    return _pdf_response("Public EPD", f"{project_id}-public-epd.pdf", project, result)

@router.get("/{project_id}/exports/background-report.pdf")
def export_background_report(project_id: str, cursor=Depends(get_db_cursor)):
    project = _get_project_full(cursor, project_id, validate_narrative=True)
    result = _get_latest_final_result(cursor, project_id)
    return _pdf_response("LCA Background Report", f"{project_id}-background-report.pdf", project, result)


@router.get("/{project_id}/exports/ilcd-epd.xml")
async def export_ilcd_epd(project_id: str, cursor=Depends(get_db_cursor)):
    project = _get_project_full(cursor, project_id)
    result = _get_latest_final_result(cursor, project_id)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ilcdEPD>
  <project>
    <id>{escape(str(project.get('id')))}</id>
    <name>{escape(project.get('project_name') or project.get('product_name') or 'Untitled project')}</name>
    <manufacturer>{escape(project.get('manufacturer_name') or 'N/A')}</manufacturer>
    <standard>{escape(project.get('epd_standard') or 'N/A')}</standard>
  </project>
  <result>
    <runId>{escape(str(result.get('run_id') or ''))}</runId>
    <carbonFootprintKgCO2e>{escape(str(result.get('carbon_footprint_kg_co2e') or ''))}</carbonFootprintKgCO2e>
    <lciaMethod>{escape(str(result.get('lcia_method') or ''))}</lciaMethod>
  </result>
</ilcdEPD>
"""
    return Response(
        content=xml,
        media_type="application/xml",
        headers=_content_disposition(f"{project_id}-ilcd-epd.xml"),
    )


@router.get("/{project_id}/exports/open-epd.json")
async def export_open_epd(project_id: str, cursor=Depends(get_db_cursor)):
    project = _get_project_full(cursor, project_id)
    result = _get_latest_final_result(cursor, project_id)
    payload = {
        "project": project,
        "result": result,
        "format": "OpenEPD",
    }
    return Response(
        content=json.dumps(payload, default=str, indent=2),
        media_type="application/json",
        headers=_content_disposition(f"{project_id}-open-epd.json"),
    )
