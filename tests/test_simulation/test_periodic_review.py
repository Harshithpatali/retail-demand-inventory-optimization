import pandas as pd
from src.simulation.inventory_simulator import simulate

def test_review_period_changes_review_frequency():
    d=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=7),"demand":[0]*7})
    p={"review_period_days":2,"target_inventory_position":10,"min_order_quantity":1,"max_order_quantity":500}
    out=simulate(d,p,0,20,0.05,5,2)
    assert int(out["is_review_day"].sum())==4
