import numpy as np
import pytest
from src.uncertainty.conformal import conformal_quantile, block_residual_scores, interval_bounds


def test_finite_sample_quantile():
    # Split-conformal uses ceil((n + 1) * coverage), so the third
    # order statistic is selected for n=4 and coverage=0.5.
    assert conformal_quantile([1, 2, 3, 4], 0.5) == 3


def test_block_scores():
    np.testing.assert_allclose(block_residual_scores([1, -1, 2, 2, 3], 2), [0, 4])


def test_nonnegative_intervals():
    lo, hi = interval_bounds([1, 10], [-2, 2, -1, 1], 0.5)
    assert min(lo) >= 0 and np.all(np.asarray(hi) >= np.asarray(lo))


def test_empty_rejected():
    with pytest.raises(ValueError):
        conformal_quantile([], 0.9)
