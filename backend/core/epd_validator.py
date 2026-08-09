"""
backend/core/epd_validator.py

EPD Pre-Export Validation & Fabrication Detection Engine.
Enforces ISO 14025 / EN 15804+A2 data integrity rules.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import json

from engine.material_composition import (
    MaterialInventoryItem,
    build_material_composition_table,
    MaterialCompositionError,
)

KNOWN_FILLER_PHRASES = [
    "transport details for delivery",
    "manufacturing occurs at designated facility",
    "this section...",
    "this product...",
    "details below...",
    "lorem ipsum",
    "placeholder",
    "to be filled",
    "tbd",
]


def check_fabrication_patterns(result: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Rule 1.2: Detect and reject repeated-pattern fabrication.
    Checks for suspicious fabrication patterns, such as multiple identical exact
    non-zero numerical values (e.g., placeholder values like 1.2345 repeated across categories).
    """
    exact_counts: Dict[float, int] = {}
    numbers_to_check: List[float] = []

    impacts = result.get("environmental_impacts") or result.get("lca_by_module") or {}

    if isinstance(impacts, dict):
        for cat, val in impacts.items():
            if isinstance(val, dict):
                for mod, num in val.items():
                    if isinstance(num, (int, float)) and not isinstance(num, bool):
                        if abs(num) > 1e-9:
                            numbers_to_check.append(round(float(num), 6))
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                if abs(val) > 1e-9:
                    numbers_to_check.append(round(float(val), 6))

    for num in numbers_to_check:
        exact_counts[num] = exact_counts.get(num, 0) + 1

    for num, count in exact_counts.items():
        if count >= 8 and not (num in (0.0, 1.0, 10.0)):
            msg = f"Repeated exact value pattern detected: '{num}' appeared {count} times across impact calculations."
            return True, msg

    return False, None


def validate_epd_export_completeness(project: Dict[str, Any], result: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Part 6: Full validation pass run before PDF export.
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    if not result:
        errors.append("No finalized LCA calculation result found. Run calculation first.")
        return False, errors

    # Check 1: Fabrication detection (Rule 1.2)
    is_fabricated, fab_msg = check_fabrication_patterns(result)
    if is_fabricated:
        errors.append(f"Fabrication/Repeated Pattern Check Failed: {fab_msg}")

    # Check 2: Denylist filler phrases (Rule 1.5)
    project_str = json.dumps(project, default=str).lower()
    for phrase in KNOWN_FILLER_PHRASES:
        if phrase in project_str:
            errors.append(f"Placeholder text detected: Found '{phrase}' in project narrative fields.")

    # Check 3: Material composition percentages (Rule 1.3) via engine
    bom = project.get("bom") or []
    mfg = project.get("manufacturing") or {}
    fu_description = project.get("functional_unit_description") or f"{project.get('functional_unit_quantity') or 1} {project.get('functional_unit_unit') or 'unit'}"
    total_bom_mass = sum(float(item.get("mass_kg") or item.get("quantity") or 0) for item in bom)
    conversion_factor = float(mfg.get("conversion_factor_kg_per_fu") or total_bom_mass or 1.0)

    try:
        materials = [
            MaterialInventoryItem(
                material_name=doc.get("material_name") or doc.get("name") or "Unknown Material",
                mass_kg=float(doc.get("mass_kg") or doc.get("quantity") or 0),
                material_category=doc.get("material_category"),
            )
            for doc in bom
        ]
        build_material_composition_table(
            materials=materials,
            functional_unit_description=fu_description,
            conversion_factor_kg_per_fu=conversion_factor,
        )
    except MaterialCompositionError as e:
        errors.append(f"Material Composition Error: {str(e)}")

    # Compressed air double-counting check
    if float(mfg.get("compressed_air_energy_mj") or 0) > 0 and not mfg.get("compressed_air_already_in_electricity"):
        errors.append("Compressed air energy specified without confirmation that it is excluded from electricity (double-counting risk).")

    # Check 4: Required narrative fields (Part 4)
    if not project.get("company_description") or len(str(project.get("company_description")).strip()) < 5:
        errors.append("Missing required field: Company Description in Project Setup.")

    p_desc = project.get("product_description") or {}
    if isinstance(p_desc, str):
        try:
            p_desc = json.loads(p_desc)
        except Exception:
            p_desc = {}

    if not isinstance(p_desc, dict) or not p_desc.get("operating_principle"):
        if not project.get("product_narrative") or len(str(project.get("product_narrative")).strip()) < 5:
            errors.append("Missing required field: Product Operating Principle in Project Setup.")

    # Check 5: Non-zero operational energy & EOL routing (Rule 1.4)
    use = project.get("use_phase") or {}
    annual_kwh = float(use.get("annual_electricity_kwh") or 0)
    if annual_kwh <= 0:
        errors.append("Operational Energy (Module B6) Invalid: Annual electricity demand is 0 kWh.")

    eol = project.get("end_of_life") or {}
    landfill = float(eol.get("waste_to_landfill_pct") or 0)
    recycling = float(eol.get("waste_to_recycling_pct") or 0)
    incineration = float(eol.get("waste_to_incineration_pct") or 0)
    reuse = float(eol.get("waste_to_reuse_pct") or 0)
    if (landfill + recycling + incineration + reuse) <= 0:
        errors.append("End-of-Life Routing Invalid: All routing percentages are 0%. Please configure EOL scenarios.")

    # Check 6: Transportation module presence
    transport = project.get("transport") or project.get("transport_legs") or []
    t_data = project.get("transportation_data")
    if isinstance(t_data, str):
        try:
            t_data = json.loads(t_data)
        except Exception:
            t_data = None

    has_transport = bool(
        (isinstance(transport, list) and len(transport) > 0) or
        (isinstance(t_data, dict) and (t_data.get("a4_segment") or (isinstance(t_data.get("a2_segments"), list) and len(t_data.get("a2_segments")) > 0)))
    )

    if not has_transport:
        errors.append("Transportation Data Invalid: No transport legs entered. Please complete the Transportation step.")

    is_valid = len(errors) == 0
    return is_valid, errors
