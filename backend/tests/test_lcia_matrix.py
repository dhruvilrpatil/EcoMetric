"""
backend/tests/test_lcia_matrix.py
=================================
Comprehensive unit tests for the LCIA Results Matrix Engine.

Verifies:
  - Benchmark reconciliation against Carrier EPD11017 Tables 18-22 (GWP-total, ODP, AP, ADPF).
  - Strict reconciliation invariant: row.total == sum(active module cells) for all 37 indicators.
  - Distinct visual states for ND/MND vs 0.0 values.
  - Multi-methodology conversions (EN 15804+A2, TRACI 2.1, CML-IA, PEF, ISO 21930) and unit adjustments.
  - Provenance source traceability for verifier trust (B6 operational energy, A1-A3 materials, A4 logistics).
"""

import pytest
from engine.lcia_matrix import (
    INDICATOR_DEFINITIONS,
    EXPANDED_MODULE_LIST,
    COLLAPSED_MODULE_GROUPS,
    build_indicator_matrix,
    get_epd11017_reference_matrix,
    LCIAMatrixResponse,
)


@pytest.fixture
def epd11017_matrix():
    return get_epd11017_reference_matrix("EN_15804_A2")


class TestEPD11017Benchmark:
    """Verifies calculated matrix against Carrier EPD11017 reference document."""

    def test_matrix_contains_all_four_groups(self, epd11017_matrix):
        categories = {ind.category for ind in epd11017_matrix.indicators}
        assert "core" in categories
        assert "additional" in categories
        assert "resource_use" in categories
        assert "waste_output" in categories
        assert len(epd11017_matrix.indicators) >= 30

    def test_gwp_total_benchmark_values(self, epd11017_matrix):
        gwp = next(ind for ind in epd11017_matrix.indicators if ind.code == "GWP-total")
        assert gwp.unit == "kg CO2e"
        assert gwp.modules["A1-A3"] == 166.0
        assert gwp.modules["A4"] == 1.24
        assert gwp.modules["A5"] == 0.84
        assert gwp.modules["B1"] == 1.38
        assert gwp.modules["B6"] == 35900.0
        assert gwp.modules["C1"] == 2.59
        assert gwp.modules["C2"] == 0.42
        assert gwp.modules["C3"] == 2.07
        assert gwp.modules["C4"] == 0.099
        assert gwp.modules["D"] == -15.2
        assert gwp.modules["B3"] is None
        assert gwp.module_flags["B3"] in ["ND", "MND"]

    def test_odp_benchmark_values(self, epd11017_matrix):
        odp = next(ind for ind in epd11017_matrix.indicators if ind.code == "ODP")
        assert odp.unit == "kg CFC-11e"
        assert pytest.approx(odp.modules["A1-A3"], rel=1e-3) == 1.12e-5
        assert pytest.approx(odp.modules["B6"], rel=1e-3) == 1.82e-3
        assert odp.modules["B5"] is None
        assert odp.module_flags["B5"] in ["ND", "MND"]

    def test_ap_benchmark_values(self, epd11017_matrix):
        ap = next(ind for ind in epd11017_matrix.indicators if ind.code == "AP")
        assert ap.unit == "mol H+e"
        assert pytest.approx(ap.modules["A1-A3"], rel=1e-3) == 0.842
        assert pytest.approx(ap.modules["B6"], rel=1e-3) == 142.0
        assert ap.modules["B7"] is None

    def test_adpf_benchmark_values(self, epd11017_matrix):
        adpf = next(ind for ind in epd11017_matrix.indicators if ind.code == "ADPF")
        assert adpf.unit == "MJ"
        assert pytest.approx(adpf.modules["A1-A3"], rel=1e-3) == 2150.0
        assert pytest.approx(adpf.modules["B6"], rel=1e-3) == 485000.0


class TestReconciliationInvariant:
    """Verifies that for every row and methodology, total == sum(module cells)."""

    @pytest.mark.parametrize("method", ["EN_15804_A2", "TRACI_2_1", "CML_IA", "PEF", "ISO_21930"])
    def test_total_equals_module_sum_for_all_indicators(self, method):
        matrix = get_epd11017_reference_matrix(method)
        for ind in matrix.indicators:
            declared_sum = sum(v for v in ind.modules.values() if v is not None)
            assert pytest.approx(ind.total, abs=1e-5) == declared_sum, (
                f"Reconciliation drift in {ind.code} for methodology {method}: "
                f"total={ind.total} vs sum={declared_sum}"
            )


class TestDistinctNDAndZeroStates:
    """Verifies that undeclared modules (ND/MND) are distinct from zero-impact modules."""

    def test_undeclared_vs_zero_distinction(self, epd11017_matrix):
        # PERM is 0.0 (declared zero use)
        perm = next(ind for ind in epd11017_matrix.indicators if ind.code == "PERM")
        assert perm.modules["A1-A3"] == 0.0
        assert "A1-A3" not in perm.module_flags

        # B3 is undeclared (ND)
        assert perm.modules["B3"] is None
        assert perm.module_flags["B3"] in ["ND", "MND"]


class TestSourceTraceability:
    """Verifies provenance data attached to calculation outputs for verifier audit trust."""

    def test_b6_operational_energy_trace(self, epd11017_matrix):
        gwp = next(ind for ind in epd11017_matrix.indicators if ind.code == "GWP-total")
        b6_trace = gwp.source_trace.get("B6")
        assert b6_trace is not None
        assert "inputs" in b6_trace
        assert "data_source" in b6_trace
        assert b6_trace["inputs"]["annual_electricity_kwh"] == 688967
        assert b6_trace["inputs"]["rsl_years"] == 25
        assert "Grid Mix" in b6_trace["data_source"]

    def test_a1_a3_bom_materials_trace(self, epd11017_matrix):
        gwp = next(ind for ind in epd11017_matrix.indicators if ind.code == "GWP-total")
        a1_trace = gwp.source_trace.get("A1-A3")
        assert a1_trace is not None
        assert a1_trace["inputs"]["bom_count"] == 8
        assert "Ecoinvent" in a1_trace["data_source"]


class TestBuildIndicatorMatrixFromDbResult:
    """Verifies constructing the matrix from database result dictionaries."""

    def test_build_matrix_from_custom_result(self):
        lca_result = {
            "gwp_total_kg_co2e": {"A1": 100.0, "A2": 10.0, "A3": 5.0, "A4": 2.0, "B6": 1200.0, "C4": 0.5},
            "odp_kg_cfc11e": {"A1": 1e-6, "A2": 1e-7, "A3": 1e-8, "B6": 5e-5},
            "ap_mol_h_eq": {"A1": 0.5, "A2": 0.05, "A3": 0.02, "B6": 10.0},
        }
        project = {
            "functional_unit_quantity": 1.0,
            "functional_unit_unit": "ton_chilling_capacity",
            "active_modules": ["A1", "A2", "A3", "A4", "B6", "C4"],
            "product_lifetime_years": 25.0,
            "use_phase": {"annual_electricity_kwh": 5000.0, "electricity_grid_region": "US"},
            "bom": [{"material_name": "Steel", "mass_kg": 1000.0}],
        }
        matrix = build_indicator_matrix(lca_result, project, "EN_15804_A2")
        gwp = next(ind for ind in matrix.indicators if ind.code == "GWP-total")
        assert gwp.modules["A1-A3"] == 115.0  # 100 + 10 + 5
        assert gwp.modules["A4"] == 2.0
        assert gwp.modules["B6"] == 1200.0
        assert gwp.modules["C4"] == 0.5
        assert gwp.modules["B3"] is None
        assert gwp.module_flags["B3"] == "ND"
        assert gwp.total == 115.0 + 2.0 + 1200.0 + 0.5

    def test_traci_methodology_unit_and_factors(self):
        matrix = get_epd11017_reference_matrix("TRACI_2_1")
        ap = next(ind for ind in matrix.indicators if ind.code == "AP")
        assert ap.unit == "kg SO2e"
        assert ap.methodology == "TRACI 2 1"
