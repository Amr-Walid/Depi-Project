import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import SUPPORTED_COINS
from app.database import get_db


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


def get_coin_summary(symbol: str, db: Session) -> Optional[dict]:
    """
    Get daily summary for a specific coin.
    
    Queries the gold.daily_market_summary table in PostgreSQL.
    """
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        return None

    query = text("""
        SELECT symbol, date, open_price, high_price, low_price, close_price, total_volume
        FROM gold.daily_market_summary
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT 1
    """)
    result = db.execute(query, {"symbol": symbol}).fetchone()
    
    if not result:
        return None

    open_p = float(result.open_price)
    close_p = float(result.close_price)
    price_change_pct = ((close_p - open_p) / open_p * 100) if open_p > 0 else 0

    return {
        "symbol": result.symbol,
        "trading_date": result.date.strftime("%Y-%m-%d"),
        "day_open": round(open_p, 4),
        "day_close": round(close_p, 4),
        "day_high": round(float(result.high_price), 4),
        "day_low": round(float(result.low_price), 4),
        "total_volume": round(float(result.total_volume), 2),
        "avg_price": round((open_p + close_p) / 2, 4),
        "price_change_pct": round(price_change_pct, 4),
        "tick_count": 0,
    }


def get_coin_prices(symbol: str, days: int, db: Session) -> Optional[dict]:
    """
    Get historical price data for a coin.
    
    Queries gold.daily_market_summary for the last N days.
    """
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        return None

    query = text("""
        SELECT date, open_price, high_price, low_price, close_price, total_volume
        FROM gold.daily_market_summary
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT :days
    """)
    results = db.execute(query, {"symbol": symbol, "days": days}).fetchall()

    prices = []
    # Reverse to return chronologically (oldest first)
    for row in reversed(results):
        prices.append({
            "timestamp": row.date.strftime("%Y-%m-%dT00:00:00Z"),
            "open": float(row.open_price),
            "high": float(row.high_price),
            "low": float(row.low_price),
            "close": float(row.close_price),
            "volume": float(row.total_volume),
        })

    return {
        "symbol": symbol,
        "days": days,
        "prices": prices,
    }


def get_market_overview(db: Session) -> dict:
    """
    Get market-wide overview statistics.
    
    Aggregates from the latest data in gold.daily_market_summary.
    """
    # 1. Get the latest date available in the database
    latest_date_query = text("SELECT MAX(date) FROM gold.daily_market_summary")
    latest_date_result = db.execute(latest_date_query).scalar()

    if not latest_date_result:
        return {
            "total_market_cap": 0.0,
            "total_volume_24h": 0.0,
            "btc_dominance": 0.0,
            "active_coins": len(SUPPORTED_COINS),
            "top_gainers": [],
            "top_losers": [],
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    # 2. Get summaries for the latest date for all coins
    query = text("""
        SELECT symbol, open_price, close_price, total_volume
        FROM gold.daily_market_summary
        WHERE date = :latest_date
    """)
    results = db.execute(query, {"latest_date": latest_date_result}).fetchall()

    summaries = []
    total_volume_24h = 0.0
    btc_volume = 0.0

    for row in results:
        open_p = float(row.open_price)
        close_p = float(row.close_price)
        vol = float(row.total_volume)
        
        pct_change = ((close_p - open_p) / open_p * 100) if open_p > 0 else 0
        
        summaries.append({
            "symbol": row.symbol,
            "name": COIN_NAMES.get(row.symbol, row.symbol.replace("USDT", "")),
            "change_pct": round(pct_change, 2)
        })

        total_volume_24h += vol
        if row.symbol == "BTCUSDT":
            btc_volume = vol

    sorted_by_change = sorted(summaries, key=lambda x: x["change_pct"], reverse=True)
    top_gainers = sorted_by_change[:5] if len(sorted_by_change) >= 5 else sorted_by_change
    top_losers = sorted_by_change[-5:] if len(sorted_by_change) >= 5 else sorted_by_change

    # Market cap approximation based on volume since we lack circulating supply
    total_market_cap = total_volume_24h * 15.0
    btc_dominance = (btc_volume / total_volume_24h * 100) if total_volume_24h > 0 else 50.0

    return {
        "total_market_cap": round(total_market_cap, 2),
        "total_volume_24h": round(total_volume_24h, 2),
        "btc_dominance": round(btc_dominance, 2),
        "active_coins": len(SUPPORTED_COINS),
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "last_updated": latest_date_result.strftime("%Y-%m-%dT00:00:00Z"),
    }
