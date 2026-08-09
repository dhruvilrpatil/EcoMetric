import pytest
from engine.transport_scenario import (
    TransportScenario,
    TransportScenarioError,
    build_transport_scenario,
    render_a4_transport_table_html,
)


def test_build_transport_scenario_success():
    data = {
        "vehicle_type": ">32000 kg payload Flatbed Truck",
        "road_distance": 500.0,
        "ocean_distance": 13681.0,
        "product_weight": 15455.7,
        "gross_density": 369.0,
        "capacity_utilization": 24.0,
        "capacity_volume_factor": "<1",
    }
    scenario = build_transport_scenario(data)
    assert scenario.vehicle_type == ">32000 kg payload Flatbed Truck"
    assert scenario.road_distance == 500.0
    assert scenario.ocean_distance == 13681.0
    assert scenario.product_weight == 15455.7
    assert scenario.gross_density == 369.0
    assert scenario.capacity_utilization == 24.0
    assert scenario.capacity_volume_factor == "<1"


def test_render_html_hides_zero_ocean_distance():
    data = {
        "vehicle_type": "Heavy Truck",
        "road_distance": 350.0,
        "ocean_distance": 0.0,
        "product_weight": 5000.0,
    }
    scenario = build_transport_scenario(data)
    html = render_a4_transport_table_html(scenario)
    assert "Distance" in html
    assert "350" in html
    assert "Additional Ocean Freight Distance" not in html
    assert "Parameter" in html
    assert "Value" in html
    assert "Unit" in html


def test_render_html_shows_ocean_distance_when_present():
    data = {
        "vehicle_type": ">32000 kg payload Flatbed Truck",
        "road_distance": 500.0,
        "ocean_distance": 13681.0,
        "product_weight": 15455.7,
    }
    scenario = build_transport_scenario(data)
    html = render_a4_transport_table_html(scenario)
    assert "Additional Ocean Freight Distance" in html
    assert "13681" in html


def test_validation_negative_distance_raises():
    data = {"road_distance": -50.0}
    with pytest.raises(TransportScenarioError, match="Road distance must be greater than or equal to 0"):
        build_transport_scenario(data)


def test_validation_capacity_utilization_out_of_bounds_raises():
    data = {"capacity_utilization": 150.0}
    with pytest.raises(TransportScenarioError, match="Capacity utilization must be between 1% and 100%"):
        build_transport_scenario(data)
