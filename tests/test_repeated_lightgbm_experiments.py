import numpy as np
import pandas as pd
import pytest
from scripts.run_repeated_lightgbm_experiments import _allocate, stratified_sample

def test_allocation_exact_and_capacity_safe():
    sizes=np.array([3,10,20,100])
    allocation=_allocate(sizes,50)
    assert allocation.sum()==50
    assert np.all(allocation<=sizes)

def test_sampler_exact_and_reproducible():
    n=500
    frame=pd.DataFrame({
      "store_segment":np.tile([0,1],n//2),
      "category_segment":np.tile([0,1,2,3,4],n//5),
      "horizon":np.tile(np.arange(1,11),n//10),
      "zero_frac_90":np.linspace(0,1,n),
      "target":np.arange(n,dtype=float)})
    a=stratified_sample(frame,200,17)
    b=stratified_sample(frame,200,17)
    pd.testing.assert_frame_equal(a,b)
    assert len(a)==200
    assert "demand_pattern" not in a

def test_sampler_rejects_insufficient_rows():
    frame=pd.DataFrame({"store_segment":[0],"category_segment":[0],
      "horizon":[1],"zero_frac_90":[0.0]})
    with pytest.raises(ValueError,match="Need 2"):
        stratified_sample(frame,2,1)
