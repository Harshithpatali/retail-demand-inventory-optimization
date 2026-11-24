"""Publish the complete M5 source and derived Parquet datasets to Cloudflare R2."""
from __future__ import annotations
import hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
import boto3, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from botocore.config import Config
ROOT=Path(__file__).resolve().parents[1]
BUCKET=os.getenv("R2_BUCKET","m5-retail-analytics")
def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def s3_client():
 account=os.environ["R2_ACCOUNT_ID"]
 return boto3.client("s3",endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
  region_name="auto",config=Config(signature_version="s3v4",retries={"max_attempts":5}))
def upload(s3,path,key,ctype=None):
 extra={"ContentType":ctype} if ctype else {}
 s3.upload_file(str(path),BUCKET,key,ExtraArgs=extra)
 return {"key":key,"bytes":path.stat().st_size,"sha256":digest(path)}
def convert_csv(src,dst,chunksize):
 dst.parent.mkdir(parents=True,exist_ok=True); writer=None; rows=0
 try:
  for frame in pd.read_csv(src,chunksize=chunksize):
   table=pa.Table.from_pandas(frame,preserve_index=False)
   if writer is None: writer=pq.ParquetWriter(dst,table.schema,compression="zstd")
   writer.write_table(table); rows+=len(frame)
 finally:
  if writer is not None: writer.close()
 if writer is None: raise RuntimeError(f"Empty source CSV: {src}")
 return rows
def main():
 for name in ("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY"):
  if not os.getenv(name): raise RuntimeError(f"Missing required GitHub Actions secret: {name}")
 raw=ROOT/"data"/"raw"; work=ROOT/".m5_download"; archive=work/"m5_source.zip"
 if not archive.is_file(): raise FileNotFoundError(f"Original M5 ZIP not found: {archive}")
 s3=s3_client(); records=[upload(s3,archive,"raw/m5-forecasting-accuracy.zip","application/zip")]
 for csv in sorted(raw.glob("*.csv")):
  pqpath=work/"parquet"/f"{csv.stem}.parquet"
  rows=convert_csv(csv,pqpath,256 if csv.name.startswith("sales_train_") else 100000)
  rec=upload(s3,pqpath,f"raw/extracted/{csv.stem}.parquet","application/vnd.apache.parquet")
  rec.update({"source_csv":csv.name,"rows":rows}); records.append(rec)
  print(f"Uploaded {csv.name}: {rows:,} rows")
 for rel in ("data/interim/cleaned_sales.parquet","data/processed/forecast_features.parquet","data/interim/validation_report.json"):
  p=ROOT/rel
  if p.is_file():
   records.append(upload(s3,p,f"processed/{rel.removeprefix('data/')}",
    "application/vnd.apache.parquet" if p.suffix==".parquet" else "application/json"))
 eda=ROOT/"reports"/"eda"/"full_data"
 if eda.exists():
  for p in sorted(x for x in eda.rglob("*") if x.is_file()):
   suffix=p.suffix.lower(); ctype={" .parquet":"application/vnd.apache.parquet",".parquet":"application/vnd.apache.parquet",
    ".json":"application/json",".csv":"text/csv",".png":"image/png",".md":"text/markdown"}.get(suffix)
   records.append(upload(s3,p,"processed/full_population_eda/"+p.relative_to(eda).as_posix(),ctype))
 manifest={"project":"retail-demand-inventory-optimization","dataset":"M5 Forecasting Accuracy",
  "created_at_utc":datetime.now(timezone.utc).isoformat(),"bucket":BUCKET,
  "format":"Parquet with Zstandard compression","source_archive":"raw/m5-forecasting-accuracy.zip",
  "objects":records,"note":"Archive preserved byte-for-byte; extracted source and curated datasets stored as Parquet. Supabase remains the SQL analytics warehouse."}
 m=work/"r2_manifest.json"; m.write_text(json.dumps(manifest,indent=2))
 s3.put_object(Bucket=BUCKET,Key="metadata/manifest.json",Body=m.read_bytes(),ContentType="application/json")
 print(f"Published {len(records)} R2 objects; manifest: metadata/manifest.json")
if __name__=="__main__": main()
