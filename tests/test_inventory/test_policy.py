from src.inventory.inventory_policy import InventoryPolicy, calculate_policy

def test_rs_target_uses_lead_plus_review():
    p=calculate_policy(InventoryPolicy(10,2,7,0.9,7,1,500))
    assert p["protection_period_days"]==14
    assert p["target_inventory_position"]>70
