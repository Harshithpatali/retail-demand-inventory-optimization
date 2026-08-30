import pandas as pd
from src.simulation.inventory_simulator import simulate

def pol(r=3,t=10): return {"review_period_days":r,"target_inventory_position":t,"min_order_quantity":1,"max_order_quantity":500}

def test_periodic_review_only():
    d=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=8),"demand":[0]*8})
    out=simulate(d,pol(3,10),0,2,0.05,5,2)
    assert out.loc[~out.is_review_day,"order_quantity_placed"].sum()==0

def test_lead_time():
    d=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=4),"demand":[0]*4})
    out=simulate(d,pol(1,10),0,2,0.05,5,2)
    assert out.loc[0,"ending_inventory"]==0 and out.loc[1,"ending_inventory"]==0 and out.loc[2,"ending_inventory"]==10

def test_outstanding_order_prevents_duplicate_order():
    d=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=6),"demand":[0]*6})
    out=simulate(d,pol(1,10),0,5,0.05,5,2)
    assert out["order_quantity_placed"].sum()==10
