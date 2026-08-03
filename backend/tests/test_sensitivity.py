"""
tests/test_sensitivity.py
=========================
pytest unit tests for engine/sensitivity.py
"""
import numpy as np
import pytest
from engine.sensitivity import (
    sensitivity_coefficient,
    compute_all_sensitivities,
    SensitivityResult,
    SensitivityEntry,
)


@pytest.fixture
def simple_2x2():
    A = np.array([[2.0, 0.0],
                  [0.0, 3.0]])
    B = np.array([[1.0, 0.0],
                  [0.0, 1.0]])
    f = np.array([1.0, 0.0])
    return A, B, f


class TestSensitivityCoefficient:

    def test_returns_correct_shape(self, simple_2x2):
        A, B, f = simple_2x2
        A_inv = np.linalg.inv(A)
        delta_A = np.zeros_like(A)
        delta_A[0, 0] = 1.0
        result = sensitivity_coefficient(B, A_inv, delta_A, f)
        assert result.shape == (B.shape[0],)

    def test_analytical_value(self, simple_2x2):
        """
        For A=diag(2,3), B=I2, f=[1,0]:
          A_inv = diag(0.5, 1/3)
          delta_A[0,0]=1:
            A_inv @ f = [0.5, 0]
            delta_A @ (A_inv @ f) = [0.5, 0]  (delta_A[0,0]=1 picks row 0)
            A_inv @ [0.5, 0] = [0.25, 0]
            -B @ [0.25, 0] = -[0.25, 0] = [-0.25, 0]
        """
        A, B, f = simple_2x2
        A_inv = np.linalg.inv(A)
        delta_A = np.zeros_like(A)
        delta_A[0, 0] = 1.0
        result = sensitivity_coefficient(B, A_inv, delta_A, f)
        np.testing.assert_allclose(result, [-0.25, 0.0], rtol=1e-10)

    def test_zero_perturbation_gives_zero(self, simple_2x2):
        A, B, f = simple_2x2
        A_inv = np.linalg.inv(A)
        delta_A = np.zeros_like(A)  # no perturbation
        result = sensitivity_coefficient(B, A_inv, delta_A, f)
        np.testing.assert_allclose(result, np.zeros(B.shape[0]), atol=1e-15)


class TestComputeAllSensitivities:

    def test_returns_correct_entry_count(self, simple_2x2):
        A, B, f = simple_2x2
        result = compute_all_sensitivities(A, B, f)
        assert isinstance(result, SensitivityResult)
        assert len(result.entries) == A.shape[0] ** 2  # n² entries

    def test_all_entries_have_correct_types(self, simple_2x2):
        A, B, f = simple_2x2
        result = compute_all_sensitivities(A, B, f)
        for entry in result.entries:
            assert isinstance(entry, SensitivityEntry)
            assert isinstance(entry.coefficient_norm, float)
            assert isinstance(entry.is_high_sensitivity, bool)

    def test_threshold_is_mean_plus_2std(self, simple_2x2):
        A, B, f = simple_2x2
        result = compute_all_sensitivities(A, B, f)
        expected_threshold = result.mean_sensitivity + 2.0 * result.std_sensitivity
        assert abs(result.threshold - expected_threshold) < 1e-12

    def test_high_sensitivity_flags_match_threshold(self, simple_2x2):
        A, B, f = simple_2x2
        result = compute_all_sensitivities(A, B, f)
        for entry in result.entries:
            if entry.coefficient_norm > result.threshold:
                assert entry.is_high_sensitivity, (
                    f"Entry ({entry.row},{entry.col}) coeff={entry.coefficient_norm} "
                    f"above threshold={result.threshold} but not flagged."
                )
            # Note: entries exactly AT threshold might not be flagged (strict >)

    def test_larger_system_runs(self):
        """4×4 system completes without error."""
        rng = np.random.default_rng(42)
        n = 4
        A = np.eye(n) + rng.random((n, n)) * 0.1  # diagonally dominant → invertible
        B = rng.random((6, n))
        f = np.zeros(n); f[0] = 1.0
        result = compute_all_sensitivities(A, B, f)
        assert len(result.entries) == n * n
