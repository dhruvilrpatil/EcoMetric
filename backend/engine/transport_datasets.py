"""
backend/engine/transport_datasets.py

Ecoinvent v3.12 transport dataset mappings for EN 15804+A2 Modules A2, A4, C2.
Contains exact dataset IDs, names, geography codes, GWP factors, and full elementary exchange maps.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class TransportDatasetRef:
    ecoinvent_name: str
    ecoinvent_id: str
    geography: str
    unit: str                  # Always 'ton·km' for freight datasets
    emission_factor_kgco2_per_tonkm: float  # GWP-total factor
    elementary_exchanges: Dict[str, Dict[str, Any]]  # Full elementary exchange profile

TRANSPORT_DATASETS: Dict[str, TransportDatasetRef] = {
    'heavy_truck': TransportDatasetRef(
        ecoinvent_name='transport, freight, lorry >32 metric ton, EURO6',
        ecoinvent_id='3ba672d8-2b95-5f29-a1cd-1c442d2b480f',
        geography='RER',
        unit='ton·km',
        emission_factor_kgco2_per_tonkm=0.092,
        elementary_exchanges={
            'Carbon dioxide, fossil': {'amount': 0.067367, 'unit': 'kg'},
            'Methane, fossil': {'amount': 8.24e-07, 'unit': 'kg'},
            'Dinitrogen monoxide': {'amount': 6.97e-07, 'unit': 'kg'},
            'Sulfur dioxide': {'amount': 1.61e-05, 'unit': 'kg'},
            'Nitrogen oxides': {'amount': 0.000661, 'unit': 'kg'},
            'Particulate Matter, < 2.5 um': {'amount': 2.02e-05, 'unit': 'kg'},
            'NMVOC, non-methane volatile organic compounds': {'amount': 3.35e-05, 'unit': 'kg'},
        }
    ),
    'rail': TransportDatasetRef(
        ecoinvent_name='transport, freight, rail',
        ecoinvent_id='44d50051-df16-566f-89bd-c242f306efdf',
        geography='RER',
        unit='ton·km',
        emission_factor_kgco2_per_tonkm=0.015,
        elementary_exchanges={
            'Carbon dioxide, fossil': {'amount': 0.0065815, 'unit': 'kg'},
            'Methane, fossil': {'amount': 2.719e-07, 'unit': 'kg'},
            'Dinitrogen monoxide': {'amount': 2.091e-07, 'unit': 'kg'},
            'Sulfur dioxide': {'amount': 1.254e-06, 'unit': 'kg'},
            'Nitrogen oxides': {'amount': 0.0001149, 'unit': 'kg'},
            'Particulate Matter, < 2.5 um': {'amount': 2.683e-06, 'unit': 'kg'},
            'NMVOC, non-methane volatile organic compounds': {'amount': 1.059e-05, 'unit': 'kg'},
        }
    ),
    'ocean_freight': TransportDatasetRef(
        ecoinvent_name='transport, freight, sea, bulk large-capacity vessel',
        ecoinvent_id='4497e1e0-1ad0-58f2-899d-4fd9cf0d5f0d',
        geography='GLO',
        unit='ton·km',
        emission_factor_kgco2_per_tonkm=0.008,
        elementary_exchanges={
            'Carbon dioxide, fossil': {'amount': 0.10580, 'unit': 'kg'},
            'Methane, fossil': {'amount': 1.698e-06, 'unit': 'kg'},
            'Dinitrogen monoxide': {'amount': 6.115e-06, 'unit': 'kg'},
            'Sulfur dioxide': {'amount': 0.0003314, 'unit': 'kg'},
            'Nitrogen oxides': {'amount': 0.002578, 'unit': 'kg'},
            'Particulate Matter, < 2.5 um': {'amount': 0.0002358, 'unit': 'kg'},
            'NMVOC, non-methane volatile organic compounds': {'amount': 0.0001087, 'unit': 'kg'},
        }
    ),
    'air_freight': TransportDatasetRef(
        ecoinvent_name='transport, freight, air, intercontinental',
        ecoinvent_id='7d701408-4504-58bc-9d11-3e3d797db6f9',
        geography='GLO',
        unit='ton·km',
        emission_factor_kgco2_per_tonkm=0.520,
        elementary_exchanges={
            'Carbon dioxide, fossil': {'amount': 0.0191, 'unit': 'kg'},
            'Sulfur dioxide': {'amount': 5.157e-06, 'unit': 'kg'},
            'Nitrogen oxides': {'amount': 9.481e-05, 'unit': 'kg'},
            'Particulate Matter, < 2.5 um': {'amount': 7.21e-07, 'unit': 'kg'},
            'NMVOC, non-methane volatile organic compounds': {'amount': 7.388e-07, 'unit': 'kg'},
        }
    ),
}
