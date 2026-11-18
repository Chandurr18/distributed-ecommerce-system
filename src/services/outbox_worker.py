
import asyncio
import logging

from src.core.db import SessionLocal
from src.services.outbox_service import OutboxPublisher

logger = logging.getLogger(__name__)


async def run_outbox_worker(kafka_producer):

    while True:
        db = SessionLocal()

        try:
            publisher = OutboxPublisher(
                db=db,
                kafka_producer=kafka_producer,
            )

            published_count = await publisher.publish_pending_events()

            if published_count:
                logger.debug(
                    "Published %s outbox events",
                    published_count,
                )

        except Exception:
            logger.exception("Outbox publishing failed")

        finally:
            db.close()

        await asyncio.sleep(5)
