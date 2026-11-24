import numpy as np
import pandas as pd

from api.services.statistical_service import StatisticalService
from scripts.load_retail_warehouse import _prepare


def test_block_bootstrap_mean_is_reproducible_and_ordered():
    values = np.arange(70, dtype=float)
    first = StatisticalService._block_bootstrap_mean(values, repetitions=200, seed=7)
    second = StatisticalService._block_bootstrap_mean(values, repetitions=200, seed=7)
    assert first == second
    assert first[0] <= first[1]


def test_weekday_permutation_returns_valid_p_value():
    dates = pd.date_range("2024-01-01", periods=70, freq="D")
    frame = pd.DataFrame({"date": dates, "demand": 10 + dates.weekday * 2})
    result = StatisticalService._weekday_permutation(frame, repetitions=99, seed=3)
    assert result["weeks"] == 10
    assert 0 < result["p_value"] <= 1


def test_warehouse_preparation_maps_m5_columns():
    frame = pd.DataFrame({
        "store_id": ["CA_1"], "item_id": ["ITEM_1"], "dept_id": ["FOODS_1"],
        "cat_id": ["FOODS"], "state_id": ["CA"], "date": [pd.Timestamp("2016-01-01")],
        "d": ["d_1"], "weekday": ["Friday"], "wday": [6], "month": [1],
        "year": [2016], "wm_yr_wk": [11501], "demand": [3], "sell_price": [2.5],
        "snap_CA": [True], "snap_TX": [False], "snap_WI": [False],
    })
    prepared = _prepare(frame)
    assert prepared.loc[0, "calendar_date"] == "2016-01-01"
    assert prepared.loc[0, "snap_ca"] is True or bool(prepared.loc[0, "snap_ca"])
    assert int(prepared.loc[0, "demand"]) == 3
