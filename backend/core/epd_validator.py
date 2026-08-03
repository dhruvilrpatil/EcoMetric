"""
backend/core/epd_validator.py

EPD Pre-Export Validation & Fabrication Detection Engine.
Enforces ISO 14025 / EN 15804+A2 data integrity rules.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import json

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
    If 3 or more values across different impact categories or modules share the
    same leading significant digits (mantissa), flag as a calculation bug / fabrication.
    """
    mantissa_counts: Dict[str, int] = {}
    numbers_to_check: List[float] = []

    impacts = result.get("environmental_impacts") or result.get("lca_by_module") or {}

    if isinstance(impacts, dict):
        for cat, val in impacts.items():
            if isinstance(val, dict):
                for mod, num in val.items():
                    if isinstance(num, (int, float)) and not isinstance(num, bool):
                        if abs(num) > 1e-9:
                            numbers_to_check.append(float(num))
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                if abs(val) > 1e-9:
                    numbers_to_check.append(float(val))

    for num in numbers_to_check:
        exp_str = f"{abs(num):.2e}"
        mantissa = exp_str.split("e")[0]
        mantissa_counts[mantissa] = mantissa_counts.get(mantissa, 0) + 1

    for mantissa, count in mantissa_counts.items():
        if count >= 3:
            msg = f"Repeated mantissa pattern detected: '{mantissa}' appeared {count} times across impact calculations."
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

    # Check 3: Material composition percentages (Rule 1.3)
    bom = project.get("bom") or []
    if not bom:
        errors.append("BOM Inventory is empty. At least one material input is required.")
    else:
        total_mass = sum(float(b.get("mass_kg") or 0) for b in bom)
        if total_mass <= 0:
            errors.append("Total BOM mass must be greater than 0 kg.")
        else:
            pct_sum = sum((float(b.get("mass_kg") or 0) / total_mass) * 100 for b in bom)
            if abs(pct_sum - 100.0) > 0.1:
                errors.append(f"Material composition sum error: Percentages sum to {pct_sum:.2f}%, expected 100% ± 0.1%.")

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
    if not transport:
        errors.append("Transportation Data Invalid: No transport legs entered. Please complete the Transportation step.")

    is_valid = len(errors) == 0
    return is_valid, errors
