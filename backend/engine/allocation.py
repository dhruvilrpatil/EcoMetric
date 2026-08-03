"""
engine/allocation.py — Multi-functionality partitioning method.
PRD §7.2: A_allocated = (U ∘ (A_raw.T @ ones)) @ C
          B_allocated = B_0.T @ C
"""
from __future__ import annotations
import numpy as np
from numpy.typing import NDArray


class AllocationSumError(ValueError):
    def __init__(self, process_index: int, actual_sum: float) -> None:
        self.process_index = process_index
        self.actual_sum = actual_sum
        super().__init__(
            f"Allocation factors for process {process_index} sum to "
            f"{actual_sum:.6f}, expected 1.0 (±0.001). "
            "Please review your allocation inputs."
        )


class AllocationRankError(ValueError):
    def __init__(self, rank: int, expected: int) -> None:
        super().__init__(
            f"Allocated technology matrix is rank {rank}, expected {expected}."
        )


def apply_partitioning(
    A_raw: NDArray[np.float64],
    C: NDArray[np.float64],
    B_0: NDArray[np.float64],
    U: NDArray[np.float64] | None = None,
    *,
    factor_tolerance: float = 0.001,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Apply partitioning allocation per PRD §7.2.

    Returns (A_allocated, B_allocated) — both square/full-rank verified.
    Raises AllocationSumError if C rows deviate from 1.0 by > factor_tolerance.
    Raises AllocationRankError if A_allocated is rank-deficient.
    """
    A_raw = np.asarray(A_raw, dtype=np.float64)
    C     = np.asarray(C,     dtype=np.float64)
    B_0   = np.asarray(B_0,   dtype=np.float64)

    n_flows, n_processes = A_raw.shape
    n_proc_C, n_allocated = C.shape

    if n_proc_C != n_processes:
        raise ValueError(f"C.shape[0]={n_proc_C} must equal A_raw.shape[1]={n_processes}.")
    if B_0.shape[1] != n_processes:
        raise ValueError(f"B_0.shape[1]={B_0.shape[1]} must equal A_raw.shape[1]={n_processes}.")

    # Default U to identity
    if U is None:
        U = np.eye(n_processes, dtype=np.float64)
    else:
        U = np.asarray(U, dtype=np.float64)

    # Validate allocation factor sums per process row
    row_sums = C.sum(axis=1)
    for i, row_sum in enumerate(row_sums):
        if abs(float(row_sum) - 1.0) > factor_tolerance:
            raise AllocationSumError(process_index=i, actual_sum=float(row_sum))

    # PRD formula: A_allocated = (U ∘ (A_raw.T @ ones)) @ C
    ones = np.ones((n_flows, 1), dtype=np.float64)
    inner = A_raw.T @ ones          # (n_processes, 1)
    hadamard = U * inner            # (n_processes, n_processes) broadcast
    A_allocated = hadamard @ C      # (n_processes, n_allocated)

    # Assert square
    assert A_allocated.shape[0] == A_allocated.shape[1], (
        f"A_allocated is not square: {A_allocated.shape}"
    )

    # Assert full rank
    rank = int(np.linalg.matrix_rank(A_allocated))
    expected_rank = A_allocated.shape[0]
    if rank != expected_rank:
        raise AllocationRankError(rank=rank, expected=expected_rank)

    # B_allocated = B_0.T @ C → transposed back to (n_env, n_allocated)
    B_allocated = (B_0.T @ C).T

    return A_allocated, B_allocated
