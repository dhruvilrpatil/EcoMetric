"""
backend/api/models.py

Pydantic v2 data models for all EPD project inputs and outputs.
Covers all 4 output groups and all input categories per the EcoMetric PRD.
"""

from __future__ import annotations
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class LCModule(str, Enum):
    A1 = "A1"; A2 = "A2"; A3 = "A3"; A4 = "A4"; A5 = "A5"
    B1 = "B1"; B2 = "B2"; B3 = "B3"; B4 = "B4"; B5 = "B5"; B6 = "B6"; B7 = "B7"
    C1 = "C1"; C2 = "C2"; C3 = "C3"; C4 = "C4"; D = "D"

class EPDStandard(str, Enum):
    EN_15804_A2 = "EN_15804_A2"
    ISO_21930   = "ISO_21930"
    ISO_14025   = "ISO_14025"

class LCIAMethod(str, Enum):
    EF_3_1  = "EF_3_1"
    TRACI   = "TRACI_2_1"
    CML     = "CML_IA"
    PEF     = "PEF"

class DataQuality(str, Enum):
    PRIMARY   = "PRIMARY"
    SECONDARY = "SECONDARY"
    PROXY     = "PROXY"

class VehicleType(str, Enum):
    HEAVY_TRUCK_EURO5 = "Heavy truck EURO5"
    RAIL              = "Rail"
    SHIP              = "Ship"
    AIR               = "Air"


# ─────────────────────────────────────────────────────────────
# INPUT MODELS
# ─────────────────────────────────────────────────────────────

class ProductDetails(BaseModel):
    product_name:            str
    product_sku:             Optional[str] = None
    product_lifetime_years:  float = Field(75.0, gt=0)
    product_configuration:   Optional[str] = None
    manufacturer_name:       Optional[str] = None
    manufacturing_country:   Optional[str] = None
    functional_unit_quantity: float = Field(1.0, gt=0)
    functional_unit_unit:    str   = "ton_chilling_capacity"

class ProgramOperator(BaseModel):
    name: str = ""
    address: str = ""
    website: str = ""
    logo_url: Optional[str] = None


class ProductDescriptionFields(BaseModel):
    operating_principle: str = ""
    core_technology_description: str = ""
    heat_transfer_description: Optional[str] = None
    applications_description: str = ""
    capacity_range_description: str = ""
    configuration_notes: Optional[str] = None
    refrigerant_technology_notes: Optional[str] = None


class ManufacturingNarrativeFields(BaseModel):
    component_sourcing_description: str = ""
    assembly_description: str = ""
    production_facility_locations: List[str] = []
    capital_goods_exclusion_rationale: Optional[str] = None


class CertificationItem(BaseModel):
    standard_name: str
    certifying_body: Optional[str] = None


class ProjectNarrativeFields(BaseModel):
    company_description: str = ""
    product_narrative: str = ""
    product_description: Optional[ProductDescriptionFields] = None
    manufacturing_narrative: Optional[ManufacturingNarrativeFields] = None
    certifications_structured: List[CertificationItem] = []
    csi_division_code: Optional[str] = None
    certifications: List[str] = []
    pcr_reviewer_names: List[str] = []
    lca_conductor_name: Optional[str] = None
    verifier_name: Optional[str] = None
    verifier_email: Optional[str] = None
    program_operator: Optional[ProgramOperator] = None


class BOMItem(BaseModel):
    material_name:   str
    mass_kg:         float = Field(..., gt=0)
    unit:            str = "kg"
    lc_module:       LCModule = LCModule.A1
    lci_dataset_id:  Optional[str] = None
    data_quality:    DataQuality = DataQuality.SECONDARY
    is_cut_off:      bool = False
    cut_off_reason:  Optional[str] = None


class ManufacturingData(BaseModel):
    manufacturing_location:  Optional[str] = None
    electricity_use_kwh:     float = Field(0.0, ge=0)
    electricity_grid_region: str = "GLO"
    assembly_process_desc:   Optional[str] = None
    product_mass_kg:         Optional[float] = None
    manufacturing_energy_mj: float = Field(0.0, ge=0)
    other_energy_sources:    Optional[Dict[str, float]] = None  # {"natural_gas_mj": 0}


class TransportLeg(BaseModel):
    lc_module:               LCModule
    vehicle_type:            VehicleType = VehicleType.HEAVY_TRUCK_EURO5
    product_weight_kg:       Optional[float] = None
    fuel_type:               Optional[str] = None
    road_distance_km:        float = Field(0.0, ge=0)
    ocean_freight_km:        float = Field(0.0, ge=0)
    capacity_utilization_pct: float = Field(100.0, ge=0, le=100)
    lci_dataset_id:          Optional[str] = None


class InstallationData(BaseModel):
    diesel_crane_liters:     float = Field(0.0, ge=0)
    packaging_waste_kg:      float = Field(0.0, ge=0)
    packaging_material:      str = "cardboard"
    installation_assumptions: Optional[str] = None


class UsePhaseData(BaseModel):
    # B6 Operational energy
    annual_electricity_kwh:    float = Field(..., ge=0)
    electricity_grid_region:   str = "US"
    electricity_per_func_unit: Optional[float] = None
    # B1 Refrigerant
    refrigerant_type:          str = "R-1233zd(E)"
    refrigerant_charge_kg:     float = Field(0.0, ge=0)
    annual_leakage_rate_pct:   float = Field(0.01, ge=0, le=1)
    refrigerant_gwp:           float = Field(1.0, ge=0)  # GWP100
    # Maintenance
    maintenance_cycles:        int = 1
    replacement_cycles:        int = 0
    maintenance_notes:         Optional[str] = None


class EndOfLifeData(BaseModel):
    waste_to_landfill_pct:       float = Field(30.0, ge=0, le=100)
    waste_to_recycling_pct:      float = Field(60.0, ge=0, le=100)
    waste_to_incineration_pct:   float = Field(10.0, ge=0, le=100)
    waste_to_reuse_pct:          float = Field(0.0, ge=0, le=100)
    disposal_transport_km:       float = Field(50.0, ge=0)
    disposal_vehicle_type:       str = "Heavy truck EURO5"
    refrigerant_recovery_rate_pct: float = Field(95.0, ge=0, le=100)
    recycling_credit_included:   bool = True
    energy_recovery_mj:          float = Field(0.0, ge=0)


class LCAConfig(BaseModel):
    epd_standard:    EPDStandard = EPDStandard.EN_15804_A2
    system_boundary: str = "cradle_to_grave"
    lcia_method:     LCIAMethod  = LCIAMethod.EF_3_1
    lci_database:    str = "ecoinvent_3.12_cutoff"
    active_modules:  List[LCModule] = [
        LCModule.A1, LCModule.A2, LCModule.A3, LCModule.A4, LCModule.A5,
        LCModule.B1, LCModule.B6,
        LCModule.C1, LCModule.C2, LCModule.C3, LCModule.C4,
        LCModule.D
    ]


class ProjectCreateRequest(BaseModel):
    """Full project creation payload — all input groups."""
    product:        ProductDetails
    bom:            List[BOMItem]          = []
    manufacturing:  Optional[ManufacturingData] = None
    transport_legs: List[TransportLeg]     = []
    installation:   Optional[InstallationData] = None
    use_phase:      Optional[UsePhaseData] = None
    end_of_life:    Optional[EndOfLifeData] = None
    lca_config:     LCAConfig              = LCAConfig()
    narrative:      Optional[ProjectNarrativeFields] = None


# ─────────────────────────────────────────────────────────────
# OUTPUT MODELS
# ─────────────────────────────────────────────────────────────

class ModuleValues(BaseModel):
    """Per-module LCIA result values. Keys are module codes + 'total'."""
    A1: Optional[float] = None
    A2: Optional[float] = None
    A3: Optional[float] = None
    A4: Optional[float] = None
    A5: Optional[float] = None
    B1: Optional[float] = None
    B6: Optional[float] = None
    C1: Optional[float] = None
    C2: Optional[float] = None
    C3: Optional[float] = None
    C4: Optional[float] = None
    D:  Optional[float] = None
    total: Optional[float] = None


class EnvironmentalImpactIndicators(BaseModel):
    """Group 1 — Environmental Impact Indicators (EN 15804+A2 mandatory)."""
    gwp_total:      ModuleValues   # kg CO2e   — Global Warming Potential (total)
    gwp_fossil:     ModuleValues   # kg CO2e   — GWP fossil
    gwp_biogenic:   ModuleValues   # kg CO2e   — GWP biogenic
    gwp_luluc:      ModuleValues   # kg CO2e   — GWP land use
    odp:            ModuleValues   # kg CFC-11 eq — Ozone Depletion
    ap:             ModuleValues   # mol H+ eq — Acidification
    ep_freshwater:  ModuleValues   # kg P eq   — Eutrophication Freshwater
    ep_marine:      ModuleValues   # kg N eq   — Eutrophication Marine
    ep_terrestrial: ModuleValues   # mol N eq  — Eutrophication Terrestrial
    pocp:           ModuleValues   # kg NMVOC  — Photochemical Ozone Formation
    adpe:           ModuleValues   # kg Sb eq  — Abiotic Depletion (minerals/metals)
    adpf:           ModuleValues   # MJ        — Abiotic Depletion (fossil fuels)
    wdp:            ModuleValues   # m3 world eq — Water Deprivation
    pm:             ModuleValues   # disease incidence — Particulate Matter
    ir:             ModuleValues   # kBq U235 eq — Ionizing Radiation
    etox:           ModuleValues   # CTUe      — Freshwater Ecotoxicity
    htox_cancer:    ModuleValues   # CTUh      — Human Toxicity (Cancer)
    htox_noncancer: ModuleValues   # CTUh      — Human Toxicity (Non-Cancer)
    land_use:       ModuleValues   # Pt        — Land Use Impact


class ResourceUseOutputs(BaseModel):
    """Group 2 — Resource Use Outputs."""
    pere:   ModuleValues   # MJ — Renewable primary energy (energy carrier)
    perm:   ModuleValues   # MJ — Renewable primary energy (raw material)
    pert:   ModuleValues   # MJ — Renewable primary energy (total)
    penre:  ModuleValues   # MJ — Non-renewable primary energy (energy carrier)
    penrm:  ModuleValues   # MJ — Non-renewable primary energy (raw material)
    penrt:  ModuleValues   # MJ — Non-renewable primary energy (total)
    sm:     ModuleValues   # kg — Secondary material use
    rsf:    ModuleValues   # MJ — Renewable secondary fuels
    nrsf:   ModuleValues   # MJ — Non-renewable secondary fuels
    fw:     ModuleValues   # m³ — Freshwater consumption


class WasteOutputs(BaseModel):
    """Group 3 — Waste and End-of-Life Outputs."""
    hwd:    ModuleValues   # kg — Hazardous waste disposed
    nhwd:   ModuleValues   # kg — Non-hazardous waste disposed
    rwd:    ModuleValues   # kg — Radioactive waste disposed
    cru:    ModuleValues   # kg — Components for reuse
    mfr:    ModuleValues   # kg — Materials sent for recycling
    mer:    ModuleValues   # kg — Materials for energy recovery
    ee:     ModuleValues   # MJ — Exported energy


class OperationalOutputs(BaseModel):
    """Group 4 — Product-Specific Operational Outputs."""
    annual_electricity_kwh:      float
    lifetime_electricity_kwh:    float   # annual × product_lifetime
    electricity_per_func_unit:   float
    refrigerant_leakage_kg:      float
    direct_air_emissions_kg_co2: float
    packaging_waste_kg:          float
    waste_to_landfill_kg:        float
    waste_to_recycling_kg:       float
    transport_distances_km:      Dict[str, float]  # {"A2": 200, "A4": 500}
    maintenance_impact_kg_co2e:  float


class AIEPDOutputs(BaseModel):
    """AI-generated EPD summary fields."""
    carbon_footprint_kg_co2e: float
    lca_by_module:            Dict[str, Dict[str, float]]  # { "A1": {"GWP": 10.2, ...}, ... }
    compliance_summary:       Dict[str, str]               # { "ISO_14025": "PASS", ... }
    report_formats:           List[str] = ["PDF", "JSON", "XML"]


class LCAResultResponse(BaseModel):
    """Full LCA result — all 4 output groups."""
    project_id:           str
    run_id:               str
    lcia_method:          str
    functional_unit:      str
    is_final:             bool

    # 4 Output Groups
    environmental_impacts: EnvironmentalImpactIndicators
    resource_use:          ResourceUseOutputs
    waste_outputs:         WasteOutputs
    operational_outputs:   OperationalOutputs
    ai_epd_summary:        Optional[AIEPDOutputs] = None

    # Audit trace
    condition_number:     float
    matrix_A_dimensions:  List[int]
    matrix_B_dimensions:  List[int]
    hotspots:             List[dict] = []
