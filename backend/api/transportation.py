"""
backend/api/transportation.py

Transportation Module A4 API Endpoints.
Implements TransportScenario persistence, PCR validation, and AI suggestion assistance.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import get_db_cursor
from engine.transport_scenario import (
    TransportScenario,
    TransportScenarioError,
    VEHICLE_DATABASE,
    build_transport_scenario,
)

router = APIRouter(prefix="/projects", tags=["Transportation"])
logger = logging.getLogger(__name__)


class TransportScenarioRequest(BaseModel):
    vehicle_type: str = ">32000 kg payload Flatbed Truck"
    payload_capacity: float = 32000.0
    fuel_type: str = "Diesel"
    fuel_efficiency: float = 36.3
    road_distance: float = Field(0.0, ge=0)
    ocean_distance: float = Field(0.0, ge=0)
    rail_distance: float = Field(0.0, ge=0)
    air_distance: float = Field(0.0, ge=0)
    product_weight: float = Field(1.0, gt=0)
    gross_density: float = Field(369.0, gt=0)
    capacity_utilization: float = Field(24.0, ge=1.0, le=100.0)
    capacity_volume_factor: str = "<1"


class AISuggestRequest(BaseModel):
    product_weight: Optional[float] = None
    product_name: Optional[str] = None


def ensure_transport_scenario_table(cursor):
    """Ensure the transport_scenario database table exists."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transport_scenario (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            vehicle_type VARCHAR(100) NOT NULL,
            payload_capacity NUMERIC(14,4) DEFAULT 32000,
            fuel_type VARCHAR(50) DEFAULT 'Diesel',
            fuel_efficiency NUMERIC(8,4) DEFAULT 36.3,
            road_distance NUMERIC(10,2) DEFAULT 0,
            ocean_distance NUMERIC(10,2) DEFAULT 0,
            rail_distance NUMERIC(10,2) DEFAULT 0,
            air_distance NUMERIC(10,2) DEFAULT 0,
            product_weight NUMERIC(14,4) DEFAULT 0,
            gross_density NUMERIC(10,2) DEFAULT 369,
            capacity_utilization NUMERIC(5,2) DEFAULT 24.0,
            capacity_volume_factor VARCHAR(10) DEFAULT '<1',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_transport_scenario_project ON transport_scenario(project_id);
    """)


@router.get("/{project_id}/transportation")
async def get_transportation(project_id: str, cursor=Depends(get_db_cursor)):
    """Fetch existing Module A4 transport scenario for the edit form."""
    ensure_transport_scenario_table(cursor)

    cursor.execute(
        "SELECT * FROM transport_scenario WHERE project_id = %s ORDER BY updated_at DESC LIMIT 1",
        (project_id,)
    )
    row = cursor.fetchone()

    # Calculate BOM mass if product_weight needs auto-filling
    cursor.execute("SELECT SUM(mass_kg) as total_mass FROM bom_items WHERE project_id = %s", (project_id,))
    bom_row = cursor.fetchone()
    bom_total_mass = float(bom_row["total_mass"]) if bom_row and bom_row.get("total_mass") else 15455.7

    if row:
        result = dict(row)
        if not result.get("product_weight") or result.get("product_weight") == 0:
            result["product_weight"] = bom_total_mass
        return result

    # Fallback / initial default scenario
    default_sc = build_transport_scenario({}, bom_total_weight=bom_total_mass)
    return {
        "vehicle_type": default_sc.vehicle_type,
        "payload_capacity": default_sc.payload_capacity,
        "fuel_type": default_sc.fuel_type,
        "fuel_efficiency": default_sc.fuel_efficiency,
        "road_distance": 500.0,
        "ocean_distance": 0.0,
        "rail_distance": 0.0,
        "air_distance": 0.0,
        "product_weight": bom_total_mass,
        "gross_density": default_sc.gross_density,
        "capacity_utilization": default_sc.capacity_utilization,
        "capacity_volume_factor": default_sc.capacity_volume_factor,
    }


@router.post("/{project_id}/transportation/save")
async def save_transportation(
    project_id: str,
    body: TransportScenarioRequest,
    cursor=Depends(get_db_cursor)
):
    """
    Validate and save Module A4 TransportScenario to PostgreSQL.
    Invalidates stale lca_results.
    """
    ensure_transport_scenario_table(cursor)

    try:
        # Validate scenario using engine rules
        scenario_data = body.dict()
        scenario = build_transport_scenario(scenario_data)

        # Check existing scenario
        cursor.execute("SELECT id FROM transport_scenario WHERE project_id = %s", (project_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE transport_scenario
                SET vehicle_type = %s,
                    payload_capacity = %s,
                    fuel_type = %s,
                    fuel_efficiency = %s,
                    road_distance = %s,
                    ocean_distance = %s,
                    rail_distance = %s,
                    air_distance = %s,
                    product_weight = %s,
                    gross_density = %s,
                    capacity_utilization = %s,
                    capacity_volume_factor = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE project_id = %s
            """, (
                scenario.vehicle_type,
                scenario.payload_capacity,
                scenario.fuel_type,
                scenario.fuel_efficiency,
                scenario.road_distance,
                scenario.ocean_distance,
                scenario.rail_distance,
                scenario.air_distance,
                scenario.product_weight,
                scenario.gross_density,
                scenario.capacity_utilization,
                scenario.capacity_volume_factor,
                project_id
            ))
        else:
            cursor.execute("""
                INSERT INTO transport_scenario (
                    project_id, vehicle_type, payload_capacity, fuel_type, fuel_efficiency,
                    road_distance, ocean_distance, rail_distance, air_distance,
                    product_weight, gross_density, capacity_utilization, capacity_volume_factor
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id,
                scenario.vehicle_type,
                scenario.payload_capacity,
                scenario.fuel_type,
                scenario.fuel_efficiency,
                scenario.road_distance,
                scenario.ocean_distance,
                scenario.rail_distance,
                scenario.air_distance,
                scenario.product_weight,
                scenario.gross_density,
                scenario.capacity_utilization,
                scenario.capacity_volume_factor
            ))

        # Synchronize JSON column on project table & mark LCA stale
        cursor.execute("""
            UPDATE projects
            SET transportation_data = %s,
                status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (json.dumps(scenario_data), project_id))

        cursor.execute("UPDATE lca_results SET is_final = FALSE WHERE project_id = %s", (project_id,))

        return {"status": "success", "scenario": scenario_data}

    except TransportScenarioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to save transport scenario for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/transportation/ai-suggest")
async def ai_suggest_transport(
    project_id: str,
    body: AISuggestRequest,
    cursor=Depends(get_db_cursor)
):
    """
    AI Assistance endpoint:
    Suggests vehicle type, fuel efficiency, gross density, default capacity utilization,
    and missing distances based on product weight and classification.
    """
    cursor.execute("SELECT SUM(mass_kg) as total_mass FROM bom_items WHERE project_id = %s", (project_id,))
    bom_row = cursor.fetchone()
    total_weight = body.product_weight or (float(bom_row["total_mass"]) if bom_row and bom_row.get("total_mass") else 15455.7)

    # Heuristic AI logic based on weight class
    if total_weight > 25000:
        recommended_vehicle = "Rail" if total_weight > 100000 else ">32000 kg payload Flatbed Truck"
    elif total_weight > 15000:
        recommended_vehicle = "Flatbed Truck (>32 ton)"
    elif total_weight > 5000:
        recommended_vehicle = "Heavy Truck"
    else:
        recommended_vehicle = "Medium Truck"

    veh_info = VEHICLE_DATABASE.get(recommended_vehicle, VEHICLE_DATABASE[">32000 kg payload Flatbed Truck"])

    # Estimated gross density calculation (industrial standard default: 350 - 450 kg/m³)
    estimated_gross_density = 369.0 if total_weight > 10000 else 320.0

    return {
        "suggested_vehicle_type": recommended_vehicle,
        "payload_capacity": veh_info["payload_capacity"],
        "suggested_fuel_type": veh_info["fuel_type"],
        "suggested_fuel_efficiency": veh_info["fuel_efficiency"],
        "suggested_capacity_utilization": 24.0,
        "suggested_gross_density": estimated_gross_density,
        "suggested_road_distance": 500.0,
        "suggested_ocean_distance": 0.0,
        "suggested_capacity_volume_factor": "<1",
        "rationale": f"Based on product mass of {total_weight:.1f} kg, {recommended_vehicle} is optimal for freight efficiency and PCR compliance.",
    }
