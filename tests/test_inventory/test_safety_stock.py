from src.inventory.safety_stock import safety_stock

def test_safety_stock_increases_with_service_level():
    assert safety_stock(2,7,0.95)>safety_stock(2,7,0.90)

def test_protection_period_increases_safety_stock():
    assert safety_stock(2,14,0.90)>safety_stock(2,7,0.90)
