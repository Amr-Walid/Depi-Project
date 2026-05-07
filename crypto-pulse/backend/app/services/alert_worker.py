"""
Background worker for price alert monitoring.

Run with:
    python -m app.services.alert_worker
"""
import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] alert-worker: %(message)s",
)
logger = logging.getLogger(__name__)
CHECK_INTERVAL_SECONDS = 60


def check_alerts() -> None:
    """Check active alerts against the latest Gold market prices."""
    db = SessionLocal()
    try:
        price_rows = db.execute(text("""
            SELECT symbol, close_price
            FROM (
                SELECT
                    symbol,
                    close_price,
                    ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS row_num
                FROM gold.daily_market_summary
                WHERE close_price IS NOT NULL
            ) latest_prices
            WHERE row_num = 1
        """)).fetchall()

        if not price_rows:
            logger.info("No latest prices found in gold.daily_market_summary.")
            return

        price_map = {row.symbol.upper(): float(row.close_price) for row in price_rows}

        active_alerts = db.execute(text("""
            SELECT id, user_id, symbol, condition, threshold
            FROM alerts
            WHERE is_active = TRUE
        """)).fetchall()

        if not active_alerts:
            logger.info("No active alerts to evaluate.")
            return

        triggered_count = 0
        for alert in active_alerts:
            symbol = alert.symbol.upper()
            current_price = price_map.get(symbol)
            if current_price is None:
                logger.info("No latest price for active alert %s (%s).", alert.id, symbol)
                continue

            threshold = float(alert.threshold)
            condition = alert.condition
            triggered = (
                (condition == "above" and current_price >= threshold)
                or (condition == "below" and current_price <= threshold)
            )

            if not triggered:
                continue

            message = (
                f"ALERT TRIGGERED: alert_id={alert.id} user_id={alert.user_id} "
                f"{symbol} is {condition} {threshold} (current: {current_price})"
            )
            print(message, flush=True)
            logger.info(message)
            db.execute(
                text("UPDATE alerts SET is_active = FALSE WHERE id = :alert_id"),
                {"alert_id": alert.id},
            )
            db.commit()
            triggered_count += 1

        logger.info("Alert check complete. Triggered %s alert(s).", triggered_count)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Database error while checking alerts; will retry: %s", exc)
    finally:
        db.close()


def run_worker() -> None:
    """Run the alert worker forever."""
    logger.info("Starting alert worker. Poll interval: %s seconds.", CHECK_INTERVAL_SECONDS)
    while True:
        check_alerts()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()
