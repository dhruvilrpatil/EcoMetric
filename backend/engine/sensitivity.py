"""
engine/sensitivity.py — Analytical perturbation sensitivity analysis.
PRD §7.3: ∂g/∂a_ij = -B @ A⁻¹ @ ΔA_ij @ A⁻¹ @ f
Flags entries > 2 std deviations above mean as HIGH_SENSITIVITY.
"""
from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass


@dataclass(frozen=True)
class SensitivityEntry:
    """Sensitivity coefficient for one (i,j) element of the technology matrix."""
    row: int
    col: int
    coefficient_norm: float   # L2-norm of the sensitivity vector ∂g/∂a_ij
    is_high_sensitivity: bool


@dataclass(frozen=True)
class SensitivityResult:
    """Complete sensitivity analysis result for all matrix elements."""
    entries: list[SensitivityEntry]
    mean_sensitivity: float
    std_sensitivity: float
    threshold: float   # mean + 2*std — entries above are HIGH_SENSITIVITY


def sensitivity_coefficient(
    B: NDArray[np.float64],
    A_inv: NDArray[np.float64],
    delta_A: NDArray[np.float64],
    f: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Compute ∂g/∂a_ij = -B @ A⁻¹ @ ΔA @ A⁻¹ @ f

    PRD §7.3 formula exactly.

    Parameters
    ----------
    B      : (n_env, n) intervention matrix
    A_inv  : (n, n) pre-computed inverse of A (computed once, reused per element)
    delta_A: (n, n) perturbation matrix with 1 at position (i,j) and 0 elsewhere
    f      : (n,) final demand vector

    Returns
    -------
    ndarray, shape (n_env,) — the sensitivity vector for this element
    """
    return -B @ A_inv @ delta_A @ A_inv @ f


def compute_all_sensitivities(
    A: NDArray[np.float64],
    B: NDArray[np.float64],
    f: NDArray[np.float64],
) -> SensitivityResult:
    """
    Compute analytical sensitivity coefficients for every element of A.

    The L2-norm of each sensitivity vector is used as the scalar measure.
    Entries with |coeff| > mean + 2*std are flagged HIGH_SENSITIVITY.

    Parameters
    ----------
    A : (n, n) technology matrix
    B : (n_env, n) intervention matrix
    f : (n,) final demand vector

    Returns
    -------
    SensitivityResult
    """
    A   = np.asarray(A, dtype=np.float64)
    B   = np.asarray(B, dtype=np.float64)
    f   = np.asarray(f, dtype=np.float64).ravel()

    n = A.shape[0]

    # Compute A_inv once (only used for sensitivity — not for the main solve)
    A_inv = np.linalg.inv(A)

    coefficients: list[float] = []
    positions: list[tuple[int, int]] = []

    for i in range(n):
        for j in range(n):
            delta_A = np.zeros((n, n), dtype=np.float64)
            delta_A[i, j] = 1.0
            sens_vec = sensitivity_coefficient(B, A_inv, delta_A, f)
            coeff_norm = float(np.linalg.norm(sens_vec))
            coefficients.append(coeff_norm)
            positions.append((i, j))

    coefficients_arr = np.array(coefficients, dtype=np.float64)
    mean_s = float(np.mean(coefficients_arr))
    std_s  = float(np.std(coefficients_arr))
    threshold = mean_s + 2.0 * std_s

    entries = [
        SensitivityEntry(
            row=pos[0],
            col=pos[1],
            coefficient_norm=coeff,
            is_high_sensitivity=(coeff > threshold),
        )
        for pos, coeff in zip(positions, coefficients)
    ]

    return SensitivityResult(
        entries=entries,
        mean_sensitivity=mean_s,
        std_sensitivity=std_s,
        threshold=threshold,
    )
