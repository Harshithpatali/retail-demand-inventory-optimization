import pandas as pd
from src.features.lag_features import add_lag_features

def test_lag_1():
    df=pd.DataFrame({"id":["a"]*3,"demand":[1,2,3]})
    out=add_lag_features(df)
    assert pd.isna(out.loc[0,"lag_1"])
    assert out.loc[2,"lag_1"]==2
