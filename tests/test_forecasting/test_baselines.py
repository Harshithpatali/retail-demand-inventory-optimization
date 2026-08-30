import pandas as pd
from src.forecasting.baselines import seasonal_naive_forecast
from src.forecasting.evaluate import wape

def test_seasonal_naive_shape():
    h=pd.Series([1,2,3,4,5,6,7])
    p=seasonal_naive_forecast(h,10,7)
    assert len(p)==10 and list(p[:7])==[1,2,3,4,5,6,7]

def test_wape():
    assert abs(wape([10,0],[8,2])-0.4)<1e-9
