from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import asyncio


async def fetch_google_trend_data(term: str, weeks: int = 12) -> pd.DataFrame:
    """
    Asynchronously fetch Google Trends interest data for a given term over the past N weeks.
    Returns a DataFrame with columns: date, <term>
    """
    def fetch_sync():
        pytrends = TrendReq(hl="en-US", tz=360)
        timeframe = (
            (datetime.today() - timedelta(weeks=weeks)).strftime("%Y-%m-%d") +
            " " +
            datetime.today().strftime("%Y-%m-%d")
        )
        pytrends.build_payload([term], timeframe=timeframe, geo="")
        data = pytrends.interest_over_time()

        if data.empty:
            raise ValueError(f"No trend data found for: {term}")

        return data.reset_index()[["date", term]]

    return await asyncio.to_thread(fetch_sync)


if __name__ == "__main__":
    async def run():
        df = await fetch_google_trend_data("nvidia", weeks=12)
        print(df.head())

    asyncio.run(run())
