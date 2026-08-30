from dataclasses import dataclass
import pandas as pd

@dataclass
class PurchaseOrder:
    arrival_date: pd.Timestamp
    quantity: float

def simulate(demand_df: pd.DataFrame, policy: dict, initial_inventory: float, lead_time_days: int, holding_cost_per_unit_day: float, ordering_cost_per_order: float, stockout_cost_per_unit: float, review_start_date=None) -> pd.DataFrame:
    required={"date","demand"}
    missing=required-set(demand_df.columns)
    if missing: raise ValueError(f"Missing simulation columns: {sorted(missing)}")
    review_period=int(policy.get("review_period_days",1))
    if review_period < 1: raise ValueError("review_period_days must be >= 1")
    target=float(policy.get("target_inventory_position",policy.get("reorder_point",0.0)))
    min_order=float(policy.get("min_order_quantity",0.0)); max_order=float(policy.get("max_order_quantity",500.0))
    if max_order < min_order: raise ValueError("max_order_quantity must be >= min_order_quantity")
    x=demand_df.sort_values("date").reset_index(drop=True).copy(); x["date"]=pd.to_datetime(x["date"])
    if x.empty: return pd.DataFrame()
    review_start_date=pd.Timestamp(review_start_date) if review_start_date is not None else x["date"].min()
    on_hand=max(0.0,float(initial_inventory)); orders=[]; rows=[]
    for day_index,r in x.iterrows():
        date=pd.Timestamp(r["date"])
        arrivals=sum(po.quantity for po in orders if po.arrival_date==date)
        if arrivals: on_hand += arrivals
        orders=[po for po in orders if po.arrival_date!=date]
        demand=max(0.0,float(r["demand"]))
        fulfilled=min(on_hand,demand); stockout=max(0.0,demand-fulfilled); on_hand-=fulfilled
        before=on_hand+sum(po.quantity for po in orders)
        elapsed=(date-review_start_date).days
        is_review_day=elapsed>=0 and elapsed%review_period==0
        place=0.0
        if is_review_day and before < target:
            gap=target-before
            place=min(max(gap,min_order),max_order)
            if place>0:
                orders.append(PurchaseOrder(date+pd.Timedelta(days=int(lead_time_days)),float(place)))
        after=on_hand+sum(po.quantity for po in orders)
        hold=max(0.0,on_hand)*holding_cost_per_unit_day
        order_cost=ordering_cost_per_order if place>0 else 0.0
        stock_cost=stockout*stockout_cost_per_unit
        rows.append({"date":date,"demand":demand,"fulfilled":fulfilled,"stockout_units":stockout,"ending_inventory":on_hand,"inventory_position":after,"inventory_position_before_order":before,"order_quantity_placed":place,"outstanding_order_units":sum(po.quantity for po in orders),"is_review_day":bool(is_review_day),"holding_cost":hold,"ordering_cost":order_cost,"stockout_cost":stock_cost,"total_cost":hold+order_cost+stock_cost})
    return pd.DataFrame(rows)
