"""
Converts a project's raw Bill of Materials (material_inventory) into a
"Material Composition per Functional Unit" table, matching the structure
used in published EPDs (e.g. Carrier EPD11017 Table 3):

  Table A — Material Composition per Functional Unit (mass values)
  Table B — Contribution to Total Material Composition (percentages)

Both tables are derived from the same source data and must always be
internally consistent (percentages sum to 100% +/- rounding tolerance).
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List


class MaterialCompositionError(Exception):
    """Raised when the BOM cannot be converted into a valid composition table."""
    pass


@dataclass
class MaterialInventoryItem:
    """Mirrors the material_inventory schema already used by the platform."""
    material_name: str
    mass_kg: float
    material_category: Optional[str] = None  # metal_ferrous, plastic, refrigerant, etc.


@dataclass
class MaterialCompositionRow:
    material_name: str
    mass_kg: float
    mass_per_functional_unit_kg: float
    percentage_of_total: float


@dataclass
class MaterialCompositionTable:
    functional_unit_description: str      # e.g. "1 ton chilling capacity"
    conversion_factor_kg_per_fu: float     # kg of product per 1 functional unit
    rows: List[MaterialCompositionRow]
    total_mass_kg: float
    total_percentage: float                # should always be 100.0 (+/- tolerance)


def _round_half_up(value: float, decimals: int = 2) -> float:
    """
    Standard rounding (not banker's rounding) so displayed percentages behave the
    way a reader expects and match the convention used in published EPD tables.
    """
    quant = Decimal("1." + "0" * decimals)
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))


def build_material_composition_table(
    materials: List[MaterialInventoryItem],
    functional_unit_description: str,
    conversion_factor_kg_per_fu: float,
    percentage_tolerance: float = 0.1,
) -> MaterialCompositionTable:
    """
    Convert a raw BOM into the two-part Material Composition table structure.

    Args:
        materials: raw material_inventory rows already stored for the project.
        functional_unit_description: human-readable FU string, e.g. "1 ton chilling capacity".
        conversion_factor_kg_per_fu: total product mass expressed as kg per 1 functional unit
            (this is the same "Conversion factor (kg per Functional Unit)" value already
            present in the platform's Functional Unit Details table).
        percentage_tolerance: acceptable drift from 100% due to rounding, in percentage points.

    Returns:
        MaterialCompositionTable ready to hand directly to the PDF renderer.

    Raises:
        MaterialCompositionError: if the BOM is empty, contains non-positive mass values,
            or the resulting percentages fail the 100% consistency check. This function
            never silently produces a table that would misrepresent the product's
            material makeup — callers must handle this exception by blocking export,
            per the platform's existing pre-export validation pattern.
    """
    if not materials:
        raise MaterialCompositionError(
            "Material inventory is empty. At least one material is required to "
            "generate a Material Composition table."
        )

    if conversion_factor_kg_per_fu <= 0:
        raise MaterialCompositionError(
            f"Invalid conversion factor: {conversion_factor_kg_per_fu} kg per functional "
            "unit. This must be a positive value derived from the product's mass and "
            "declared functional unit."
        )

    for item in materials:
        if item.mass_kg <= 0:
            raise MaterialCompositionError(
                f"Material '{item.material_name}' has non-positive mass "
                f"({item.mass_kg} kg). Every BOM entry must have a positive mass "
                "before a composition table can be generated."
            )

    total_mass_kg = sum(item.mass_kg for item in materials)

    # Scale factor: how much of the "per one delivered product" mass corresponds
    # to one functional unit. This mirrors the existing platform pattern where
    # BOM mass is captured per delivered product, then normalized to the FU basis
    # using the same conversion factor already computed in Functional Unit Details.
    per_fu_scale = conversion_factor_kg_per_fu / total_mass_kg if total_mass_kg > 0 else 0

    rows: List[MaterialCompositionRow] = []
    for item in materials:
        mass_per_fu = item.mass_kg * per_fu_scale
        percentage = (item.mass_kg / total_mass_kg) * 100 if total_mass_kg > 0 else 0

        rows.append(
            MaterialCompositionRow(
                material_name=item.material_name,
                mass_kg=_round_half_up(item.mass_kg, 2),
                mass_per_functional_unit_kg=_round_half_up(mass_per_fu, 4),
                percentage_of_total=_round_half_up(percentage, 2),
            )
        )

    # Sort descending by contribution, matching the convention in published EPDs
    # (largest material first — e.g. Steel 55.32%, Iron 27.32%, ... in EPD11017).
    rows.sort(key=lambda r: r.percentage_of_total, reverse=True)

    total_percentage = _round_half_up(sum(r.percentage_of_total for r in rows), 2)

    if abs(total_percentage - 100.0) > percentage_tolerance:
        raise MaterialCompositionError(
            f"Material composition percentages sum to {total_percentage}%, which "
            f"exceeds the {percentage_tolerance} percentage-point tolerance from "
            "100%. This indicates a data integrity issue in the BOM (e.g. a "
            "duplicate or corrupted mass value) — fix the source data rather than "
            "adjusting this table."
        )

    return MaterialCompositionTable(
        functional_unit_description=functional_unit_description,
        conversion_factor_kg_per_fu=_round_half_up(conversion_factor_kg_per_fu, 4),
        rows=rows,
        total_mass_kg=_round_half_up(total_mass_kg, 2),
        total_percentage=total_percentage,
    )


def render_composition_table_html(table: MaterialCompositionTable) -> str:
    """
    Render the two-part table as HTML matching the platform's existing PDF table
    design tokens (hairline borders, dark header band). This is deliberately plain
    HTML/CSS so it can be dropped directly into the WeasyPrint pipeline already
    used for EPD generation, using the same table classes as every other results
    table in the document.
    """
    rows_html = "\n".join(
        f"""
        <tr>
            <td class="mat-name">{row.material_name}</td>
            <td class="mat-num">{row.mass_per_functional_unit_kg:.4f}</td>
            <td class="mat-num">{row.percentage_of_total:.2f}%</td>
        </tr>
        """
        for row in table.rows
    )

    return f"""
    <div class="epd-section">
        <h3>Material Composition per Functional Unit</h3>
        <p class="epd-caption">
            Functional Unit: {table.functional_unit_description} &mdash;
            {table.conversion_factor_kg_per_fu:.4f} kg per functional unit
        </p>
        <table class="epd-wide-table">
            <thead>
                <tr>
                    <th>Material</th>
                    <th>Mass per Functional Unit (kg)</th>
                    <th>Contribution to Total (%)</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
                <tr class="mat-total-row">
                    <td class="mat-name"><strong>Total</strong></td>
                    <td class="mat-num"><strong>{table.conversion_factor_kg_per_fu:.4f}</strong></td>
                    <td class="mat-num"><strong>{table.total_percentage:.2f}%</strong></td>
                </tr>
            </tbody>
        </table>
    </div>
    """
