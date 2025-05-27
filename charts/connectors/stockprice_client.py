import httpx
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import yfinance as yf

# Load API key from .env file
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise EnvironmentError("POLYGON_API_KEY not found in environment variables.")
    
ETF_TICKERS = {
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "XLU", "XLB", "XLRE", "XLC"
}

async def fetch_stock_price_data(ticker: str, period: str = "6mo", full_ohlc: bool = False) -> pd.DataFrame:
    try:
        return await asyncio.to_thread(get_yfinance_df, ticker, period, full_ohlc)
    except Exception as e:
        print(f"[yfinance Fallback] Ticker '{ticker}' failed on yfinance: {e}")
        return await fetch_from_polygon(ticker, period, full_ohlc)


def get_yfinance_df(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
    import time

    for attempt in range(3):
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
            break
        except Exception as e:
            print(f"[yfinance Retry {attempt+1}] {ticker}: {e}")
            time.sleep(1)
    else:
        raise RuntimeError(f"yfinance failed after retries for {ticker}")

    if df.empty:
        raise ValueError(f"yfinance returned empty data for ticker: {ticker}")

    # Handle MultiIndex like ('Close', 'XLK')
    if isinstance(df.columns, pd.MultiIndex):
    # If ticker is in MultiIndex (multi-ticker download), extract it
        if ticker in df.columns.levels[1]:
            df = df.xs(ticker, axis=1, level=1)
        else:
            # If only one ticker was downloaded, yfinance may flatten it unexpectedly
            try:
                df.columns = df.columns.get_level_values(0)
            except Exception:
                raise ValueError(f"{ticker}: Unable to extract from yfinance MultiIndex.")

    df = df.reset_index()  # Ensures 'Date' is a column

    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]

    expected_cols = ["Date", "Close"] if not full_ohlc else ["Date", "High", "Low", "Close"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"{ticker}: Missing columns in yfinance data: {missing_cols}")

    df["Date"] = pd.to_datetime(df["Date"])
    df.dropna(subset=expected_cols, inplace=True)
    return df[expected_cols].reset_index(drop=True)


async def fetch_from_polygon(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
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

            # Handle malformed or empty responses
            if response.status_code != 200:
                raise RuntimeError(f"Polygon API returned status {response.status_code}: {response.text[:100]}")
            if not response.text.strip().startswith("{"):
                raise RuntimeError(f"Polygon API returned non-JSON for {ticker}: {response.text[:100]}")

            try:
                json_data = response.json()
            except Exception as json_err:
                raise RuntimeError(f"Polygon JSON decode error for {ticker}: {json_err}")

            data = json_data.get("results", [])
            if not data:
                raise ValueError(f"No data in Polygon response for {ticker}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for ticker '{ticker}' from Polygon: {e}")

    df = pd.DataFrame(data)
    if "t" not in df.columns:
        raise KeyError("Missing timestamp column 't'.")

    df["Date"] = pd.to_datetime(df["t"], unit="ms").dt.date
    df.rename(columns={"c": "Close"}, inplace=True)
    df.dropna(subset=["Date", "Close"], inplace=True)
    return df[["Date", "High", "Low", "Close"]] if full_ohlc else df[["Date", "Close"]]

if __name__ == "__main__":
    import sys
    import time
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = "6mo"

    print(f"\n⏱️ Benchmarking stock data fetch for '{ticker}'")

    # Polygon
    try:
        start = time.perf_counter()
        df_polygon = asyncio.run(fetch_from_polygon(ticker, period, full_ohlc=False))
        polygon_time = time.perf_counter() - start
        print(f"\n✅ Polygon API Success ({polygon_time:.2f} sec):")
        print(df_polygon.head())
    except Exception as e:
        polygon_time = None
        print(f"\n❌ Polygon failed: {e}")

    # yfinance
    try:
        start = time.perf_counter()
        df_yf = get_yfinance_df(ticker, period, full_ohlc=False)
        yf_time = time.perf_counter() - start
        print(f"\n✅ yfinance Success ({yf_time:.2f} sec):")
        print(df_yf.head())
    except Exception as e:
        yf_time = None
        print(f"\n❌ yfinance failed: {e}")

    # Summary
    if polygon_time and yf_time:
        print(f"\n🏁 Faster API: {'Polygon' if polygon_time < yf_time else 'yfinance'}")