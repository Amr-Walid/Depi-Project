"""
Data service — provides coin data, market overview, and price history.

Currently returns structured mock data that matches the exact schema
the Gold Layer (dbt) will produce. When Gold Layer is ready, only the
internals of these functions need to change — the API contract stays the same.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.config import SUPPORTED_COINS


# ──────────────────────────────────────────────
# Coin name mapping
# ──────────────────────────────────────────────
COIN_NAMES = {
    "BTCUSDT": "Bitcoin",
    "ETHUSDT": "Ethereum",
    "BNBUSDT": "BNB",
    "XRPUSDT": "XRP",
    "ADAUSDT": "Cardano",
    "SOLUSDT": "Solana",
    "DOTUSDT": "Polkadot",
    "DOGEUSDT": "Dogecoin",
    "MATICUSDT": "Polygon",
    "LINKUSDT": "Chainlink",
    "AVAXUSDT": "Avalanche",
    "UNIUSDT": "Uniswap",
    "ATOMUSDT": "Cosmos",
    "LTCUSDT": "Litecoin",
    "ETCUSDT": "Ethereum Classic",
    "XLMUSDT": "Stellar",
    "ALGOUSDT": "Algorand",
    "VETUSDT": "VeChain",
    "ICPUSDT": "Internet Computer",
    "FILUSDT": "Filecoin",
}

# Mock base prices for realistic data generation
MOCK_BASE_PRICES = {
    "BTCUSDT": 68500.0,
    "ETHUSDT": 3450.0,
    "BNBUSDT": 580.0,
    "XRPUSDT": 0.55,
    "ADAUSDT": 0.45,
    "SOLUSDT": 145.0,
    "DOTUSDT": 7.2,
    "DOGEUSDT": 0.16,
    "MATICUSDT": 0.72,
    "LINKUSDT": 14.5,
    "AVAXUSDT": 35.0,
    "UNIUSDT": 7.8,
    "ATOMUSDT": 8.9,
    "LTCUSDT": 82.0,
    "ETCUSDT": 26.0,
    "XLMUSDT": 0.11,
    "ALGOUSDT": 0.18,
    "VETUSDT": 0.028,
    "ICPUSDT": 12.5,
    "FILUSDT": 5.8,
}


def get_supported_coins() -> List[dict]:
    """
    Return list of all supported cryptocurrency coins.
    
    Returns:
        List of coin info dictionaries with symbol, name, and active status.
    """
    return [
        {
            "symbol": symbol,
            "name": COIN_NAMES.get(symbol, symbol.replace("USDT", "")),
            "is_active": True,
        }
        for symbol in SUPPORTED_COINS
    ]


def get_coin_summary(symbol: str) -> Optional[dict]:
    """
    Get daily summary for a specific coin.
    
    When Gold Layer is ready, this will query the coin_daily_summary table.
    Currently returns realistic mock data.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
    
    Returns:
        Dictionary with daily summary or None if coin not found
    """
    symbol = symbol.upper()
    if symbol not in MOCK_BASE_PRICES:
        return None

    base_price = MOCK_BASE_PRICES[symbol]
    # Generate realistic daily variation (±3%)
    random.seed(hash(symbol + datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    variation = random.uniform(-0.03, 0.03)

    day_open = base_price * (1 + random.uniform(-0.01, 0.01))
    day_close = base_price * (1 + variation)
    day_high = max(day_open, day_close) * (1 + random.uniform(0.005, 0.02))
    day_low = min(day_open, day_close) * (1 - random.uniform(0.005, 0.02))
    price_change_pct = ((day_close - day_open) / day_open) * 100

    return {
        "symbol": symbol,
        "trading_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "day_open": round(day_open, 2),
        "day_close": round(day_close, 2),
        "day_high": round(day_high, 2),
        "day_low": round(day_low, 2),
        "total_volume": round(random.uniform(1_000_000, 50_000_000), 2),
        "avg_price": round((day_open + day_close) / 2, 2),
        "price_change_pct": round(price_change_pct, 4),
        "tick_count": random.randint(50000, 200000),
    }


def get_coin_prices(symbol: str, days: int = 30) -> Optional[dict]:
    """
    Get historical price data for a coin.
    
    When Gold Layer is ready, this will query ADLS Gen2 via the Gold tables.
    Currently returns realistic mock OHLCV data.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        days: Number of days of history to return (default: 30)
    
    Returns:
        Dictionary with symbol, days, and list of price data points
    """
    symbol = symbol.upper()
    if symbol not in MOCK_BASE_PRICES:
        return None

    base_price = MOCK_BASE_PRICES[symbol]
    prices = []
    current_price = base_price

    for i in range(days, 0, -1):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        # Random walk for realistic price movement
        random.seed(hash(symbol + date.strftime("%Y-%m-%d")))
        change = random.uniform(-0.04, 0.04)
        current_price = current_price * (1 + change)

        day_open = current_price * (1 + random.uniform(-0.01, 0.01))
        day_close = current_price
        day_high = max(day_open, day_close) * (1 + random.uniform(0.005, 0.02))
        day_low = min(day_open, day_close) * (1 - random.uniform(0.005, 0.02))

        prices.append({
            "timestamp": date.strftime("%Y-%m-%dT00:00:00Z"),
            "open": round(day_open, 2),
            "high": round(day_high, 2),
            "low": round(day_low, 2),
            "close": round(day_close, 2),
            "volume": round(random.uniform(500_000, 30_000_000), 2),
        })

    return {
        "symbol": symbol,
        "days": days,
        "prices": prices,
    }


def get_market_overview() -> dict:
    """
    Get market-wide overview statistics.
    
    When Gold Layer is ready, this will aggregate from the Gold tables.
    Currently returns realistic mock data.
    
    Returns:
        Dictionary with market-wide stats including top gainers and losers.
    """
    # Generate summaries for all coins to find top gainers/losers
    summaries = []
    for symbol in SUPPORTED_COINS:
        summary = get_coin_summary(symbol)
        if summary:
            summaries.append(summary)

    # Sort by price change to find gainers and losers
    sorted_by_change = sorted(summaries, key=lambda x: x["price_change_pct"], reverse=True)

    top_gainers = [
        {"symbol": s["symbol"], "name": COIN_NAMES.get(s["symbol"], ""), "change_pct": s["price_change_pct"]}
        for s in sorted_by_change[:5]
    ]
    top_losers = [
        {"symbol": s["symbol"], "name": COIN_NAMES.get(s["symbol"], ""), "change_pct": s["price_change_pct"]}
        for s in sorted_by_change[-5:]
    ]

    return {
        "total_market_cap": round(random.uniform(2.0e12, 3.0e12), 2),
        "total_volume_24h": round(random.uniform(80e9, 150e9), 2),
        "btc_dominance": round(random.uniform(48.0, 55.0), 2),
        "active_coins": len(SUPPORTED_COINS),
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
