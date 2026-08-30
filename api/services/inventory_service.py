from api.services.artifacts import ArtifactStore
from src.inventory.safety_stock import safety_stock
class InventoryService:
    def __init__(self): self.store=ArtifactStore()
    def calculate(self,store_id,item_id,service_level,lead_time_days,current_inventory):
        df=self.store.load_data(); g=df[(df.store_id.astype(str)==str(store_id))&(df.item_id.astype(str)==str(item_id))].sort_values("date")
        if g.empty: raise ValueError("Unknown store_id/item_id combination.")
        tail=g.demand.tail(56); mean=float(tail.mean()); std=float(tail.std(ddof=1)) if len(tail)>1 else 0.0
        ss=safety_stock(std,lead_time_days,service_level); ltd=mean*lead_time_days; rop=ltd+ss; q=max(1.0,min(500.0,mean*7)); action="REORDER" if current_inventory < rop else "HOLD"
        model_name="unavailable"
        try: model_name=self.store.load_model()["model_name"]
        except FileNotFoundError: pass
        return {"mean_daily_demand":mean,"lead_time_demand":ltd,"demand_std":std,"safety_stock":ss,"reorder_point":rop,"order_quantity":q,"service_level":service_level,"lead_time_days":lead_time_days,"current_inventory":current_inventory,"recommended_action":action,"store_id":store_id,"item_id":item_id,"model_name":model_name}
