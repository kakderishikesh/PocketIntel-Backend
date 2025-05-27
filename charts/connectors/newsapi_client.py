import os
import httpx
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
import logging

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Environment & constants ---
load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_URL = "https://newsapi.org/v2/everything"
vader = SentimentIntensityAnalyzer()


def classify_headlines_with_vader(headlines: List[str]) -> List[str]:
    sentiments = []
    for text in headlines:
        if not text:
            sentiments.append("neutral")
            continue
        score = vader.polarity_scores(text)["compound"]
        if score >= 0.2:
            sentiments.append("positive")
        elif score <= -0.2:
            sentiments.append("negative")
        else:
            sentiments.append("neutral")
    return sentiments


async def fetch_headlines_newsapi(client: httpx.AsyncClient, subject: str, from_date: str, to_date: str) -> List[str]:
    params = {
        "q": subject,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 50,
        "apiKey": NEWSAPI_KEY
    }

    try:
        logger.info(f"📰 Fetching headlines for '{subject}' from {from_date} to {to_date}...")
        resp = await client.get(NEWSAPI_URL, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        logger.info(f"📄 Retrieved {len(articles)} articles for {from_date}.")
        return [a.get("description", "") for a in articles]
    except Exception as e:
        logger.error(f"[NewsAPI error for {from_date}] {e}", exc_info=True)
        return []


async def fetch_news_sentiment_data(subject: str, classifier: str = "vader") -> pd.DataFrame:
    """
    Fetch news headlines from NewsAPI for the past 5 days and classify sentiment.
    Returns a DataFrame with columns: date, positive, neutral, negative
    """
    logger.info(f"🧠 Starting sentiment analysis for '{subject}' using {classifier}...")
    today = datetime.today()
    date_ranges = [
        (
            (today - timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            (today - timedelta(days=i)).strftime("%Y-%m-%d")
        )
        for i in reversed(range(5))
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_headlines_newsapi(client, subject, start, end) for start, end in date_ranges]
        all_article_batches = await asyncio.gather(*tasks)

        result = []
        for (start_date, _), headlines in zip(date_ranges, all_article_batches):
            sentiments = classify_headlines_with_vader(headlines)
            counts = {"positive": 0, "neutral": 0, "negative": 0}
            for s in sentiments:
                counts[s] += 1

            logger.info(f"📊 {start_date}: {counts} from {len(headlines)} headlines")
            result.append({"date": start_date, **counts})

        df = pd.DataFrame(result)
        logger.info(f"✅ Sentiment data shape: {df.shape}")
        logger.debug(f"\n{df.head()}")
        return df


if __name__ == "__main__":
    subject = "nvidia"
    df = asyncio.run(fetch_news_sentiment_data(subject))
    print(df)
