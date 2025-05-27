from stockprice_client import fetch_stock_price_data
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import asyncio


async def get_sector_typical_prices(period: str = "6mo") -> pd.DataFrame:
    sector_etfs = {
        "Technology": "XLK",
        "Financials": "XLF",
        "Energy": "XLE",
        "Healthcare": "XLV",
        "Consumer Discretionary": "XLY",
        "Industrials": "XLI",
        "Utilities": "XLU",
        "Materials": "XLB",
        "Real Estate": "XLRE",
        "Communication Services": "XLC"
    }

    async def get_typical_price(sector, ticker):
        try:
            df = await fetch_stock_price_data(ticker, period=period, full_ohlc=True)
            df.set_index("Date", inplace=True)
            typical = (df["High"] + df["Low"] + df["Close"]) / 3
            return sector, typical
        except Exception as e:
            print(f"[{sector}] Failed to fetch typical price: {e}")
            return sector, None

    tasks = [get_typical_price(sector, ticker) for sector, ticker in sector_etfs.items()]
    results = await asyncio.gather(*tasks)
    print(pd.DataFrame({sector: ts for sector, ts in results if ts is not None}))

    return pd.DataFrame({sector: ts for sector, ts in results if ts is not None})
async def plot_absolute_prices(highlight_sector: str = None):
    df = await get_sector_typical_prices()
    plt.figure(figsize=(14, 8))
    sns.set_style("whitegrid")

    for sector in df.columns:
        if sector == highlight_sector:
            plt.plot(df.index, df[sector], label=f"{sector} (Highlighted)", linewidth=2.5, color="darkred")
        else:
            plt.plot(df.index, df[sector], label=sector, linewidth=1, linestyle="--", alpha=0.5)

    plt.title(f"Typical Prices of Sectors\nHighlight: {highlight_sector or 'None'}")
    plt.xlabel("Date")
    plt.ylabel("Typical Price")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.xticks(rotation=45)
    plt.show()


async def plot_normalized_growth(highlight_sector: str = None):
    df = await get_sector_typical_prices()
    normalized = df / df.iloc[0] * 100

    plt.figure(figsize=(14, 8))
    sns.set_style("whitegrid")

    for sector in normalized.columns:
        if sector == highlight_sector:
            plt.plot(normalized.index, normalized[sector], label=f"{sector} (Highlighted)", linewidth=2.5, color="darkred")
        else:
            plt.plot(normalized.index, normalized[sector], label=sector, linewidth=1, linestyle="--", alpha=0.5)

    plt.title(f"Normalized Sector Growth (Base = 100)\nHighlight: {highlight_sector or 'None'}")
    plt.xlabel("Date")
    plt.ylabel("Growth Index (Base = 100)")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.xticks(rotation=45)
    plt.show()


if __name__ == "__main__":
    # asyncio.run(plot_absolute_prices(highlight_sector="Technology"))
    # asyncio.run(plot_normalized_growth(highlight_sector="Technology"))
    asyncio.run(get_sector_typical_prices())