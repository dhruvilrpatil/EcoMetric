"""
backend/engine/functional_unit_details.py

Computes and renders the "Functional Unit Details" table for the platform,
derived dynamically from the BOM (material_inventory) total mass and the project's
functional unit quantity.
"""

from dataclasses import dataclass
from typing import List, Optional
from engine.material_composition import MaterialInventoryItem, build_material_composition_table


class FunctionalUnitDetailsError(Exception):
    """Raised when the functional unit conversion factor cannot be computed."""
    pass


@dataclass
class FunctionalUnitDetails:
    functional_unit_description: str      # e.g. "1 ton chilling capacity"
    unit_label: str                        # e.g. "650 ton" — the specific configuration label
    mass_of_one_delivered_product_kg: float
    conversion_factor_kg_per_fu: float
    conversion_factor_unit: str            # e.g. "kg/ton of chilling capacity"


def compute_functional_unit_details(
    materials: List[MaterialInventoryItem],
    functional_unit_description: str,
    functional_unit_quantity: float,
    functional_unit_measure_name: str,     # e.g. "ton of chilling capacity"
    configuration_label: str,              # e.g. "650 ton" — identifies product configuration
) -> FunctionalUnitDetails:
    """
    Compute the Functional Unit Details table values. The conversion factor is
    NEVER user-entered — it is always derived from the BOM total mass and the
    declared functional unit quantity, so it stays automatically correct if the
    BOM changes after initial entry.
    """
    if functional_unit_quantity <= 0:
        raise FunctionalUnitDetailsError(
            f"Functional unit quantity must be positive; got {functional_unit_quantity}."
        )

    if not materials:
        raise FunctionalUnitDetailsError(
            "Cannot compute functional unit details: material inventory is empty. "
            "Complete the Bill of Materials (Step 2) before this table can be generated."
        )

    total_mass_kg = sum(item.mass_kg for item in materials)

    if total_mass_kg <= 0:
        raise FunctionalUnitDetailsError(
            "Total BOM mass is zero or negative; check material inventory entries."
        )

    conversion_factor = total_mass_kg / functional_unit_quantity

    return FunctionalUnitDetails(
        functional_unit_description=functional_unit_description,
        unit_label=configuration_label,
        mass_of_one_delivered_product_kg=round(total_mass_kg, 2),
        conversion_factor_kg_per_fu=round(conversion_factor, 4),
        conversion_factor_unit=f"kg/{functional_unit_measure_name}",
    )


def render_functional_unit_details_html(details: FunctionalUnitDetails) -> str:
    """
    Render the Functional Unit Details table matching the reference EPD's exact
    visual structure: dark navy header band, configuration label as column header,
    Functional Unit row merged across the value+unit columns, remaining rows as
    label | value | unit.
    """
    return f"""
    <div class="epd-section">
        <p class="epd-table-caption">Table: Functional Unit Details</p>
        <table class="epd-fu-details-table">
            <thead>
                <tr>
                    <th class="fu-label-col"></th>
                    <th class="fu-header-value">{details.unit_label}</th>
                    <th class="fu-header-unit">Unit</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="fu-row-label"><strong>Functional Unit</strong></td>
                    <td class="fu-merged-value" colspan="2">
                        {details.functional_unit_description}
                    </td>
                </tr>
                <tr>
                    <td class="fu-row-label">
                        <strong>Mass of one delivered product</strong>
                    </td>
                    <td class="fu-value">{details.mass_of_one_delivered_product_kg:.0f}</td>
                    <td class="fu-unit">kg</td>
                </tr>
                <tr>
                    <td class="fu-row-label">
                        <strong>Conversion factor (kg per Functional Unit)</strong>
                    </td>
                    <td class="fu-value">{details.conversion_factor_kg_per_fu:.1f}</td>
                    <td class="fu-unit">{details.conversion_factor_unit}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
