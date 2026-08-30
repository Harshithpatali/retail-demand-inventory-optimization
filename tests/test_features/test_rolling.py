import pandas as pd
from src.features.rolling_features import add_rolling_features

def test_rolling_uses_past_only():
    df=pd.DataFrame({"id":["a"]*4,"demand":[1,10,100,1000]})
    out=add_rolling_features(df)
    assert out.loc[2,"rolling_mean_7"] == 5.5
    assert out.loc[2,"rolling_mean_7"] != 37
