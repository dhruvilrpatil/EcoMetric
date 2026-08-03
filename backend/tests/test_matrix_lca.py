"""
tests/test_matrix_lca.py
========================
pytest unit tests for engine/matrix_lca.py

Tests verify:
  - solve_scaling_vector returns correct s given known A and f
  - compute_inventory returns correct g
  - compute_impact returns correct h
  - validate_matrix_invertibility raises SingularMatrixError for ill-conditioned A
  - run_lca is deterministic (bit-identical for same inputs)
  - sparse solver path returns same result as dense path
  - dimension mismatch raises MatrixDimensionMismatch
"""

import numpy as np
import pytest
from scipy.sparse import csc_matrix

from engine.matrix_lca import (
    solve_scaling_vector,
    compute_inventory,
    compute_impact,
    validate_matrix_invertibility,
    run_lca,
    SingularMatrixError,
    MatrixDimensionMismatch,
    LCAMatrices,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — small, analytically solvable LCA systems
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_system():
    """
    2-process, 2-flow system with known analytical solution.

    A = [[2, 0],    f = [1, 0]   → s = [0.5, 0]
         [0, 3]]

    B = [[1, 2],    → g = B @ s = [0.5, 1.0, 0]
         [0, 1],
         [0, 0]]

    Q = [[1, 0, 1], → h = Q @ g = [0.5, 1.0]
         [0, 1, 0]]
    """
    A = np.array([[2.0, 0.0],
                  [0.0, 3.0]])
    B = np.array([[1.0, 2.0],
                  [0.0, 1.0],
                  [0.0, 0.0]])
    Q = np.array([[1.0, 0.0, 1.0],
                  [0.0, 1.0, 0.0]])
    f = np.array([1.0, 0.0])
    return A, B, Q, f


@pytest.fixture
def linked_system():
    """
    3-process system with process linkages (off-diagonal A elements).
    Supply chain: Process 1 produces 1 unit; Process 2 requires 0.5 units from Process 1.

    A = [[1, -0.5, 0 ],
         [0,  1,  -0.3],
         [0,  0,   1 ]]

    f = [1, 0, 0]

    Analytical s:
      s[2] = 0
      s[1] = 0
      s[0] = 1
    """
    A = np.array([
        [ 1.0, -0.5,  0.0],
        [ 0.0,  1.0, -0.3],
        [ 0.0,  0.0,  1.0],
    ])
    B = np.array([
        [2.0, 1.0, 0.5],
        [0.0, 3.0, 0.0],
    ])
    Q = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
    ])
    f = np.array([1.0, 0.0, 0.0])
    return A, B, Q, f


# ─────────────────────────────────────────────────────────────────────────────
# validate_matrix_invertibility
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateMatrixInvertibility:

    def test_well_conditioned_matrix_does_not_raise(self, simple_system):
        A, *_ = simple_system
        cond = validate_matrix_invertibility(A)
        assert cond < 1e12

    def test_singular_matrix_raises_singular_error(self):
        # Singular matrix (rank 1) — cond number is infinite
        A = np.array([[1.0, 1.0],
                      [1.0, 1.0]])
        with pytest.raises(SingularMatrixError) as exc_info:
            validate_matrix_invertibility(A)
        assert exc_info.value.condition_number > 1e12

    def test_near_singular_raises_singular_error(self):
        # Near-singular: second row is almost a multiple of first
        A = np.array([[1.0,     2.0     ],
                      [1.0,     2.0 + 1e-15]])
        with pytest.raises(SingularMatrixError):
            validate_matrix_invertibility(A)

    def test_non_square_raises_dimension_mismatch(self):
        A = np.array([[1.0, 2.0, 3.0],
                      [4.0, 5.0, 6.0]])
        with pytest.raises(MatrixDimensionMismatch):
            validate_matrix_invertibility(A)

    def test_returns_condition_number(self, simple_system):
        A, *_ = simple_system
        cond = validate_matrix_invertibility(A)
        # A = diag(2, 3) — condition number = 3/2 = 1.5
        assert abs(cond - 1.5) < 1e-10


# ─────────────────────────────────────────────────────────────────────────────
# solve_scaling_vector
# ─────────────────────────────────────────────────────────────────────────────

class TestSolveScalingVector:

    def test_simple_diagonal_system(self, simple_system):
        A, B, Q, f = simple_system
        s = solve_scaling_vector(A, f)
        expected = np.array([0.5, 0.0])
        np.testing.assert_allclose(s, expected, rtol=1e-12)

    def test_linked_system(self, linked_system):
        A, B, Q, f = linked_system
        s = solve_scaling_vector(A, f)
        # s[0]=1, s[1]=0, s[2]=0 for f=[1,0,0]
        np.testing.assert_allclose(s, [1.0, 0.0, 0.0], atol=1e-12)

    def test_singular_A_raises(self):
        A = np.array([[1.0, 1.0], [1.0, 1.0]])
        f = np.array([1.0, 0.0])
        with pytest.raises(SingularMatrixError):
            solve_scaling_vector(A, f)

    def test_dimension_mismatch_raises(self, simple_system):
        A, B, Q, f = simple_system
        f_wrong = np.array([1.0, 0.0, 0.0])  # size 3 vs A size 2
        with pytest.raises(MatrixDimensionMismatch):
            solve_scaling_vector(A, f_wrong)

    def test_sparse_path_matches_dense(self, linked_system):
        """sparse_threshold=0 forces sparse solver; result must match dense."""
        A, B, Q, f = linked_system
        s_dense  = solve_scaling_vector(A, f, sparse_threshold=9999)
        s_sparse = solve_scaling_vector(A, f, sparse_threshold=0)
        np.testing.assert_allclose(s_dense, s_sparse, rtol=1e-10)

    def test_column_vector_f_accepted(self, simple_system):
        """f as (n,1) column vector should be accepted and flattened."""
        A, B, Q, f = simple_system
        f_col = f.reshape(-1, 1)
        s = solve_scaling_vector(A, f_col)
        np.testing.assert_allclose(s, [0.5, 0.0], rtol=1e-12)


# ─────────────────────────────────────────────────────────────────────────────
# compute_inventory
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeInventory:

    def test_correct_result(self, simple_system):
        A, B, Q, f = simple_system
        s = np.array([0.5, 0.0])
        g = compute_inventory(B, s)
        # B @ [0.5, 0] = [0.5, 0, 0]
        np.testing.assert_allclose(g, [0.5, 0.0, 0.0], rtol=1e-12)

    def test_linked_system_inventory(self, linked_system):
        A, B, Q, f = linked_system
        s = np.array([1.0, 0.0, 0.0])
        g = compute_inventory(B, s)
        # B = [[2,1,0.5],[0,3,0]] → B @ [1,0,0] = [2, 0]
        np.testing.assert_allclose(g, [2.0, 0.0], rtol=1e-12)

    def test_dimension_mismatch_raises(self):
        B = np.eye(3)
        s = np.array([1.0, 2.0])   # s size 2, B needs 3
        with pytest.raises(MatrixDimensionMismatch):
            compute_inventory(B, s)

    def test_non_2d_B_raises(self):
        B = np.array([1.0, 2.0, 3.0])  # 1-D
        s = np.array([1.0])
        with pytest.raises(MatrixDimensionMismatch):
            compute_inventory(B, s)


# ─────────────────────────────────────────────────────────────────────────────
# compute_impact
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeImpact:

    def test_correct_result(self, simple_system):
        A, B, Q, f = simple_system
        g = np.array([0.5, 0.0, 0.0])
        h = compute_impact(Q, g)
        # Q = [[1,0,1],[0,1,0]] → Q @ [0.5,0,0] = [0.5, 0]
        np.testing.assert_allclose(h, [0.5, 0.0], rtol=1e-12)

    def test_dimension_mismatch_raises(self):
        Q = np.array([[1.0, 0.0], [0.0, 1.0]])
        g = np.array([1.0, 2.0, 3.0])  # size 3, Q needs 2
        with pytest.raises(MatrixDimensionMismatch):
            compute_impact(Q, g)


# ─────────────────────────────────────────────────────────────────────────────
# run_lca — integration test + determinism
# ─────────────────────────────────────────────────────────────────────────────

class TestRunLCA:

    def test_full_pipeline_simple(self, simple_system):
        A, B, Q, f = simple_system
        result = run_lca(A, B, Q, f)

        assert isinstance(result, LCAMatrices)
        np.testing.assert_allclose(result.s, [0.5, 0.0], rtol=1e-12)
        np.testing.assert_allclose(result.g, [0.5, 0.0, 0.0], rtol=1e-12)
        np.testing.assert_allclose(result.h, [0.5, 0.0], rtol=1e-12)

    def test_determinism_identical_inputs(self, linked_system):
        """Same inputs must produce bit-identical results — PRD critical rule."""
        A, B, Q, f = linked_system
        result1 = run_lca(A, B, Q, f)
        result2 = run_lca(A, B, Q, f)

        # Bit-identical: use array_equal, not allclose
        assert np.array_equal(result1.s, result2.s), "s not bit-identical"
        assert np.array_equal(result1.g, result2.g), "g not bit-identical"
        assert np.array_equal(result1.h, result2.h), "h not bit-identical"

    def test_condition_number_logged(self, simple_system):
        A, B, Q, f = simple_system
        result = run_lca(A, B, Q, f)
        assert result.condition_number > 0
        assert result.condition_number < 1e12

    def test_singular_A_raises(self):
        A = np.array([[1.0, 1.0], [1.0, 1.0]])
        B = np.eye(2)
        Q = np.eye(2)
        f = np.array([1.0, 0.0])
        with pytest.raises(SingularMatrixError):
            run_lca(A, B, Q, f)

    def test_all_matrices_in_result(self, simple_system):
        """All intermediate matrices present in result for audit trace."""
        A, B, Q, f = simple_system
        result = run_lca(A, B, Q, f)
        assert result.A is not None
        assert result.B is not None
        assert result.Q is not None
        assert result.f is not None
        assert result.s is not None
        assert result.g is not None
        assert result.h is not None
