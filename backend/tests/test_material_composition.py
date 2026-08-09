import pytest
from engine.material_composition import (
    MaterialInventoryItem,
    build_material_composition_table,
    MaterialCompositionError,
    render_composition_table_html,
)


def test_percentages_sum_to_100():
    materials = [
        MaterialInventoryItem("Steel", 13.34),
        MaterialInventoryItem("Iron", 6.32),
        MaterialInventoryItem("Copper", 3.00),
    ]
    table = build_material_composition_table(materials, "1 unit", 22.66)
    assert abs(table.total_percentage - 100.0) <= 0.1


def test_empty_bom_raises():
    with pytest.raises(MaterialCompositionError):
        build_material_composition_table([], "1 unit", 10.0)


def test_zero_mass_material_raises():
    materials = [MaterialInventoryItem("Steel", 0.0)]
    with pytest.raises(MaterialCompositionError):
        build_material_composition_table(materials, "1 unit", 10.0)


def test_negative_conversion_factor_raises():
    materials = [MaterialInventoryItem("Steel", 10.0)]
    with pytest.raises(MaterialCompositionError):
        build_material_composition_table(materials, "1 unit", -5.0)


def test_rows_sorted_descending_by_percentage():
    materials = [
        MaterialInventoryItem("Small", 1.0),
        MaterialInventoryItem("Large", 10.0),
        MaterialInventoryItem("Medium", 5.0),
    ]
    table = build_material_composition_table(materials, "1 unit", 16.0)
    percentages = [r.percentage_of_total for r in table.rows]
    assert percentages == sorted(percentages, reverse=True)


def test_single_material_is_100_percent():
    materials = [MaterialInventoryItem("Only Material", 42.0)]
    table = build_material_composition_table(materials, "1 unit", 42.0)
    assert table.rows[0].percentage_of_total == 100.0


def test_render_html():
    materials = [
        MaterialInventoryItem("Steel", 10.0),
        MaterialInventoryItem("Copper", 5.0),
    ]
    table = build_material_composition_table(materials, "1 unit", 15.0)
    html = render_composition_table_html(table)
    assert "Material Composition per Functional Unit" in html
    assert "Steel" in html
    assert "Copper" in html
    assert "100.00%" in html
