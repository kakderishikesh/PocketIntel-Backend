import os
import logging
import asyncio
import httpx
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tiingo import TiingoClient

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Load API keys ---
load_dotenv()
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

if not TIINGO_API_KEY:
    raise EnvironmentError("TIINGO_API_KEY not found in environment variables.")
if not POLYGON_API_KEY:
    raise EnvironmentError("POLYGON_API_KEY not found in environment variables.")

# --- Tiingo setup ---
tiingo_client = TiingoClient({
    "session": True,
    "api_key": TIINGO_API_KEY
})

ETF_TICKERS = {
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "XLU", "XLB", "XLRE", "XLC"
}

from pathlib import Path

CACHE_DIR = "./.cache/stock_data"
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_CACHE_AGE_HOURS = 24

def get_cache_path(ticker: str, period: str, full_ohlc: bool, source: str = "tiingo") -> str:
    return os.path.join(CACHE_DIR, f"{source}_{ticker}_{period}_{'ohlc' if full_ohlc else 'close'}.parquet")

def is_cache_fresh(path: str, max_age_hours: int = MAX_CACHE_AGE_HOURS) -> bool:
    if not os.path.exists(path):
        return False
    file_time = datetime.fromtimestamp(Path(path).stat().st_mtime)
    return (datetime.now() - file_time) < timedelta(hours=max_age_hours)

# --- Main fetcher ---
async def fetch_stock_price_data(ticker: str, period: str = "6mo", full_ohlc: bool = True) -> pd.DataFrame:
    try:
        logger.info(f"[{ticker}] Fetching from Tiingo (primary)...")
        return await asyncio.to_thread(fetch_from_tiingo, ticker, period, full_ohlc)
    except Exception as e:
        logger.warning(f"[{ticker}] Tiingo failed: {e} — attempting Polygon fallback.", exc_info=True)
        try:
            return await fetch_from_polygon(ticker, period, full_ohlc)
        except Exception as fallback_error:
            logger.error(f"[{ticker}] Polygon fallback also failed: {fallback_error}", exc_info=True)
            raise

# --- Tiingo ---
def fetch_from_tiingo(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
    cache_path = get_cache_path(ticker, period, full_ohlc, source="tiingo")
    if is_cache_fresh(cache_path):
        logger.info(f"[{ticker}] Using cached Tiingo data from {cache_path}")
        return pd.read_parquet(cache_path)

    if period.endswith("mo"):
        days = int(period[:-2]) * 30
    elif period.endswith("y"):
        days = int(period[:-1]) * 365
    else:
        raise ValueError("Unsupported period format. Use '6mo', '1y', etc.")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    df = tiingo_client.get_dataframe(
        ticker,
        frequency='daily',
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d")
    )

    if df.empty:
        raise ValueError(f"[{ticker}] Tiingo returned empty DataFrame.")

    df = df.reset_index()
    df.rename(columns={"date": "Date","high": "High","low":"Low","close":"Close"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    expected_cols = ["Date", "Close"] if not full_ohlc else ["Date", "High", "Low", "Close"]
    missing = [col for col in expected_cols if col.lower() not in df.columns.str.lower()]
    if missing:
        raise KeyError(f"[{ticker}] Missing columns from Tiingo: {missing}")

    result = df[expected_cols] if full_ohlc else df[["Date", "Close"]]
    result = result.rename(columns=str.capitalize).reset_index(drop=True)
    result.to_parquet(cache_path, index=False)
    logger.info(f"[{ticker}] Cached Tiingo result to {cache_path}")
    return result

# --- Polygon fallback ---
async def fetch_from_polygon(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
    cache_path = get_cache_path(ticker, period, full_ohlc, source="polygon")
    if is_cache_fresh(cache_path):
        logger.info(f"[{ticker}] Using cached Polygon data from {cache_path}")
        return pd.read_parquet(cache_path)

    logger.info(f"[{ticker}] Fetching from Polygon...")
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
            if response.status_code != 200:
                raise RuntimeError(f"Polygon API returned {response.status_code}: {response.text[:100]}")
            json_data = response.json()
            data = json_data.get("results", [])
            if not data:
                raise ValueError("No data in Polygon response")
        except Exception as e:
            logger.error(f"[{ticker}] Polygon API fetch failed: {e}", exc_info=True)
            raise

    df = pd.DataFrame(data)
    if "t" not in df.columns:
        raise KeyError("Missing 't' (timestamp) column in Polygon response")

    df["Date"] = pd.to_datetime(df["t"], unit="ms").dt.date
    df.rename(columns={"c": "Close"}, inplace=True)
    df.dropna(subset=["Date", "Close"], inplace=True)
    result = df[["Date", "High", "Low", "Close"]] if full_ohlc else df[["Date", "Close"]]
    result.to_parquet(cache_path, index=False)
    logger.info(f"[{ticker}] Polygon fetched and cached {len(result)} rows to {cache_path}")
    return result

# --- CLI Benchmark ---
if __name__ == "__main__":
    import sys
    import time

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = "6mo"

    logger.info(f"\n⏱️ Benchmarking stock data fetch for '{ticker}'")

    try:
        start = time.perf_counter()
        df = asyncio.run(fetch_stock_price_data(ticker, period, full_ohlc=False))
        elapsed = time.perf_counter() - start
        logger.info(f"✅ Success ({elapsed:.2f}s)\n{df.head()}")
    except Exception as e:
        logger.error(f"❌ Failed to fetch data: {e}", exc_info=True)
