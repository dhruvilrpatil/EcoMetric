"""
engine/cutoff.py — ISO 14044 cut-off criteria enforcement.
PRD §7.4:
  - Individual omitted flow < 1% of total mass OR energy
  - Aggregate of all omitted flows < 5% of total mass OR energy
Returns CutoffResult with structured violations list.
Cut-off is enforced BEFORE calculation runs, not as a post-hoc warning.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaterialFlow:
    """Represents one material flow for cut-off evaluation."""
    name: str
    mass: float          # kg
    energy: float        # MJ
    omitted: bool        # True if this flow is excluded from the system boundary


@dataclass(frozen=True)
class CutoffViolation:
    """Details of a single cut-off rule violation."""
    flow_name: str
    violation_type: str   # 'individual_mass' | 'individual_energy' | 'aggregate_mass' | 'aggregate_energy'
    actual_pct: float
    threshold_pct: float
    message: str


@dataclass
class CutoffResult:
    """
    Structured result of cut-off criteria validation.
    compliant=True means all ISO 14044 cut-off rules are satisfied.
    """
    compliant: bool
    individual_max_mass_pct: float
    individual_max_energy_pct: float
    aggregate_mass_pct: float
    aggregate_energy_pct: float
    violations: list[CutoffViolation] = field(default_factory=list)


def validate_cutoff(
    flows: list[MaterialFlow],
    total_mass: float,
    total_energy: float,
    *,
    individual_threshold: float = 0.01,   # 1%
    aggregate_threshold: float = 0.05,    # 5%
) -> CutoffResult:
    """
    ISO 14044 / GPI cut-off rule enforcement (PRD §7.4).

    Rules:
      1. Any single omitted flow < individual_threshold of total_mass OR energy.
      2. Aggregate of all omitted flows < aggregate_threshold of total_mass OR energy.

    Parameters
    ----------
    flows : list of MaterialFlow
        All material flows in the system, omitted and included.
    total_mass : float
        Total system mass (kg). Must be > 0.
    total_energy : float
        Total system energy (MJ). Must be > 0.
    individual_threshold : float
        Maximum fraction for any single omitted flow. Default 0.01 (1%).
    aggregate_threshold : float
        Maximum aggregate fraction of all omitted flows. Default 0.05 (5%).

    Returns
    -------
    CutoffResult
        compliant=True if all rules satisfied. violations list contains details.

    Raises
    ------
    ValueError
        If total_mass or total_energy is zero or negative.
    """
    if total_mass <= 0:
        raise ValueError(f"total_mass must be > 0; got {total_mass}.")
    if total_energy <= 0:
        raise ValueError(f"total_energy must be > 0; got {total_energy}.")

    violations: list[CutoffViolation] = []
    omitted_flows = [f for f in flows if f.omitted]

    individual_max_mass_pct   = 0.0
    individual_max_energy_pct = 0.0

    # Rule 1: Individual flow checks
    for flow in omitted_flows:
        mass_pct   = flow.mass   / total_mass
        energy_pct = flow.energy / total_energy

        individual_max_mass_pct   = max(individual_max_mass_pct,   mass_pct)
        individual_max_energy_pct = max(individual_max_energy_pct, energy_pct)

        if mass_pct >= individual_threshold:
            violations.append(CutoffViolation(
                flow_name=flow.name,
                violation_type='individual_mass',
                actual_pct=round(mass_pct * 100, 4),
                threshold_pct=individual_threshold * 100,
                message=(
                    f"Flow '{flow.name}' omitted mass ({mass_pct*100:.2f}%) "
                    f"exceeds {individual_threshold*100:.0f}% individual cut-off threshold."
                ),
            ))

        if energy_pct >= individual_threshold:
            violations.append(CutoffViolation(
                flow_name=flow.name,
                violation_type='individual_energy',
                actual_pct=round(energy_pct * 100, 4),
                threshold_pct=individual_threshold * 100,
                message=(
                    f"Flow '{flow.name}' omitted energy ({energy_pct*100:.2f}%) "
                    f"exceeds {individual_threshold*100:.0f}% individual cut-off threshold."
                ),
            ))

    # Rule 2: Aggregate checks
    total_omitted_mass   = sum(f.mass   for f in omitted_flows)
    total_omitted_energy = sum(f.energy for f in omitted_flows)

    aggregate_mass_pct   = total_omitted_mass   / total_mass
    aggregate_energy_pct = total_omitted_energy / total_energy

    if aggregate_mass_pct >= aggregate_threshold:
        violations.append(CutoffViolation(
            flow_name='(aggregate)',
            violation_type='aggregate_mass',
            actual_pct=round(aggregate_mass_pct * 100, 4),
            threshold_pct=aggregate_threshold * 100,
            message=(
                f"Aggregate omitted mass ({aggregate_mass_pct*100:.2f}%) "
                f"exceeds {aggregate_threshold*100:.0f}% threshold. "
                "Omitted materials exceed the 5% aggregate cut-off threshold. "
                "Add the missing data or justify the exclusion."
            ),
        ))

    if aggregate_energy_pct >= aggregate_threshold:
        violations.append(CutoffViolation(
            flow_name='(aggregate)',
            violation_type='aggregate_energy',
            actual_pct=round(aggregate_energy_pct * 100, 4),
            threshold_pct=aggregate_threshold * 100,
            message=(
                f"Aggregate omitted energy ({aggregate_energy_pct*100:.2f}%) "
                f"exceeds {aggregate_threshold*100:.0f}% threshold."
            ),
        ))

    return CutoffResult(
        compliant=len(violations) == 0,
        individual_max_mass_pct=round(individual_max_mass_pct * 100, 4),
        individual_max_energy_pct=round(individual_max_energy_pct * 100, 4),
        aggregate_mass_pct=round(aggregate_mass_pct * 100, 4),
        aggregate_energy_pct=round(aggregate_energy_pct * 100, 4),
        violations=violations,
    )
