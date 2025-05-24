import httpx
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio

# Load API key from .env file
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise EnvironmentError("POLYGON_API_KEY not found in environment variables.")

async def fetch_stock_price_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Asynchronously fetch historical daily OHLCV stock price data from Polygon.io.
    Returns DataFrame with columns: Date, Open, High, Low, Close, Volume.
    """
    # Calculate date range from period
    end_date = datetime.utcnow()
    if period.endswith("mo"):
        months = int(period[:-2])
        start_date = end_date - timedelta(days=months * 30)
    elif period.endswith("y"):
        years = int(period[:-1])
        start_date = end_date - timedelta(days=years * 365)
    else:
        raise ValueError("Unsupported period format. Use '6mo', '1y', etc.")

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start_date.date()}/{end_date.date()}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            json_data = response.json()
            data = json_data.get("results", [])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Polygon API: {e}")

    if not data:
        raise ValueError(f"No stock price data returned for ticker: {ticker}")

    df = pd.DataFrame(data)

    if "t" not in df.columns:
        raise KeyError("Timestamp column 't' not found in Polygon API response.")

    df["Date"] = pd.to_datetime(df["t"], unit="ms")
    df.rename(columns={
        "o": "Open",
        "h": "High",
        "l": "Low",
        "c": "Close",
        "v": "Volume"
    }, inplace=True)

    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]

if __name__ == "__main__":
    ticker = "NVDA"
    period = "1y"
    data = asyncio.run(fetch_stock_price_data(ticker, period))
    print(data.head())
