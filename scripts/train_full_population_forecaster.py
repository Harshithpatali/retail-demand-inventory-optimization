"""Global 28-day M5 LightGBM demand forecaster for all 30,490 item-store series."""
from __future__ import annotations
import gc, json, os
import psutil
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
import pyarrow as pa
import pyarrow.parquet as pq
from src.utils.config import ROOT

RAW=ROOT/"data/raw"
OUT=ROOT/"reports/full_population_forecasting"
MODEL=ROOT/"models/full_population"
H=28
CHUNK=128
PROCESS=psutil.Process(os.getpid())
MEMORY_LOG=[]
def memory_checkpoint(label):
 rss=PROCESS.memory_info().rss/(1024**3)
 MEMORY_LOG.append({"stage":label,"rss_gb":round(rss,3)})
 print(f"[memory] {label}: RSS={rss:.2f} GiB",flush=True)
 return rss
FEATURES=["item_code","store_code","dept_code","cat_code","state_code","horizon",
 "day_of_week","month","is_weekend","event_flag","snap_flag","lag_1","lag_7",
 "lag_14","lag_28","lag_56","lag_364","mean_7","mean_28","mean_56","mean_90",
 "std_28","zero_frac_28","zero_frac_90","adi_90","cv2_90"]
CATS=["item_code","store_code","dept_code","cat_code","state_code"]
META=["id","item_id","dept_id","cat_id","store_id","state_id"]

def source_file():
 for name in ("sales_train_evaluation.csv","sales_train_validation.csv"):
  p=RAW/name
  if p.exists(): return p
 raise FileNotFoundError("Full M5 sales matrix is missing from data/raw.")

def read_calendar(date_cols):
 c=pd.read_csv(RAW/"calendar.csv").set_index("d").reindex(date_cols).reset_index()
 c["date"]=pd.to_datetime(c["date"])
 return c

def build_examples(path,date_cols,cal,origins,out):
 # Small metadata-only pass builds stable category codes for all series.
 ids=pd.read_csv(path,usecols=META)
 levels={c:sorted(ids[c].astype(str).unique()) for c in META[1:]}
 maps={c:{v:i for i,v in enumerate(vals)} for c,vals in levels.items()}
 del ids; gc.collect()
 writer=None; total=0
 try:
  for chunk in pd.read_csv(path,usecols=META+date_cols,chunksize=CHUNK):
   v=chunk[date_cols].to_numpy(dtype=np.float32,copy=False); n=len(chunk)
   store=chunk.store_id.astype(str).map(maps["store_id"]).to_numpy(dtype=np.int8)
   state=chunk.state_id.astype(str).map(maps["state_id"]).to_numpy(dtype=np.int8)
   cat=chunk.cat_id.astype(str).map(maps["cat_id"]).to_numpy(dtype=np.int8)
   dept=chunk.dept_id.astype(str).map(maps["dept_id"]).to_numpy(dtype=np.int8)
   item=chunk.item_id.astype(str).map(maps["item_id"]).to_numpy(dtype=np.int16)
   for origin in origins:
    hist=v[:,origin-89:origin+1]
    nonzero=(hist>0).sum(axis=1); mean=hist.mean(axis=1)
    shared={"item_code":item,"store_code":store,"dept_code":dept,"cat_code":cat,"state_code":state,
     "lag_1":v[:,origin],"lag_7":v[:,origin-6],"lag_14":v[:,origin-13],
     "lag_28":v[:,origin-27],"lag_56":v[:,origin-55],"lag_364":v[:,origin-363],
     "mean_7":v[:,origin-6:origin+1].mean(axis=1),
     "mean_28":v[:,origin-27:origin+1].mean(axis=1),
     "mean_56":v[:,origin-55:origin+1].mean(axis=1),"mean_90":mean,
     "std_28":v[:,origin-27:origin+1].std(axis=1),
     "zero_frac_28":(v[:,origin-27:origin+1]==0).mean(axis=1),
     "zero_frac_90":(hist==0).mean(axis=1),
     "adi_90":np.divide(90,nonzero,out=np.full(n,90,dtype=np.float32),where=nonzero>0),
     "cv2_90":np.divide(hist.std(axis=1),mean,out=np.zeros(n,dtype=np.float32),where=mean>0)**2}
    for h in range(1,H+1):
     ti=origin+h; cr=cal.iloc[ti]
     ev=int(pd.notna(cr.get("event_name_1")) or pd.notna(cr.get("event_name_2")))
     snap=np.zeros(n,dtype=np.int8)
     for st in ("CA","TX","WI"):
      if st in maps["state_id"]:
       snap[chunk.state_id.astype(str).to_numpy()==st]=int(cr.get("snap_"+st,0) or 0)
     data={**shared,"horizon":np.full(n,h,dtype=np.int8),
      "day_of_week":np.full(n,int(cr["wday"]),dtype=np.int8),
      "month":np.full(n,int(cr["month"]),dtype=np.int8),
      "is_weekend":np.full(n,int(cr["wday"] in (1,7)),dtype=np.int8),
      "event_flag":np.full(n,ev,dtype=np.int8),"snap_flag":snap,
      "target":v[:,ti],"seasonal_naive":v[:,ti-7],
      "train_sample":(pd.util.hash_pandas_object(chunk["id"],index=False).to_numpy(dtype=np.uint64)%4==0),
      "origin_index":np.full(n,origin,dtype=np.int16),
      "store_segment":store,"state_segment":state,"category_segment":cat,"department_segment":dept}
     frame=pd.DataFrame(data)
     table=pa.Table.from_pandas(frame,preserve_index=False)
     if writer is None:
      out.parent.mkdir(parents=True,exist_ok=True)
      writer=pq.ParquetWriter(out,table.schema,compression="zstd",use_dictionary=True)
     writer.write_table(table,row_group_size=50000); total+=n
   del v,chunk
   print(f"Feature generation progress: {total:,} rows")
 finally:
  if writer: writer.close()
 (OUT/"category_code_maps.json").write_text(json.dumps(levels,indent=2))
 print(f"Generated {total:,} all-series horizon examples.")
 return total,levels

def make_model():
 return lgb.LGBMRegressor(objective="poisson",n_estimators=450,learning_rate=.045,
  num_leaves=63,min_child_samples=100,subsample=.85,colsample_bytree=.85,
  reg_lambda=2.0,n_jobs=2,random_state=42,verbosity=-1)

def fit(frame,mask,levels):
 d=frame.loc[mask]
 X=d[FEATURES].copy()
 category_sizes={"item_code":len(levels["item_id"]),"store_code":len(levels["store_id"]),
  "dept_code":len(levels["dept_id"]),"cat_code":len(levels["cat_id"]),
  "state_code":len(levels["state_id"])}
 for c in CATS: X[c]=pd.Categorical(X[c],categories=range(category_sizes[c]))
 model=make_model()
 model.fit(X,d.target.astype(np.float32),categorical_feature=CATS)
 del d,X; gc.collect()
 return model

def load_model_frame(path,train_origins,val_origin,test_origin,batch_size=65536):
 # Stream Parquet row groups. Keep a deterministic 25% series sample for training,
 # but retain every row from validation and test origins for honest evaluation.
 train_parts=[]; eval_parts=[]; parquet=pq.ParquetFile(path)
 for batch in parquet.iter_batches(batch_size=batch_size):
  part=batch.to_pandas()
  train=part[part.origin_index.isin(train_origins)&part.train_sample]
  evaluate=part[part.origin_index.isin([val_origin,test_origin])]
  if not train.empty: train_parts.append(train)
  if not evaluate.empty: eval_parts.append(evaluate)
  del part,train,evaluate
 train=pd.concat(train_parts,ignore_index=True)
 evaluate=pd.concat(eval_parts,ignore_index=True)
 del train_parts,eval_parts; gc.collect()
 result=pd.concat([train,evaluate],ignore_index=True)
 del train,evaluate; gc.collect()
 return result

def metrics(y,p,frame,split,levels):
 y=np.asarray(y,dtype=float); p=np.clip(np.asarray(p,dtype=float),0,None)
 rows=[]
 def add(kind,name,mask):
  if not mask.any():return
  a=y[mask]; b=p[mask]
  rows.append({"split":split,"segment_type":kind,"segment":name,"observations":int(mask.sum()),
   "MAE":float(np.abs(a-b).mean()),"RMSE":float(np.sqrt(np.mean((a-b)**2))),
   "WAPE":float(np.abs(a-b).sum()/max(np.abs(a).sum(),1e-9)),
   "bias":float((b-a).sum()/max(a.sum(),1e-9))})
 add("overall","all",np.ones(len(y),dtype=bool))
 for col,kind in (("store_segment","store_id"),("state_segment","state_id"),
  ("category_segment","cat_id"),("department_segment","dept_id")):
  codes=frame[col].to_numpy()
  names=levels[kind]
  for code,name in enumerate(names):add(kind,name,codes==code)
 return rows

def predict_future(path,date_cols,cal,model,levels):
 memory_checkpoint("before_future_inference")
 maps={c:{v:i for i,v in enumerate(vals)} for c,vals in levels.items()}
 last=pd.to_datetime(cal.iloc[-1].date)
 dates=pd.date_range(last+pd.Timedelta(days=1),periods=H)
 out=OUT/"forecast_28d_all_series.parquet"; writer=None; count=0
 try:
  for chunk in pd.read_csv(path,usecols=META+date_cols,chunksize=CHUNK):
   v=chunk[date_cols].to_numpy(dtype=np.float32,copy=False); n=len(chunk)
   hist=v[:,-90:]; nz=(hist>0).sum(axis=1); mean=hist.mean(axis=1)
   base=pd.DataFrame({
    "item_code":chunk.item_id.astype(str).map(maps["item_id"]).astype("int16"),
    "store_code":chunk.store_id.astype(str).map(maps["store_id"]).astype("int8"),
    "dept_code":chunk.dept_id.astype(str).map(maps["dept_id"]).astype("int8"),
    "cat_code":chunk.cat_id.astype(str).map(maps["cat_id"]).astype("int8"),
    "state_code":chunk.state_id.astype(str).map(maps["state_id"]).astype("int8"),
    "lag_1":v[:,-1],"lag_7":v[:,-7],"lag_14":v[:,-14],"lag_28":v[:,-28],
    "lag_56":v[:,-56],"lag_364":v[:,-364],
    "mean_7":v[:,-7:].mean(axis=1),"mean_28":v[:,-28:].mean(axis=1),
    "mean_56":v[:,-56:].mean(axis=1),"mean_90":mean,
    "std_28":v[:,-28:].std(axis=1),"zero_frac_28":(v[:,-28:]==0).mean(axis=1),
    "zero_frac_90":(hist==0).mean(axis=1),
    "adi_90":np.divide(90,nz,out=np.full(n,90,dtype=np.float32),where=nz>0),
    "cv2_90":np.divide(hist.std(axis=1),mean,out=np.zeros(n,dtype=np.float32),where=mean>0)**2})
   for h,dt in enumerate(dates,1):
    X=base.copy()
    X["horizon"]=h; X["day_of_week"]=((dt.dayofweek+1)%7)+1
    X["month"]=dt.month; X["is_weekend"]=int(dt.dayofweek>=5)
    X["event_flag"]=0; X["snap_flag"]=0
    category_sizes={"item_code":len(levels["item_id"]),"store_code":len(levels["store_id"]),
     "dept_code":len(levels["dept_id"]),"cat_code":len(levels["cat_id"]),
     "state_code":len(levels["state_id"])}
    for c in CATS:X[c]=pd.Categorical(X[c],categories=range(category_sizes[c]))
    yhat=np.clip(model.predict(X[FEATURES]),0,None)
    frame=pd.DataFrame({"id":chunk.id.astype(str),"item_id":chunk.item_id.astype(str),
     "dept_id":chunk.dept_id.astype(str),"cat_id":chunk.cat_id.astype(str),
     "store_id":chunk.store_id.astype(str),"state_id":chunk.state_id.astype(str),
     "date":dt,"horizon":h,"forecast_units":yhat})
    table=pa.Table.from_pandas(frame,preserve_index=False)
    if writer is None:
     out.parent.mkdir(parents=True,exist_ok=True)
     writer=pq.ParquetWriter(out,table.schema,compression="zstd")
    writer.write_table(table,row_group_size=50000); count+=n
   del v,chunk,base
 finally:
  if writer:writer.close()
 expected=30490*H
 if count != expected: raise RuntimeError(f"Forecast row count mismatch: expected {expected:,}, got {count:,}")
 check=pq.ParquetFile(out)
 if check.metadata.num_rows != expected: raise RuntimeError(f"Parquet metadata row count mismatch: {check.metadata.num_rows:,}")
 print(f"Forecast output verified: {count:,} rows, {out.stat().st_size/1e6:.1f} MB")
 memory_checkpoint("after_future_inference")

def main():
 OUT.mkdir(parents=True,exist_ok=True); MODEL.mkdir(parents=True,exist_ok=True)
 memory_checkpoint("start")
 path=source_file(); columns=list(pd.read_csv(path,nrows=0).columns)
 dates=[c for c in columns if c.startswith("d_")]
 if len(dates)<500:raise ValueError(f"Unexpected M5 daily history: {len(dates)} columns")
 n=len(dates); count=int(pd.read_csv(path,usecols=["id"]).shape[0])
 if count!=30490:raise ValueError(f"Expected 30,490 series, found {count}")
 cal=read_calendar(dates)
 # 4 rolling training origins, followed by independent validation and test origins.
 train_origins=[n-365-1,n-273-1,n-181-1,n-89-1]
 val_origin=n-56-1; test_origin=n-28-1
 origins=train_origins+[val_origin,test_origin]
 examples=OUT/"training_examples.parquet"
 total,levels=build_examples(path,dates,cal,origins,examples)
 memory_checkpoint("after_feature_generation")
 frame=load_model_frame(examples,train_origins,val_origin,test_origin)
 memory_checkpoint("after_loading_training_and_eval_frame")
 train_mask=frame.origin_index.isin(train_origins)
 val_mask=frame.origin_index.eq(val_origin)
 test_mask=frame.origin_index.eq(test_origin)
 model=fit(frame,train_mask,levels)
 memory_checkpoint("after_model_fit")
 rows=[]
 for label,mask in (("validation",val_mask),("test",test_mask)):
  d=frame.loc[mask]; X=d[FEATURES].copy()
  for c in CATS:category_sizes={"item_code":len(levels["item_id"]),"store_code":len(levels["store_id"]),
   "dept_code":len(levels["dept_id"]),"cat_code":len(levels["cat_id"]),
   "state_code":len(levels["state_id"])}
  for c in CATS:X[c]=pd.Categorical(X[c],categories=range(category_sizes[c]))
  pred=np.clip(model.predict(X),0,None)
  rows.extend(metrics(d.target,pred,d,label,levels))
  rows.extend(metrics(d.target,d.seasonal_naive,d,label+"_seasonal_naive",levels))
  del d,X,pred;gc.collect()
 metrics_df=pd.DataFrame(rows)
 metrics_df.to_csv(OUT/"full_population_forecast_metrics.csv",index=False)
 # Final production fit uses all six historical origins, including the now-observed holdout window.
 final=fit(frame,frame.index==frame.index,levels)
 final.booster_.save_model(str(MODEL/"m5_global_lightgbm_28d.txt"))
 predict_future(path,dates,cal,final,levels)
 last=pd.to_datetime(cal.iloc[-1].date)
 metadata={"model":"Global LightGBM Poisson regressor","population_series":count,
  "horizon_days":H,"training_origins":train_origins,"validation_origin":val_origin,
  "test_origin":test_origin,"production_training_origins":origins,
  "feature_example_rows":total,"last_observed_date":str(last.date()),
  "forecast_start":str((last+pd.Timedelta(days=1)).date()),
  "forecast_end":str((last+pd.Timedelta(days=H)).date()),
  "forecast_rows":count*H,"peak_process_rss_gb":max((x["rss_gb"] for x in MEMORY_LOG),default=0),"memory_checkpoints":MEMORY_LOG,"training_population":"all 30,490 series represented in inference; deterministic 25% series sample used for model fitting",
  "training_sampling":"25% stable hash sample across series; all rows from validation/test origins retained",
  "training_feature_rows_in_memory":int(train_mask.sum()),
  "features":FEATURES,"future_covariates":"weekday/month known; future events and SNAP unavailable and set to zero",
  "limitations":"M5 records sales, not latent unconstrained demand; zeros may include stockouts. Future price/event/SNAP values are unavailable beyond the source calendar."}
 (OUT/"forecast_run_metadata.json").write_text(json.dumps(metadata,indent=2))
 examples.unlink(missing_ok=True)
 print(metrics_df[metrics_df.segment_type.eq("overall")].to_string(index=False))
 print(json.dumps(metadata,indent=2))

if __name__=="__main__":main()
