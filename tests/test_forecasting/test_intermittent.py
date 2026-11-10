import numpy as np
import pytest
from src.forecasting.intermittent import croston_forecast

def test_zero_series():
    np.testing.assert_array_equal(croston_forecast([0,0],3),[0,0,0])

def test_sba_bias_correction():
    a=croston_forecast([0,4,0,0,6],3,alpha=0.2)
    b=croston_forecast([0,4,0,0,6],3,alpha=0.2,sba=True)
    assert np.all(b<=a)

def test_invalid_horizon():
    with pytest.raises(ValueError): croston_forecast([1],0)
