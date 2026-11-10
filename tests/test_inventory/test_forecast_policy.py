import pytest
from src.inventory.forecast_policy import calculate_forecast_target

def test_forecast_policy():
    p=calculate_forecast_target([2,3,4,5],[0,1,-1,2,-2,1,0,-1],2,2,0.5)
    assert p["forecast_protection_demand"]==14
    assert p["target_inventory_position"]>=14

def test_requires_full_horizon():
    with pytest.raises(ValueError): calculate_forecast_target([1,2],[0,1,-1,2],3,2,0.9)
