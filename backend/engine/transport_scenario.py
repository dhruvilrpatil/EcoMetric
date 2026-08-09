"""
backend/engine/transport_scenario.py

EPD-compliant Transport to Building Site (Module A4) scenario engine.
Enforces PCR, ISO 21930, and EN 15804+A2 reporting rules.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


class TransportScenarioError(ValueError):
    """Raised when transport scenario parameters violate PCR validation rules."""
    pass


VEHICLE_DATABASE: Dict[str, Dict[str, Any]] = {
    ">32000 kg payload Flatbed Truck": {
        "payload_capacity": 32000.0,
        "fuel_efficiency": 36.3,
        "fuel_type": "Diesel",
    },
    "Flatbed Truck (>32 ton)": {
        "payload_capacity": 32000.0,
        "fuel_efficiency": 36.3,
        "fuel_type": "Diesel",
    },
    "Heavy Truck": {
        "payload_capacity": 24000.0,
        "fuel_efficiency": 32.0,
        "fuel_type": "Diesel",
    },
    "Medium Truck": {
        "payload_capacity": 12000.0,
        "fuel_efficiency": 22.0,
        "fuel_type": "Diesel",
    },
    "Container Truck": {
        "payload_capacity": 28000.0,
        "fuel_efficiency": 34.5,
        "fuel_type": "Diesel",
    },
    "Rail": {
        "payload_capacity": 500000.0,
        "fuel_efficiency": 5.0,
        "fuel_type": "Electric",
    },
    "Ocean Vessel": {
        "payload_capacity": 10000000.0,
        "fuel_efficiency": 2.5,
        "fuel_type": "LNG",
    },
}


@dataclass
class TransportScenario:
    vehicle_type: str
    payload_capacity: float
    fuel_type: str
    fuel_efficiency: float
    road_distance: float
    ocean_distance: float
    rail_distance: float
    air_distance: float
    product_weight: float
    gross_density: float
    capacity_utilization: float
    capacity_volume_factor: str

    def validate(self) -> None:
        """Enforce PCR / ISO 21930 validation rules."""
        if self.road_distance < 0:
            raise TransportScenarioError("Road distance must be greater than or equal to 0 km.")
        if self.ocean_distance < 0:
            raise TransportScenarioError("Ocean distance must be greater than or equal to 0 km.")
        if self.rail_distance < 0:
            raise TransportScenarioError("Rail distance must be greater than or equal to 0 km.")
        if self.air_distance < 0:
            raise TransportScenarioError("Air distance must be greater than or equal to 0 km.")
        if self.fuel_efficiency <= 0:
            raise TransportScenarioError("Fuel efficiency must be greater than 0 L/100 km.")
        if not (1.0 <= self.capacity_utilization <= 100.0):
            raise TransportScenarioError(
                f"Capacity utilization must be between 1% and 100%; got {self.capacity_utilization}%."
            )
        if self.product_weight <= 0:
            raise TransportScenarioError("Product weight must be greater than 0 kg.")


def build_transport_scenario(data: Dict[str, Any], bom_total_weight: float = 0.0) -> TransportScenario:
    """
    Construct and validate a TransportScenario object.
    Product weight is auto-populated from project BOM if not specified.
    """
    vehicle_type = data.get("vehicle_type") or ">32000 kg payload Flatbed Truck"
    veh_defaults = VEHICLE_DATABASE.get(vehicle_type, VEHICLE_DATABASE[">32000 kg payload Flatbed Truck"])

    payload_capacity = float(data.get("payload_capacity") or veh_defaults["payload_capacity"])
    fuel_type = data.get("fuel_type") or veh_defaults["fuel_type"]
    fuel_efficiency = float(data.get("fuel_efficiency") or veh_defaults["fuel_efficiency"])

    product_weight = float(data.get("product_weight") or bom_total_weight or 1.0)
    gross_density = float(data.get("gross_density") or 369.0)
    capacity_utilization = float(data.get("capacity_utilization") if data.get("capacity_utilization") is not None else 24.0)
    capacity_volume_factor = str(data.get("capacity_volume_factor") or "<1")

    scenario = TransportScenario(
        vehicle_type=vehicle_type,
        payload_capacity=payload_capacity,
        fuel_type=fuel_type,
        fuel_efficiency=fuel_efficiency,
        road_distance=float(data.get("road_distance") or 0.0),
        ocean_distance=float(data.get("ocean_distance") or 0.0),
        rail_distance=float(data.get("rail_distance") or 0.0),
        air_distance=float(data.get("air_distance") or 0.0),
        product_weight=product_weight,
        gross_density=gross_density,
        capacity_utilization=capacity_utilization,
        capacity_volume_factor=capacity_volume_factor,
    )

    scenario.validate()
    return scenario


def render_a4_transport_table_html(scenario: TransportScenario) -> str:
    """
    Render Module A4 Transport to Building Site table matching Carrier/UL Solutions EPD format.
    3 columns ONLY: Parameter | Value | Unit
    """
    rows = [
        ("Vehicle Type", scenario.vehicle_type, "—"),
        ("Product Weight", f"{scenario.product_weight:.1f}", "kg"),
        ("Fuel Efficiency", f"{scenario.fuel_efficiency:.1f}", "L/100 km"),
        ("Fuel Type", scenario.fuel_type, "—"),
        ("Distance", f"{scenario.road_distance:.0f}", "km"),
    ]

    if scenario.ocean_distance > 0:
        rows.append(("Additional Ocean Freight Distance", f"{scenario.ocean_distance:.0f}", "km"))
    if scenario.rail_distance > 0:
        rows.append(("Additional Rail Freight Distance", f"{scenario.rail_distance:.0f}", "km"))
    if scenario.air_distance > 0:
        rows.append(("Additional Air Freight Distance", f"{scenario.air_distance:.0f}", "km"))

    rows.extend([
        ("Capacity Utilization", f"{scenario.capacity_utilization:.0f}", "%"),
        ("Gross Density of Products Transported", f"{scenario.gross_density:.0f}", "kg/m³"),
        ("Capacity Utilization Volume Factor", scenario.capacity_volume_factor, "—"),
    ])

    table_rows_html = "".join(
        f"<tr><td>{param}</td><td>{val}</td><td>{unit}</td></tr>"
        for param, val, unit in rows
    )

    return f"""
    <div class="epd-section">
        <p class="epd-table-caption">Table: Transport to Building Site (A4) per Functional Unit</p>
        <table class="epd-a4-transport-table">
            <thead>
                <tr class="dark-header">
                    <th>Parameter</th>
                    <th>Value</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
    """
