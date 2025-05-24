import os
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in .env file.")
if not NEWSAPI_KEY:
    raise ValueError("NEWSAPI_KEY not found in .env file.")
if not POLYGON_API_KEY:
    raise ValueError("POLYGON_API_KEY not found in .env file.")