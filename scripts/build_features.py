import pandas as pd
from src.utils.config import ROOT
from src.features.feature_pipeline import build_features

def main():
    src=ROOT/"data/interim/cleaned_sales.parquet"
    if not src.exists(): raise FileNotFoundError("Missing prerequisite: cleaned_sales.parquet. Run python -m scripts.prepare_data first.")
    df=pd.read_parquet(src)
    out=build_features(df)
    out.to_parquet(ROOT/"data/processed/forecast_features.parquet",index=False)
    print(f"Built {len(out):,} feature rows.")
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
