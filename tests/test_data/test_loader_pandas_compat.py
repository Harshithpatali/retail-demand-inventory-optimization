import pandas as pd

from src.data.loader import _score_rows


def test_score_rows_uses_supported_pandas_sum():
    frame = pd.DataFrame(
        {
            "d_1": [1, 2],
            "d_2": [3, 4],
            "d_3": [0, 5],
        }
    )

    scores = _score_rows(
        frame,
        ["d_1", "d_2", "d_3"],
    )

    assert scores.tolist() == [4.0, 11.0]
    assert str(scores.dtype) == "float32"
