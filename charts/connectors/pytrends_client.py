import logging
from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import asyncio

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_google_trend_data(term: str, weeks: int = 12) -> pd.DataFrame:
    """
    Asynchronously fetch Google Trends interest data for a given term over the past N weeks.
    Returns a DataFrame with columns: date, <term>
    """
    def fetch_sync():
        try:
            logger.info(f"📈 Fetching Google Trends for '{term}' over the past {weeks} weeks...")

            timeframe = (
                (datetime.today() - timedelta(weeks=weeks)).strftime("%Y-%m-%d") +
                " " +
                datetime.today().strftime("%Y-%m-%d")
            )
            logger.debug(f"Timeframe used: {timeframe}")

            pytrends = TrendReq(hl="en-US", tz=360)
            pytrends.build_payload([term], timeframe=timeframe, geo="")

            data = pytrends.interest_over_time()
            if data.empty:
                raise ValueError(f"No trend data found for: {term}")

            df = data.reset_index()[["date", term]]
            logger.info(f"✅ Google Trends fetched successfully — shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch Google Trends data for '{term}': {e}", exc_info=True)
            raise

    return await asyncio.to_thread(fetch_sync)


# --- CLI test ---
if __name__ == "__main__":
    async def run():
        df = await fetch_google_trend_data("nvidia", weeks=12)
        print(df.head())

    asyncio.run(run())
