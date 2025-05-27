import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import pandas as pd

from modules.prompt_generator import generate_prompts
from modules.sonar_client import fetch_sonar_responses
from modules.response_parser import parse_sonar_responses
from modules.summarizer import generate_360_summary
from modules.agent_intent_handler import get_subject_and_focus_from_agent

from charts.connectors.sector_growth_client import get_sector_typical_prices
from charts.connectors.stockprice_client import fetch_stock_price_data
from charts.connectors.pytrends_client import fetch_google_trend_data
from charts.connectors.newsapi_client import fetch_news_sentiment_data
from charts.chart_utils import format_chart_block

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Starting FastAPI app...")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    query: str

@app.post("/analyze")
async def analyze(input: QueryInput):
    query = input.query
    logger.info(f"Received query: {query}")
    output = {"summary": {}, "charts": []}

    # Step 1: Intent recognition
    try:
        intent = get_subject_and_focus_from_agent(query)
        logger.info(f"Intent detected: {intent}")
    except Exception as e:
        logger.error(f"[Intent Recognition Error] {e}", exc_info=True)
        return output

    if intent.get("type") == "direct_answer" and "answer" in intent:
        logger.info("Direct answer provided from intent.")
        output["summary"] = {
            "content": intent.get("answer", ""),
            "citations": intent.get("citations", [])
        }
        return output

    subject = intent.get("subject")
    sector = intent.get("sector")
    ticker = intent.get("ticker")
    focuses = intent.get("focus", [])

    chart_tasks = []

    try:
        if sector:
            try:
                chart_tasks.append(get_sector_typical_prices())
            except Exception as e:
                logger.error(f"[Sector Growth Fetch Error] Failed to fetch sector data: {e}", exc_info=True)
        if ticker:
            try:
                chart_tasks.append(fetch_stock_price_data(ticker))
            except Exception as e:
                logger.error(f"[Stock Price Fetch Error] Failed to fetch data for ticker: {ticker} - {e}", exc_info=True)
        if subject:
            chart_tasks.append(fetch_google_trend_data(subject))
            chart_tasks.append(fetch_news_sentiment_data(subject))

        chart_results = await asyncio.gather(*chart_tasks, return_exceptions=True)
        logger.info("Chart data fetched successfully.")
    except Exception as e:
        logger.error(f"[Chart Gathering Error] {e}", exc_info=True)
        chart_results = []

    result_idx = 0

    def safe_append_chart(df, chart_type, title, description, highlight=None):
        try:
            if isinstance(df, pd.DataFrame):
                output["charts"].append(format_chart_block(
                    chart_type=chart_type,
                    title=title,
                    description=description,
                    df=df,
                    legend=list(df.columns),
                    highlight=highlight
                ))
                logger.info(f"Appended chart: {title}")
        except Exception as e:
            logger.error(f"[Chart Formatting Error] {title}: {e}", exc_info=True)

    try:
        if sector:
            df = chart_results[result_idx]; result_idx += 1
            safe_append_chart(df, "line", "Sector Growth (Typical Price)", f"Growth comparison across all sectors with {sector} highlighted.", highlight=sector)
        if ticker:
            df = chart_results[result_idx]; result_idx += 1
            safe_append_chart(df, "line", f"{ticker} Stock Price", f"{ticker} daily OHLC price chart")
        if subject:
            py_df = chart_results[result_idx]; result_idx += 1
            news_df = chart_results[result_idx]; result_idx += 1
            safe_append_chart(py_df, "line", f"{subject} Search Trends", f"Search interest for '{subject}' over time")
            safe_append_chart(news_df, "bar", f"{subject} News Sentiment", f"News sentiment breakdown for '{subject}'")
    except Exception as e:
        logger.error(f"[Chart Processing Error] {e}", exc_info=True)

    try:
        prompts = generate_prompts(subject, focuses)
        responses = await fetch_sonar_responses(prompts)
        structured_data = parse_sonar_responses(responses)
        output["summary"] = structured_data
        logger.info("Sonar summary generated.")
    except Exception as e:
        logger.error(f"[Sonar Processing Error] {e}", exc_info=True)

    return output

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
