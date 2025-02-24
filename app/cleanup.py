import logging
from datetime import datetime, timedelta
from app import models
from db import get_db
from config import CLEANUP_HISTORY_DAYS, STUCK_LOADING_HOURS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_old_data():
    db = next(get_db())
    try:
        # Удаляем записи старше N дней
        days_ago = datetime.utcnow() - timedelta(days=CLEANUP_HISTORY_DAYS)
        deleted_count = db.query(models.ShipmentHistory).filter(
            models.ShipmentHistory.created_at < days_ago
        ).delete()
        logger.info(f"Deleted {deleted_count} old shipment records")

        # Освобождаем корабли
        hours_ago = datetime.utcnow() - timedelta(hours=STUCK_LOADING_HOURS)
        ships_to_free = db.query(models.Starship).filter(
            models.Starship.status == models.StarshipStatus.LOADING
        ).all()

        freed_count = 0
        for ship in ships_to_free:
            latest_shipment = db.query(models.ShipmentHistory).filter(
                models.ShipmentHistory.starship_id == ship.id
            ).order_by(models.ShipmentHistory.created_at.desc()).first()

            if latest_shipment and latest_shipment.created_at < hours_ago:
                ship.status = models.StarshipStatus.AVAILABLE
                freed_count += 1

        logger.info(f"Freed {freed_count} stuck ships")
        db.commit()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
