import pandas as pd

from api.services.forecast_service import ForecastService


class FakeArtifactStore:
    def load_series(self, store_id, item_id):
        return pd.DataFrame([{
            "date": pd.Timestamp("2016-05-22"),
            "demand": 12.0,
            "sell_price": 2.5,
            "store_code": 0,
            "item_code": 0,
            "dept_code": 0,
            "cat_code": 0,
            "state_code": 0,
        }])

    def load_model(self):
        return {"model_name": "test-model", "model": object(), "feature_columns": []}

    def load_uncertainty(self):
        return {
            "std": 4.0,
            "calibration_abs_residuals": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        }


def test_forecast_service_uses_calibrated_conformal_interval(monkeypatch):
    import api.services.forecast_service as module

    def fake_predict(bundle, history, future):
        return pd.DataFrame({"date": future, "forecast": [10.0] * len(future)})

    monkeypatch.setattr(module, "recursive_global_forecast", fake_predict)
    service = ForecastService()
    service.store = FakeArtifactStore()

    model_name, residual_std, output, method = service.forecast("CA_1", "FOODS_2_019", 2)

    assert model_name == "test-model"
    assert residual_std == 4.0
    assert method == "split_conformal_absolute_residual"
    assert output["lower"].tolist() == [1.0, 1.0]
    assert output["upper"].tolist() == [19.0, 19.0]
