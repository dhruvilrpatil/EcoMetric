"""
tests/test_allocation.py
========================
pytest unit tests for engine/allocation.py
"""
import numpy as np
import pytest
from engine.allocation import (
    apply_partitioning,
    AllocationSumError,
    AllocationRankError,
)


@pytest.fixture
def simple_allocation():
    """
    2-flow, 2-process system that produces 2 co-products.
    Allocation: 60% to product A, 40% to product B.
    """
    # A_raw: 2 flows, 2 processes
    A_raw = np.array([
        [2.0, 0.0],
        [0.0, 3.0],
    ])
    # C: allocation matrix — 2 processes, 2 allocated outputs
    # Each row (process) sums to 1.0, rows are DIFFERENT so A_allocated is full-rank
    C = np.array([
        [0.6, 0.4],   # process 0: 60% to product A, 40% to product B
        [0.3, 0.7],   # process 1: 30% to product A, 70% to product B  (different!)
    ])
    # B_0: 2 env flows, 2 processes
    B_0 = np.array([
        [1.0, 2.0],
        [0.5, 1.5],
    ])
    return A_raw, C, B_0


class TestApplyPartitioning:

    def test_returns_square_allocated_matrix(self, simple_allocation):
        A_raw, C, B_0 = simple_allocation
        A_alloc, B_alloc = apply_partitioning(A_raw, C, B_0)
        assert A_alloc.shape[0] == A_alloc.shape[1], "A_allocated must be square"

    def test_b_allocated_shape(self, simple_allocation):
        A_raw, C, B_0 = simple_allocation
        A_alloc, B_alloc = apply_partitioning(A_raw, C, B_0)
        # B_alloc should be (n_env, n_allocated) = (2, 2)
        assert B_alloc.shape == (B_0.shape[0], C.shape[1])

    def test_allocation_sum_error_raised(self, simple_allocation):
        """Row of C that doesn't sum to 1.0 within tolerance should raise."""
        A_raw, C, B_0 = simple_allocation
        C_bad = C.copy()
        C_bad[0, 0] = 0.7  # now row 0 sums to 1.1
        with pytest.raises(AllocationSumError) as exc_info:
            apply_partitioning(A_raw, C_bad, B_0)
        assert exc_info.value.process_index == 0

    def test_allocation_factors_at_tolerance_boundary(self, simple_allocation):
        """Row summing to 1.0005 should not raise (within 0.001 tolerance)."""
        A_raw, C, B_0 = simple_allocation
        C_edge = C.copy()
        C_edge[0] = [0.6004, 0.4001]  # sum = 1.0005
        # Should not raise
        apply_partitioning(A_raw, C_edge, B_0)

    def test_allocation_factors_outside_tolerance_raises(self, simple_allocation):
        A_raw, C, B_0 = simple_allocation
        C_bad = C.copy()
        C_bad[1] = [0.3, 0.3]  # sum = 0.6, deviation 0.4 >> 0.001
        with pytest.raises(AllocationSumError) as exc_info:
            apply_partitioning(A_raw, C_bad, B_0)
        assert exc_info.value.process_index == 1

    def test_dimension_mismatch_C_rows(self, simple_allocation):
        A_raw, C, B_0 = simple_allocation
        C_wrong = np.array([[0.6, 0.4], [0.6, 0.4], [0.6, 0.4]])  # 3 rows vs 2 processes
        with pytest.raises(ValueError, match="C.shape"):
            apply_partitioning(A_raw, C_wrong, B_0)

    def test_dimension_mismatch_B_cols(self, simple_allocation):
        A_raw, C, B_0 = simple_allocation
        B_wrong = np.ones((2, 3))  # 3 cols vs 2 processes
        with pytest.raises(ValueError, match="B_0.shape"):
            apply_partitioning(A_raw, C, B_wrong)  # B_wrong has wrong number of columns

    def test_identity_allocation_preserves_values(self):
        """C = identity → A_allocated == A (for square A)."""
        A_raw = np.array([[2.0, 1.0],
                          [0.0, 3.0]])
        C = np.eye(2)
        B_0 = np.eye(2)
        A_alloc, _ = apply_partitioning(A_raw, C, B_0)
        # With C=I and U=I, result is diag(col_sums(A_raw)) @ I
        # col sums of A_raw: [2, 4] → diag([2,4])
        expected_diag = np.diag([2.0 + 0.0, 1.0 + 3.0])
        np.testing.assert_allclose(A_alloc, expected_diag, rtol=1e-12)

    def test_full_rank_assertion_on_degenerate_C(self):
        """Zero-column in C produces rank-deficient A_allocated."""
        A_raw = np.array([[1.0, 0.0],
                          [0.0, 1.0]])
        # C with zero column → rank 1
        C = np.array([[1.0, 0.0],
                      [1.0, 0.0]])  # sum check: both rows sum to 1 ✓, but produces rank-1
        B_0 = np.eye(2)
        with pytest.raises(AllocationRankError):
            apply_partitioning(A_raw, C, B_0)
