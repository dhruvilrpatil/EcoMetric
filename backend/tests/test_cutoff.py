"""
tests/test_cutoff.py
====================
pytest unit tests for engine/cutoff.py
"""
import pytest
from engine.cutoff import (
    validate_cutoff,
    MaterialFlow,
    CutoffResult,
    CutoffViolation,
)


def make_flow(name: str, mass: float, energy: float, omitted: bool) -> MaterialFlow:
    return MaterialFlow(name=name, mass=mass, energy=energy, omitted=omitted)


class TestValidateCutoff:

    def test_all_flows_included_is_compliant(self):
        flows = [
            make_flow("Steel", mass=100.0, energy=500.0, omitted=False),
            make_flow("Concrete", mass=50.0, energy=200.0, omitted=False),
        ]
        result = validate_cutoff(flows, total_mass=150.0, total_energy=700.0)
        assert result.compliant is True
        assert result.violations == []

    def test_small_omission_is_compliant(self):
        """Omitted flow at 0.5% individual (< 1%) and 0.5% aggregate (< 5%)."""
        flows = [
            make_flow("Steel",   mass=990.0, energy=900.0, omitted=False),
            make_flow("Adhesive", mass=5.0,  energy=5.0,   omitted=True),
            # total mass=995, omitted mass pct = 5/995 ≈ 0.5%
        ]
        result = validate_cutoff(flows, total_mass=995.0, total_energy=905.0)
        assert result.compliant is True

    def test_individual_mass_violation_at_exactly_1pct(self):
        """Omitted flow at exactly 1% should trigger violation (>= threshold)."""
        flows = [
            make_flow("Steel",   mass=990.0, energy=900.0, omitted=False),
            make_flow("Adhesive", mass=10.0, energy=1.0,   omitted=True),
        ]
        # 10/1000 = 1% — should trigger
        result = validate_cutoff(flows, total_mass=1000.0, total_energy=901.0)
        assert result.compliant is False
        types = [v.violation_type for v in result.violations]
        assert 'individual_mass' in types

    def test_aggregate_mass_violation(self):
        """Multiple small omitted flows whose aggregate exceeds 5%."""
        flows = [
            make_flow("Main",  mass=900.0, energy=800.0, omitted=False),
            make_flow("Part1", mass=20.0,  energy=10.0,  omitted=True),
            make_flow("Part2", mass=20.0,  energy=10.0,  omitted=True),
            make_flow("Part3", mass=20.0,  energy=10.0,  omitted=True),
        ]
        # aggregate omitted mass = 60/960 ≈ 6.25%  → violation
        result = validate_cutoff(flows, total_mass=960.0, total_energy=830.0)
        assert result.compliant is False
        types = [v.violation_type for v in result.violations]
        assert 'aggregate_mass' in types

    def test_aggregate_within_threshold_is_compliant(self):
        """Three omitted flows with aggregate < 5% AND each individual < 1%."""
        flows = [
            make_flow("Main", mass=970.0, energy=900.0, omitted=False),
            make_flow("P1",   mass=3.0,   energy=2.0,   omitted=True),   # 0.3%
            make_flow("P2",   mass=3.0,   energy=2.0,   omitted=True),   # 0.3%
            make_flow("P3",   mass=4.0,   energy=2.0,   omitted=True),   # 0.4%
        ]
        # aggregate mass = 10/980 ≈ 1.02% < 5%  AND each individual < 1%
        result = validate_cutoff(flows, total_mass=980.0, total_energy=906.0)
        assert result.compliant is True, f"Unexpected violations: {result.violations}"

    def test_zero_total_mass_raises(self):
        flows = [make_flow("Steel", mass=100.0, energy=100.0, omitted=False)]
        with pytest.raises(ValueError, match="total_mass"):
            validate_cutoff(flows, total_mass=0.0, total_energy=100.0)

    def test_zero_total_energy_raises(self):
        flows = [make_flow("Steel", mass=100.0, energy=100.0, omitted=False)]
        with pytest.raises(ValueError, match="total_energy"):
            validate_cutoff(flows, total_mass=100.0, total_energy=0.0)

    def test_result_contains_accurate_percentages(self):
        flows = [
            make_flow("Main",  mass=990.0, energy=990.0, omitted=False),
            make_flow("Trace", mass=5.0,   energy=5.0,   omitted=True),
        ]
        result = validate_cutoff(flows, total_mass=995.0, total_energy=995.0)
        expected_pct = round(5.0 / 995.0 * 100, 4)
        assert abs(result.aggregate_mass_pct - expected_pct) < 1e-3

    def test_violation_object_structure(self):
        flows = [
            make_flow("Steel",   mass=980.0, energy=900.0, omitted=False),
            make_flow("Adhesive", mass=20.0, energy=5.0,   omitted=True),
        ]
        result = validate_cutoff(flows, total_mass=1000.0, total_energy=905.0)
        assert result.compliant is False
        assert len(result.violations) >= 1
        v = result.violations[0]
        assert isinstance(v, CutoffViolation)
        assert v.flow_name == "Adhesive"
        assert v.actual_pct > v.threshold_pct

    def test_custom_thresholds(self):
        """Custom thresholds (e.g., 2% individual, 10% aggregate)."""
        flows = [
            make_flow("Main",  mass=900.0, energy=800.0, omitted=False),
            make_flow("Small", mass=15.0,  energy=5.0,   omitted=True),
        ]
        # 15/915 ≈ 1.6% < 2% custom threshold → compliant
        result = validate_cutoff(
            flows,
            total_mass=915.0,
            total_energy=805.0,
            individual_threshold=0.02,
            aggregate_threshold=0.10,
        )
        assert result.compliant is True

    def test_energy_violation_only(self):
        """Flow with tiny mass but huge energy share triggers energy violation."""
        flows = [
            make_flow("Main",        mass=990.0, energy=100.0, omitted=False),
            make_flow("Electricity", mass=1.0,   energy=50.0,  omitted=True),
        ]
        # mass pct: 1/991 ≈ 0.1% < 1% ✓
        # energy pct: 50/150 ≈ 33% > 1% ✗
        result = validate_cutoff(flows, total_mass=991.0, total_energy=150.0)
        assert result.compliant is False
        types = [v.violation_type for v in result.violations]
        assert 'individual_energy' in types
