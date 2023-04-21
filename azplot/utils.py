import pandas as pd


def df_check(df: pd.DataFrame, required_columns: [str]):
    assert all(col in df.columns for col in required_columns), \
        f"DataFrame must contain columns: {', '.join(required_columns)}"
