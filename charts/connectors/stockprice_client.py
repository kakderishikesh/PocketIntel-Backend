import httpx
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import yfinance as yf
import logging

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Load env vars ---
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise EnvironmentError("POLYGON_API_KEY not found in environment variables.")

ETF_TICKERS = {
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "XLU", "XLB", "XLRE", "XLC"
}

# --- Main fetcher ---
async def fetch_stock_price_data(ticker: str, period: str = "6mo", full_ohlc: bool = True) -> pd.DataFrame:
    try:
        logger.info(f"[{ticker}] Fetching from yfinance (primary)...")
        return await asyncio.to_thread(get_yfinance_df, ticker, period, full_ohlc)
    except Exception as e:
        logger.warning(f"[{ticker}] yfinance failed: {e} — attempting Polygon fallback.", exc_info=True)
        try:
            return await fetch_from_polygon(ticker, period, full_ohlc)
        except Exception as fallback_error:
            logger.error(f"[{ticker}] Polygon fallback also failed: {fallback_error}", exc_info=True)
            raise

# --- yfinance ---
def get_yfinance_df(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
    import time

    for attempt in range(3):
        try:
            logger.debug(f"[{ticker}] yfinance attempt {attempt+1}")
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
            break
        except Exception as e:
            logger.warning(f"[{ticker}] yfinance retry {attempt+1} failed: {e}", exc_info=True)
            time.sleep(1)
    else:
        raise RuntimeError(f"[{ticker}] yfinance failed after 3 retries")

    if df.empty:
        raise ValueError(f"[{ticker}] yfinance returned empty data")

    # Handle MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        if ticker in df.columns.levels[1]:
            df = df.xs(ticker, axis=1, level=1)
        else:
            try:
                df.columns = df.columns.get_level_values(0)
            except Exception:
                raise ValueError(f"[{ticker}] Unable to flatten MultiIndex from yfinance")

    df = df.reset_index()
    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]

    expected_cols = ["Date", "Close"] if not full_ohlc else ["Date", "High", "Low", "Close"]
    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        raise KeyError(f"[{ticker}] Missing columns from yfinance: {missing}")

    df["Date"] = pd.to_datetime(df["Date"])
    df.dropna(subset=expected_cols, inplace=True)
    return df[expected_cols].reset_index(drop=True)

# --- Polygon API ---
async def fetch_from_polygon(ticker: str, period: str, full_ohlc: bool) -> pd.DataFrame:
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
            if not response.text.strip().startswith("{"):
                raise RuntimeError(f"Polygon API returned non-JSON: {response.text[:100]}")
            try:
                json_data = response.json()
            except Exception as json_err:
                raise RuntimeError(f"Polygon JSON decode error: {json_err}")
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
    logger.info(f"[{ticker}] Polygon fetched {len(df)} rows")
    return df[["Date", "High", "Low", "Close"]] if full_ohlc else df[["Date", "Close"]]

# --- CLI Benchmark ---
if __name__ == "__main__":
    import sys
    import time

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = "6mo"

    logger.info(f"\n⏱️ Benchmarking stock data fetch for '{ticker}'")

    # Polygon
    try:
        start = time.perf_counter()
        df_polygon = asyncio.run(fetch_from_polygon(ticker, period, full_ohlc=False))
        polygon_time = time.perf_counter() - start
        logger.info(f"✅ Polygon Success ({polygon_time:.2f}s)\n{df_polygon.head()}")
    except Exception as e:
        polygon_time = None
        logger.error(f"❌ Polygon failed: {e}", exc_info=True)

    # yfinance
    try:
        start = time.perf_counter()
        df_yf = get_yfinance_df(ticker, period, full_ohlc=False)
        yf_time = time.perf_counter() - start
        logger.info(f"✅ yfinance Success ({yf_time:.2f}s)\n{df_yf.head()}")
    except Exception as e:
        yf_time = None
        logger.error(f"❌ yfinance failed: {e}", exc_info=True)

    # Comparison
    if polygon_time and yf_time:
        faster = "Polygon" if polygon_time < yf_time else "yfinance"
        logger.info(f"🏁 Faster API: {faster}")
