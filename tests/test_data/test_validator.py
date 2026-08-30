import pandas as pd
from src.data.validator import validate_sales_columns

def test_required_sales_columns():
    validate_sales_columns(pd.DataFrame({c:[] for c in ["id","item_id","dept_id","cat_id","store_id","state_id"]}))
