"""
backend/engine/transport_module.py

Calculates environmental impacts for transport segments (Modules A2, A4, C2)
and produces structured outputs compatible with the LCA matrix engine.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

from engine.transport_datasets import TRANSPORT_DATASETS

logger = logging.getLogger(__name__)


@dataclass
class TransportSegment:
    origin_location: str
    destination_location: str
    transport_mode: str
    distance_km: float
    weight_tons: float
    capacity_utilization_pct: float
    material_name: Optional[str] = None


class TransportModule:
    """
    Calculates environmental impacts for a set of transport segments and produces
    rows compatible with the existing LCA matrix engine (matrix_lca.py).
    """

    def calculate_segment_impact(self, segment: TransportSegment) -> Dict[str, Any]:
        """
        Returns full multi-indicator impact for one transport leg.
        Shape matches elementary_exchanges format for integration into matrix B.
        """
        dataset = TRANSPORT_DATASETS.get(segment.transport_mode)
        if dataset is None:
            raise ValueError(f"Unknown transport mode: {segment.transport_mode}")

        ton_km = float(segment.weight_tons) * float(segment.distance_km)
        capacity_factor = float(segment.capacity_utilization_pct) / 100.0 if segment.capacity_utilization_pct else 1.0
        allocated_ton_km = ton_km * capacity_factor

        # Multiply elementary flow amounts by allocated_ton_km
        scaled_elementary_exchanges = {}
        for flow_name, flow_data in dataset.elementary_exchanges.items():
            amount = flow_data.get("amount", 0.0) if isinstance(flow_data, dict) else float(flow_data)
            unit = flow_data.get("unit", "kg") if isinstance(flow_data, dict) else "kg"
            scaled_elementary_exchanges[flow_name] = {
                "amount": amount * allocated_ton_km,
                "unit": unit
            }

        gwp = allocated_ton_km * dataset.emission_factor_kgco2_per_tonkm

        return {
            'origin': segment.origin_location,
            'destination': segment.destination_location,
            'mode': segment.transport_mode,
            'material_name': segment.material_name,
            'distance_km': segment.distance_km,
            'weight_tons': segment.weight_tons,
            'capacity_utilization_pct': segment.capacity_utilization_pct,
            'ton_km': ton_km,
            'allocated_ton_km': allocated_ton_km,
            'gwp_total_kgco2e': round(gwp, 6),
            'elementary_exchanges': scaled_elementary_exchanges,
            'ecoinvent_dataset_id': dataset.ecoinvent_id,
            'ecoinvent_dataset_name': dataset.ecoinvent_name,
        }

    def calculate_module_totals(
        self,
        a2_segments: List[TransportSegment],
        a4_segment: Optional[TransportSegment] = None,
        c2_segment: Optional[TransportSegment] = None,
    ) -> Dict[str, Any]:
        """
        Returns per-module totals (A2, A4, C2) plus segment-level detail for audit trails.
        """
        a2_results = [self.calculate_segment_impact(s) for s in a2_segments]
        a4_result = self.calculate_segment_impact(a4_segment) if a4_segment else None
        c2_result = self.calculate_segment_impact(c2_segment) if c2_segment else None

        a2_total_gwp = sum(r['gwp_total_kgco2e'] for r in a2_results)
        a4_total_gwp = a4_result['gwp_total_kgco2e'] if a4_result else 0.0
        c2_total_gwp = c2_result['gwp_total_kgco2e'] if c2_result else 0.0

        return {
            'A2': {'gwp_total_kgco2e': round(a2_total_gwp, 6), 'segments': a2_results},
            'A4': {'gwp_total_kgco2e': round(a4_total_gwp, 6), 'segments': [a4_result] if a4_result else []},
            'C2': {'gwp_total_kgco2e': round(c2_total_gwp, 6), 'segments': [c2_result] if c2_result else []},
        }
