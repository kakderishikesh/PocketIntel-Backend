# PocketIntel Backend

**PocketIntel** is a real-time, AI-powered financial insights platform that helps users make informed decisions by converting natural language queries into structured analysis and visualizations.

The backend is built with **FastAPI**, designed to be modular, async-first, and capable of dynamically generating insights using the **Perplexity Sonar API** along with external financial data sources.

## Important Links

* Link to the deployed website: https://pocketintel.vercel.app/
* Link to the Frontend Repo (private access only): https://github.com/kakderishikesh/PocketIntel-Frontend 

## 🧠 Project Overview

The PocketIntel backend is the core logic engine of the platform. It processes user queries, interprets the intent using Sonar, fetches structured data from external APIs, and returns chart-ready data blocks enriched with contextual metadata and insights.

It also handles execution of dynamic Python code, manages agent coordination, and formats outputs for rendering on the frontend.

---

## 🔍 Core Features

- **Natural Language Query Interpretation**  
  Uses Perplexity Sonar API to extract subject and focus from freeform text.

- **Multi-Pillar Analysis Pipeline**  
  Maps Sonar-derived focus areas (e.g., performance, sentiment, trends) to chartable dimensions.

- **Dynamic Chart Block Generation**  
  Returns chart-ready JSON objects containing data, insights, and metadata (`visualizationType`, `xKey`, `yKey`).

- **Asynchronous Data Fetching**  
  Fully async backend that supports parallel data retrieval from external APIs.

- **External Data Connectors**  
  Modular support for Tiingo (stock prices), Google Trends, Polygon.io (news), and more.

- **Smart Fallback Handling**  
  Switches between data providers (e.g., Tiingo → yFinance) based on availability and rate limits.

- **Direct Answer Mode**  
  Bypasses full pipeline for low-context queries to return fast, focused results.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Async Engine**: asyncio, httpx
- **Data Handling**: Pandas
- **External APIs**:
  - Perplexity Sonar API (intent + research)
  - Tiingo (stock data)
  - Polygon.io (news sentiment)
  - Google Trends (via pytrends)
- **Chart Rendering**: Chart-ready JSON with metadata
- **Database (optional)**: Supabase PostgreSQL with pgvector (for vector similarity search)

---

## 📁 Project Structure

```
PocketIntel-Backend/
├── charts/
│ ├── connectors/ # External data API clients
│ │ ├── newsapi_client.py # Polygon or NewsAPI integration
│ │ ├── pytrends_client.py # Google Trends connector
│ │ ├── sector_growth_client.py # Sector/industry trends
│ │ └── stockprice_client_tiingo.py # Tiingo stock data (primary)
│ └── chart_utils.py # Chart formatting and helper functions
│
├── modules/
│ ├── agent_intent_handler.py # Interprets Sonar intent and guides analysis logic
│ ├── prompt_generator.py # Prompt building utilities
│ ├── response_parser.py # Normalizes and parses Sonar responses
│ ├── sonar_client.py # Handles Perplexity Sonar API calls
│ └── summarizer.py # Merges article text and generates insight blocks
│
├── main.py # FastAPI app entry point
├── config.py # Global config and constants
├── .env # Environment variables (API keys, etc.)
├── .gitignore # Git ignore rules
├── Procfile # Deployment config (e.g., for Railway)
├── railway.json # Railway deployment settings
├── requirements.txt # Python dependencies
├── runtime.txt # Python runtime version for deployment
├── README.md # Project documentation (this file)
```
## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/GautamKataria/PocketIntel-Backend
   cd PocketIntel-Backend
   
2. **Set up environment variables**
    Create a .env file with your API keys:
   ```
    POLYGON_API_KEY=your_key
    TIINGO_API_KEY=your_key
    SONAR_API_KEY=your_key
    ```
3. **Install dependencies**
  ```
   pip install -r requirements.txt
  ```
4. **Run the server**
  ```
      uvicorn main:app --reload
  ```

## 🧩 Key Endpoints
```
POST /analyze
```
Accepts a query string and returns structured analysis blocks for frontend rendering.

## 📡 External APIs Used
 - Perplexity Sonar	Intent detection + article insights
 - Tiingo	Historical stock price data
 - Polygon.io	Fallback stock data provider
 - NewsAPI	News headlines
 - Google Trends	Search interest and trend signals

## Contact Information

### Team Members

#### Rishikesh Kakde
- Email: rishikesh.kakde59@gmail.com
- GitHub: [@kakderishikesh](https://github.com/kakderishikesh)
- LinkedIn: [Rishikesh Kakde](https://www.linkedin.com/in/rishikeshkakde/)

#### Gautam Kataria
- Email: gautzzkataria@gmail.com
- GitHub: [@GautamKataria](https://github.com/GautamKataria)
- LinkedIn: [Gautam Kataria](https://www.linkedin.com/in/gautam-kataria/)
