import pytest
from engine.material_composition import MaterialInventoryItem
from engine.functional_unit_details import (
    FunctionalUnitDetails,
    FunctionalUnitDetailsError,
    compute_functional_unit_details,
    render_functional_unit_details_html,
)


def test_compute_functional_unit_details_success():
    materials = [
        MaterialInventoryItem("Steel", 15000.0),
        MaterialInventoryItem("Copper", 456.0),
    ]
    details = compute_functional_unit_details(
        materials=materials,
        functional_unit_description="1 ton chilling capacity",
        functional_unit_quantity=650.0,
        functional_unit_measure_name="ton of chilling capacity",
        configuration_label="650 ton",
    )
    assert details.mass_of_one_delivered_product_kg == 15456.0
    assert abs(details.conversion_factor_kg_per_fu - 23.7785) < 0.01
    assert details.conversion_factor_unit == "kg/ton of chilling capacity"
    assert details.unit_label == "650 ton"


def test_zero_fu_quantity_raises():
    materials = [MaterialInventoryItem("Steel", 100.0)]
    with pytest.raises(FunctionalUnitDetailsError):
        compute_functional_unit_details(materials, "1 unit", 0.0, "unit", "1 unit")


def test_empty_materials_raises():
    with pytest.raises(FunctionalUnitDetailsError):
        compute_functional_unit_details([], "1 unit", 1.0, "unit", "1 unit")


def test_render_html():
    details = FunctionalUnitDetails(
        functional_unit_description="1 ton chilling capacity",
        unit_label="650 ton",
        mass_of_one_delivered_product_kg=15456.0,
        conversion_factor_kg_per_fu=23.8,
        conversion_factor_unit="kg/ton of chilling capacity",
    )
    html = render_functional_unit_details_html(details)
    assert "Functional Unit Details" in html
    assert "650 ton" in html
    assert "15456" in html
    assert "23.8" in html
