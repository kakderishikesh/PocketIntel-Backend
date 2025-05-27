import httpx
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import yfinance as yf

# Load API key
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise EnvironmentError("POLYGON_API_KEY not found in environment variables.")

async def fetch_stock_price_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Fetches stock price data from Polygon.io or falls back to yfinance.
    Returns DataFrame with columns: ["Date", "Close"].
    """
    try:
        return await fetch_from_polygon(ticker, period)
    except Exception as e:
        print(f"[Polygon Fallback] Ticker '{ticker}' failed on Polygon: {e}")
        return fetch_from_yfinance(ticker, period)

async def fetch_from_polygon(ticker: str, period: str) -> pd.DataFrame:
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
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Polygon API error {response.status_code}: {response.text[:100]}")
        if not response.text.strip().startswith("{"):
            raise RuntimeError("Invalid response from Polygon.")
        json_data = response.json()
        data = json_data.get("results", [])
        if not data:
            raise ValueError("No data in Polygon response.")

    df = pd.DataFrame(data)
    if "t" not in df.columns:
        raise KeyError("Missing timestamp column 't'.")

    df["Date"] = pd.to_datetime(df["t"], unit="ms")
    df.rename(columns={"c": "Close"}, inplace=True)
    df.dropna(subset=["Date", "Close"], inplace=True)
    return df[["Date", "Close"]].reset_index(drop=True)

def fetch_from_yfinance(ticker: str, period: str) -> pd.DataFrame:
    # Convert period to yfinance-compatible format
    yf_period = period if period in ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] else "6mo"
    df = yf.download(ticker, period=yf_period, interval="1d", progress=False)
    
    if df.empty:
        raise ValueError(f"yfinance returned empty data for ticker: {ticker}")

    # Flatten MultiIndex columns if needed (for e.g., when 'Close' is in ('Adj Close',) etc.)
    df.columns = [col if isinstance(col, str) else col[1] if isinstance(col, tuple) else str(col) for col in df.columns]
    
    df = df.reset_index()
    if "Close" not in df.columns or "Date" not in df.columns:
        raise KeyError("Required columns not found in yfinance response.")

    df["Date"] = pd.to_datetime(df["Date"])
    df.dropna(subset=["Date", "Close"], inplace=True)
    return df[["Date", "Close"]].reset_index(drop=True)

# CLI test
if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "XLK"
    period = "1y"
    try:
        df = asyncio.run(fetch_stock_price_data(ticker, period))
        print(df.head())
    except Exception as e:
        print("Final error:", e)
