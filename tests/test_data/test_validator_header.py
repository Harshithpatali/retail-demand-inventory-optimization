import pandas as pd

from src.data.validator import validate_sales_columns


def test_validate_sales_columns_accepts_column_index():
    columns = pd.Index(
        ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id", "d_1"]
    )
    validate_sales_columns(columns)
