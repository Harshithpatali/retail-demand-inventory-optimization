import pandas as pd
from src.data.transformer import series_summary

def test_series_summary_zero_rate():
    df=pd.DataFrame({"id":["a","a","b"],"demand":[0,2,0]})
    s=series_summary(df).set_index("id")
    assert s.loc["a","zero_rate"]==0.5
