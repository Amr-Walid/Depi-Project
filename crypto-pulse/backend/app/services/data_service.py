import logging
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import SUPPORTED_COINS

logger = logging.getLogger(__name__)


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


def _format_date(value) -> str:
    """Format DB date values from PostgreSQL or SQLite consistently."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _format_timestamp(value) -> Optional[str]:
    """Format DB date/timestamp values as an API UTC timestamp string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%dT00:00:00Z")

    text_value = str(value)
    if text_value.endswith("Z") and "T" in text_value:
        return text_value
    if len(text_value) >= 10 and text_value[4] == "-" and text_value[7] == "-":
        return f"{text_value[:10]}T00:00:00Z"
    return text_value


def _neutral_sentiment_response() -> dict:
    return {
        "overall_score": 0.0,
        "overall_label": "Neutral",
        "positive_pct": 0.0,
        "negative_pct": 0.0,
        "neutral_pct": 0.0,
        "article_count": 0,
        "last_updated": None,
        "status": "sentiment_data_not_ready",
    }


def _sentiment_label(score: float) -> str:
    if score > 0.2:
        return "Bullish"
    if score < -0.2:
        return "Bearish"
    return "Neutral"


def _format_sentiment_row(row) -> Optional[dict]:
    if not row:
        return None

    data = row._mapping
    article_count = int(data.get("article_count") or 0)
    if article_count <= 0:
        return None

    overall_score = float(data.get("overall_score") or 0.0)
    positive_count = float(data.get("positive_count") or 0.0)
    negative_count = float(data.get("negative_count") or 0.0)
    neutral_count = float(data.get("neutral_count") or 0.0)

    return {
        "overall_score": round(overall_score, 4),
        "overall_label": data.get("overall_label") or _sentiment_label(overall_score),
        "positive_pct": round((positive_count / article_count) * 100, 2),
        "negative_pct": round((negative_count / article_count) * 100, 2),
        "neutral_pct": round((neutral_count / article_count) * 100, 2),
        "article_count": article_count,
        "last_updated": _format_timestamp(data.get("last_updated")),
        "status": None,
    }


def _run_sentiment_queries(db: Session, source_name: str, queries: List) -> Optional[dict]:
    errors = []
    for query in queries:
        try:
            row = db.execute(query).fetchone()
            sentiment = _format_sentiment_row(row)
            if sentiment:
                return sentiment

            logger.info("%s is available but has no usable sentiment rows.", source_name)
            return None
        except SQLAlchemyError as exc:
            db.rollback()
            errors.append(f"{exc.__class__.__name__}: {exc}")
        except (AttributeError, TypeError, ValueError) as exc:
            db.rollback()
            errors.append(f"{exc.__class__.__name__}: {exc}")

    if errors:
        logger.warning("%s unavailable or incompatible: %s", source_name, " | ".join(errors))
    return None


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
        "trading_date": _format_date(result.date),
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
            "timestamp": _format_timestamp(row.date),
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
        "last_updated": _format_timestamp(latest_date_result),
    }


def get_market_sentiment(db: Session) -> dict:
    """
    Get the latest market-wide sentiment overview.

    Uses gold.market_sentiment first, falls back to silver.news_sentiment while
    the sentiment pipeline is still being finalized, and returns a neutral
    structure when no sentiment data is ready.
    """
    gold_queries = [
        text("""
            SELECT
                sentiment_date AS last_updated,
                AVG(avg_sentiment_score) AS overall_score,
                SUM(article_count) AS article_count,
                SUM(positive_count) AS positive_count,
                SUM(negative_count) AS negative_count,
                SUM(neutral_count) AS neutral_count
            FROM gold.market_sentiment
            WHERE sentiment_date = (
                SELECT MAX(sentiment_date)
                FROM gold.market_sentiment
            )
            GROUP BY sentiment_date
        """),
        text("""
            SELECT
                sentiment_date AS last_updated,
                CASE
                    WHEN SUM(total_articles) > 0
                    THEN SUM(avg_sentiment_score * total_articles) / SUM(total_articles)
                    ELSE AVG(avg_sentiment_score)
                END AS overall_score,
                SUM(total_articles) AS article_count,
                SUM(positive_count) AS positive_count,
                SUM(negative_count) AS negative_count,
                SUM(neutral_count) AS neutral_count
            FROM gold.market_sentiment
            WHERE sentiment_date = (
                SELECT MAX(sentiment_date)
                FROM gold.market_sentiment
            )
            GROUP BY sentiment_date
        """),
    ]

    gold_sentiment = _run_sentiment_queries(db, "gold.market_sentiment", gold_queries)
    if gold_sentiment:
        return gold_sentiment

    logger.info("Falling back to silver.news_sentiment for market sentiment.")
    silver_queries = [
        text("""
            SELECT
                DATE(published_at) AS last_updated,
                AVG(sentiment_score) AS overall_score,
                COUNT(*) AS article_count,
                SUM(CASE WHEN LOWER(sentiment_label) = 'positive' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN LOWER(sentiment_label) = 'negative' THEN 1 ELSE 0 END) AS negative_count,
                SUM(CASE WHEN LOWER(sentiment_label) = 'neutral' THEN 1 ELSE 0 END) AS neutral_count
            FROM silver.news_sentiment
            WHERE sentiment_score IS NOT NULL
              AND published_at IS NOT NULL
              AND DATE(published_at) = (
                  SELECT MAX(DATE(published_at))
                  FROM silver.news_sentiment
                  WHERE sentiment_score IS NOT NULL
                    AND published_at IS NOT NULL
              )
            GROUP BY DATE(published_at)
        """),
    ]

    silver_sentiment = _run_sentiment_queries(db, "silver.news_sentiment", silver_queries)
    if silver_sentiment:
        return silver_sentiment

    logger.warning("Returning neutral fallback because sentiment data is not ready.")
    return _neutral_sentiment_response()
