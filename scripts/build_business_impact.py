import joblib
import matplotlib.pyplot as plt
import pandas as pd
from src.utils.config import ROOT, load_yaml
from src.business.business_metrics import summarize_simulation, compare
from src.inventory.safety_stock import safety_stock

def bar_compare(summary,filename,title,metric):
    vals=[summary["baseline"][metric],summary["optimized"][metric]]
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar(["Baseline","Optimized"],vals); ax.set_title(title); ax.set_ylabel(metric.replace("_"," ").title()); fig.tight_layout(); fig.savefig(ROOT/"reports/figures/business_impact"/filename,dpi=160,bbox_inches="tight"); plt.close(fig)

def main():
    p=ROOT/"data/processed/inventory_simulation.parquet"
    if not p.exists(): raise FileNotFoundError("Missing prerequisite: inventory_simulation.parquet. Run python -m scripts.run_inventory_simulation first.")
    df=pd.read_parquet(p); bdf=df[df.policy=="baseline"].copy(); odf=df[df.policy=="optimized"].copy()
    if set(pd.to_datetime(bdf.date)) != set(pd.to_datetime(odf.date)): raise ValueError("Baseline and optimized policies do not use identical dates.")
    b=summarize_simulation(bdf); o=summarize_simulation(odf); summary={"baseline":b,"optimized":o}; comp=pd.DataFrame(compare(b,o)); comp.to_csv(ROOT/"reports/tables/business_impact_summary.csv",index=False); joblib.dump(summary,ROOT/"models/uncertainty/business_metrics.joblib")
    for metric,fn,title in [("total_cost","total_cost_comparison.png","Total Cost Comparison"),("average_inventory","inventory_comparison.png","Average Inventory Comparison"),("stockout_units","stockout_comparison.png","Stockout Units Comparison"),("service_level","service_level_comparison.png","Service-Level Comparison"),("holding_cost","holding_cost_comparison.png","Holding Cost Comparison"),("ordering_cost","ordering_cost_comparison.png","Ordering Cost Comparison"),("stockout_cost","stockout_cost_comparison.png","Stockout Cost Comparison"),("fill_rate","fill_rate_comparison.png","Fill-Rate Comparison")]: bar_compare(summary,fn,title,metric)
    inv=load_yaml("inventory_config.yaml"); mean=float(bdf.demand.mean()); sd=float(bdf.demand.std()) if len(bdf)>1 else 0.0; lead=int(inv["default_lead_time_days"]); review=int(inv["default_review_period_days"]); sls=[float(v) for v in inv["service_levels"]]; lts=[int(v) for v in inv["lead_times"]]
    vals=[safety_stock(sd,lead+review,s) for s in sls]; fig,ax=plt.subplots(figsize=(7,4)); ax.plot(sls,vals,marker="o"); ax.set_title("Safety Stock vs Service Level"); ax.set_xlabel("Service level"); ax.set_ylabel("Safety stock"); ax.set_ylim(bottom=0); fig.tight_layout(); fig.savefig(ROOT/"reports/figures/inventory/safety_stock_vs_service_level.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    rops=[mean*(lt+review)+safety_stock(sd,lt+review,inv["default_service_level"]) for lt in lts]; fig,ax=plt.subplots(figsize=(7,4)); ax.plot(lts,rops,marker="o"); ax.set_title("Target Inventory Position vs Lead Time"); ax.set_xlabel("Lead time (days)"); ax.set_ylabel("Target inventory position"); ax.set_ylim(bottom=0); fig.tight_layout(); fig.savefig(ROOT/"reports/figures/inventory/rop_vs_lead_time.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    sens=ROOT/"reports/figures/sensitivity"; sens.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(7,4)); ax.plot(sls,vals,marker="o"); ax.set_title("Service Level Sensitivity"); ax.set_xlabel("Service level"); ax.set_ylabel("Safety stock"); fig.tight_layout(); fig.savefig(sens/"service_level_sensitivity.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    total_cost=[]
    for lt in lts:
        total_cost.append(mean*(lt+review)+safety_stock(sd,lt+review,inv["default_service_level"]))
    fig,ax=plt.subplots(figsize=(7,4)); ax.plot(lts,total_cost,marker="o"); ax.set_title("Lead Time Sensitivity"); ax.set_xlabel("Lead time (days)"); ax.set_ylabel("Target inventory position"); fig.tight_layout(); fig.savefig(sens/"lead_time_sensitivity.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    print(comp.to_string(index=False))
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
