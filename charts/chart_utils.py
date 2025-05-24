import pandas as pd

def format_chart_block(
    chart_type: str,
    title: str,
    description: str,
    df: pd.DataFrame,
    legend: list = None,
    highlight: str = None
) -> dict:
    """
    Format a chart block for frontend. Ensures all datetime values are stringified as 'YYYY-MM-DD'.
    """
    df = df.copy()

    # Fast: Only convert index if it's datetime
    if pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = df.index.strftime("%Y-%m-%d")

    # Efficient column-wise datetime check and conversion
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns
    for col in datetime_cols:
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    return {
        "type": chart_type,
        "title": title,
        "description": description,
        "data": df.to_dict(orient="split"),
        "legend": legend or list(df.columns),
        **({"highlight": highlight} if highlight else {})
    }

