"""
engine/matrix_lca.py
====================
Core matrix-based LCA computation engine.

Implements PRD §7.1 Core Matrix Model:
  s = A⁻¹ @ f          (scaling vector via solve — not explicit inversion)
  g = B @ s             (inventory vector)
  h = Q @ g             (impact vector)

All functions are deterministic: same inputs → bit-identical output.
Intermediate matrices A, B, s, g, h are returned for Firestore audit logging.
Uses scipy.sparse.linalg.spsolve for large sparse systems (n > 1000 processes).

Author: EcoMetric Engineering
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import issparse, csc_matrix
from scipy.sparse.linalg import spsolve
from typing import NamedTuple


# ─────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ─────────────────────────────────────────────────────────────────────────────

class SingularMatrixError(ValueError):
    """
    Raised when the technology matrix A is singular or near-singular.
    PRD §14.1: condition number check — raise if cond(A) > 1e12.
    """
    def __init__(self, condition_number: float) -> None:
        self.condition_number = condition_number
        super().__init__(
            f"Technology matrix A is singular (condition number: {condition_number:.3e}). "
            "The supply chain model contains a circular dependency that cannot be resolved. "
            "Check for duplicate processes."
        )


class MatrixDimensionMismatch(ValueError):
    """
    Raised when matrix dimensions are incompatible for LCA operations.
    PRD §14.1: internal error — logged, not exposed to user.
    """


# ─────────────────────────────────────────────────────────────────────────────
# Result containers
# ─────────────────────────────────────────────────────────────────────────────

class LCAMatrices(NamedTuple):
    """
    Immutable container for all intermediate LCA matrices.
    Every field is persisted to Firestore for verifier audit trace.
    """
    A: NDArray[np.float64]           # Technology matrix (n_flows × n_processes)
    B: NDArray[np.float64]           # Intervention matrix (n_env × n_processes)
    Q: NDArray[np.float64]           # Characterization matrix (n_impacts × n_env)
    f: NDArray[np.float64]           # Final demand vector (n_flows,)
    s: NDArray[np.float64]           # Scaling vector (n_processes,)
    g: NDArray[np.float64]           # Inventory vector (n_env,)
    h: NDArray[np.float64]           # Impact vector (n_impacts,)
    condition_number: float           # Logged for audit; checked before solve


# ─────────────────────────────────────────────────────────────────────────────
# Core functions
# ─────────────────────────────────────────────────────────────────────────────

def validate_matrix_invertibility(A: NDArray[np.float64]) -> float:
    """
    Compute the condition number of A and raise SingularMatrixError if > 1e12.

    PRD §7.1 requirement:
        "Validate matrix invertibility (check condition number) before solve;
         raise SingularMatrixError if cond(A) > 1e12."

    Parameters
    ----------
    A : ndarray, shape (n, n)
        The technology matrix.

    Returns
    -------
    float
        The condition number (1-norm). Safe to log to Firestore.

    Raises
    ------
    SingularMatrixError
        If cond(A) > 1e12.
    MatrixDimensionMismatch
        If A is not square.
    """
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise MatrixDimensionMismatch(
            f"Technology matrix A must be square; got shape {A.shape}."
        )

    # Use 1-norm condition number estimate (fast, O(n²) instead of O(n³))
    try:
        cond = float(np.linalg.cond(A, p=1))
    except np.linalg.LinAlgError:
        raise SingularMatrixError(condition_number=float("inf"))

    if cond > 1e12 or np.isinf(cond) or np.isnan(cond):
        raise SingularMatrixError(condition_number=cond)

    return cond



def solve_scaling_vector(
    A: NDArray[np.float64],
    f: NDArray[np.float64],
    *,
    sparse_threshold: int = 1000,
) -> NDArray[np.float64]:
    """
    Solve for the scaling vector s = A⁻¹ @ f.

    Uses np.linalg.solve for dense systems (n ≤ sparse_threshold) and
    scipy.sparse.linalg.spsolve for large sparse systems (n > sparse_threshold).

    PRD §7.1:
        "Use scipy.sparse for sparse matrix storage when n_processes > 1000.
         Use scipy.sparse.linalg.spsolve for sparse system solving."

    Parameters
    ----------
    A : ndarray, shape (n, n)
        Technology matrix (must be square and invertible).
    f : ndarray, shape (n,) or (n, 1)
        Final demand vector.
    sparse_threshold : int
        Switch to sparse solver when n > this value.

    Returns
    -------
    ndarray, shape (n,)
        Scaling vector s.

    Raises
    ------
    SingularMatrixError
        If cond(A) > 1e12.
    MatrixDimensionMismatch
        If dimensions are incompatible.
    """
    # Validate and normalize shapes
    A = np.asarray(A, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64).ravel()

    if A.shape[0] != A.shape[1]:
        raise MatrixDimensionMismatch(
            f"A must be square; got {A.shape}."
        )
    if A.shape[1] != f.shape[0]:
        raise MatrixDimensionMismatch(
            f"A.shape[1]={A.shape[1]} must equal len(f)={f.shape[0]}."
        )

    # Invertibility check before solve
    validate_matrix_invertibility(A)

    n = A.shape[0]

    if n > sparse_threshold or issparse(A):
        # Sparse path — convert to CSC for efficient column slicing
        A_sparse = csc_matrix(A) if not issparse(A) else A.tocsc()
        s = spsolve(A_sparse, f)
    else:
        # Dense path — numerically stable LU factorization
        s = np.linalg.solve(A, f)

    return s.astype(np.float64)


def compute_inventory(
    B: NDArray[np.float64],
    s: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Compute the lifecycle inventory vector g = B @ s.

    Equivalent to B @ A⁻¹ @ f (the full LCI result vector).

    Parameters
    ----------
    B : ndarray, shape (n_env_flows, n_processes)
        Intervention matrix — element b_kj is the direct emission/extraction
        k associated with unit process j.
    s : ndarray, shape (n_processes,)
        Scaling vector from solve_scaling_vector.

    Returns
    -------
    ndarray, shape (n_env_flows,)
        Inventory vector g.

    Raises
    ------
    MatrixDimensionMismatch
        If B.shape[1] ≠ len(s).
    """
    B = np.asarray(B, dtype=np.float64)
    s = np.asarray(s, dtype=np.float64).ravel()

    if B.ndim != 2:
        raise MatrixDimensionMismatch(f"B must be 2-D; got {B.ndim}-D.")
    if B.shape[1] != s.shape[0]:
        raise MatrixDimensionMismatch(
            f"B.shape[1]={B.shape[1]} must equal len(s)={s.shape[0]}."
        )

    g = B @ s
    return g.astype(np.float64)


def compute_impact(
    Q: NDArray[np.float64],
    g: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Apply characterization matrix: h = Q @ g.

    Equivalent to Q @ B @ A⁻¹ @ f.

    Parameters
    ----------
    Q : ndarray, shape (n_impact_categories, n_env_flows)
        Characterization matrix — impact characterization factors (EF 3.1).
    g : ndarray, shape (n_env_flows,)
        Inventory vector from compute_inventory.

    Returns
    -------
    ndarray, shape (n_impact_categories,)
        Impact vector h — values that populate the EPD LCIA results table.

    Raises
    ------
    MatrixDimensionMismatch
        If Q.shape[1] ≠ len(g).
    """
    Q = np.asarray(Q, dtype=np.float64)
    g = np.asarray(g, dtype=np.float64).ravel()

    if Q.ndim != 2:
        raise MatrixDimensionMismatch(f"Q must be 2-D; got {Q.ndim}-D.")
    if Q.shape[1] != g.shape[0]:
        raise MatrixDimensionMismatch(
            f"Q.shape[1]={Q.shape[1]} must equal len(g)={g.shape[0]}."
        )

    h = Q @ g
    return h.astype(np.float64)


def run_lca(
    A: NDArray[np.float64],
    B: NDArray[np.float64],
    Q: NDArray[np.float64],
    f: NDArray[np.float64],
    *,
    sparse_threshold: int = 1000,
) -> LCAMatrices:
    """
    Execute the complete LCA computation sequence and return all matrices.

    Sequence:
        1. s = solve(A, f)       — scaling vector
        2. g = B @ s             — inventory vector
        3. h = Q @ g             — impact vector

    All intermediate matrices are returned in an LCAMatrices named tuple
    for Firestore audit logging (PRD §7.1 requirement).

    Parameters
    ----------
    A : ndarray, shape (n, n)
    B : ndarray, shape (n_env, n)
    Q : ndarray, shape (n_impacts, n_env)
    f : ndarray, shape (n,)
    sparse_threshold : int

    Returns
    -------
    LCAMatrices
        Named tuple with fields: A, B, Q, f, s, g, h, condition_number.

    Raises
    ------
    SingularMatrixError, MatrixDimensionMismatch
    """
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    Q = np.asarray(Q, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)

    # Step 1 — validate invertibility, then solve for s
    cond = validate_matrix_invertibility(A)
    s = solve_scaling_vector(A, f, sparse_threshold=sparse_threshold)

    # Step 2 — inventory
    g = compute_inventory(B, s)

    # Step 3 — characterization
    h = compute_impact(Q, g)

    return LCAMatrices(
        A=A, B=B, Q=Q, f=f.ravel(),
        s=s, g=g, h=h,
        condition_number=cond,
    )


def build_lca_matrices(project_data: dict) -> tuple[NDArray[np.float64], NDArray[np.float64], list[str]]:
    """
    Build technology matrix A and intervention matrix B from project data,
    appending transport columns for A2, A4, and C2.
    """
    column_labels = ["material_assembly"]
    
    # Base A matrix (1x1 for single assembly process)
    A = np.eye(1, dtype=np.float64)
    B = np.zeros((10, 1), dtype=np.float64) # 10 elementary flows
    
    transport_data = project_data.get('transportation_data')
    if transport_data:
        from engine.transport_module import TransportModule, TransportSegment
        engine = TransportModule()
        a2_segments = [TransportSegment(**s) for s in transport_data.get('a2_segments', [])]
        a4_segment = TransportSegment(**transport_data['a4_segment']) if transport_data.get('a4_segment') else None
        c2_segment = TransportSegment(**transport_data['c2_segment']) if transport_data.get('c2_segment') else None

        totals = engine.calculate_module_totals(a2_segments, a4_segment, c2_segment)

        for module_name, module_data in totals.items():
            column_labels.append(f"transport_{module_name}")
            # Expand A matrix by 1 row and 1 column (identity entry for unit process)
            n_curr = A.shape[0]
            new_A = np.eye(n_curr + 1, dtype=np.float64)
            new_A[:n_curr, :n_curr] = A
            A = new_A
            
            # Append column to B with transport GWP / elementary emissions
            gwp_val = float(module_data.get('gwp_total_kgco2e', 0.0))
            col_b = np.zeros((10, 1), dtype=np.float64)
            col_b[0, 0] = gwp_val  # CO2 fossil flow row
            B = np.hstack([B, col_b])

    return A, B, column_labels


def build_a3_manufacturing_rows(manufacturing_data: dict) -> dict:
    """
    Convert A3 manufacturing inputs into elementary exchange contributions,
    to be merged into the B matrix's A3 column alongside existing electricity
    and material-processing impacts.

    Follows the same pattern as transport_module.py's calculate_segment_impact() —
    returns a dict of {elementary_flow_name: value}, mergeable into the existing
    matrix construction without a separate code path.
    """
    exchanges = {}

    if manufacturing_data.get('natural_gas_consumption_mj'):
        exchanges['natural_gas_combustion_mj'] = float(manufacturing_data['natural_gas_consumption_mj'])

    if manufacturing_data.get('diesel_consumption_mj'):
        exchanges['diesel_combustion_mj'] = float(manufacturing_data['diesel_consumption_mj'])

    if manufacturing_data.get('manufacturing_waste_kg'):
        exchanges[f"waste_{manufacturing_data.get('manufacturing_waste_disposal_route', 'mixed')}_kg"] = \
            float(manufacturing_data['manufacturing_waste_kg'])

    if manufacturing_data.get('scrap_generated_kg'):
        scrap_rate = float(manufacturing_data.get('scrap_recycling_rate_pct', 0)) / 100.0
        net_scrap_to_waste = float(manufacturing_data['scrap_generated_kg']) * (1.0 - scrap_rate)
        exchanges['scrap_waste_kg'] = net_scrap_to_waste

    if manufacturing_data.get('process_water_consumption_m3'):
        exchanges['water_consumption_m3'] = float(manufacturing_data['process_water_consumption_m3'])

    if manufacturing_data.get('compressed_air_energy_mj') and \
       manufacturing_data.get('compressed_air_already_in_electricity') is False:
        exchanges['compressed_air_energy_mj'] = float(manufacturing_data['compressed_air_energy_mj'])

    for emission in manufacturing_data.get('process_emissions', []):
        if isinstance(emission, dict) and emission.get('substance_name') and emission.get('emission_kg'):
            exchanges[f"process_emission_{emission['substance_name']}_kg"] = float(emission['emission_kg'])

    return exchanges


