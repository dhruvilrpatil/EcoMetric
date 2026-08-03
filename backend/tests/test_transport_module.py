import pytest
from engine.transport_module import TransportModule, TransportSegment
from engine.transport_datasets import TRANSPORT_DATASETS

def test_transport_segment_impact_math():
    engine = TransportModule()
    
    # Toy segment: 10 tons transported 500 km at 50% capacity utilization
    segment = TransportSegment(
        origin_location="Shanghai",
        destination_location="Rotterdam",
        transport_mode="ocean_freight",
        distance_km=500.0,
        weight_tons=10.0,
        capacity_utilization_pct=50.0,
        material_name="Steel Plate"
    )
    
    res = engine.calculate_segment_impact(segment)
    
    # ton_km = 10 * 500 = 5000
    assert res['ton_km'] == 5000.0
    
    # allocated_ton_km = 5000 * 0.5 = 2500
    assert res['allocated_ton_km'] == 2500.0
    
    # GWP = 2500 * 0.008 = 20.0
    expected_gwp = 2500.0 * TRANSPORT_DATASETS['ocean_freight'].emission_factor_kgco2_per_tonkm
    assert pytest.approx(res['gwp_total_kgco2e'], 0.001) == expected_gwp

def test_module_totals_calculation():
    engine = TransportModule()
    
    a2_seg = TransportSegment(
        origin_location="Factory A",
        destination_location="Plant B",
        transport_mode="heavy_truck",
        distance_km=100.0,
        weight_tons=2.0,
        capacity_utilization_pct=100.0
    )
    
    a4_seg = TransportSegment(
        origin_location="Plant B",
        destination_location="Site C",
        transport_mode="rail",
        distance_km=200.0,
        weight_tons=2.0,
        capacity_utilization_pct=100.0
    )
    
    totals = engine.calculate_module_totals([a2_seg], a4_seg)
    
    # A2: 2 tons * 100 km * 0.092 = 18.4 kg CO2e
    assert pytest.approx(totals['A2']['gwp_total_kgco2e'], 0.01) == 18.4
    
    # A4: 2 tons * 200 km * 0.015 = 6.0 kg CO2e
    assert pytest.approx(totals['A4']['gwp_total_kgco2e'], 0.01) == 6.0
