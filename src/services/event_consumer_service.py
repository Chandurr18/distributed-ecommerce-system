
import json
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer

from src.core.db import SessionLocal
from src.core.kafka import KAFKA_BOOTSTRAP_SERVERS, ORDER_EVENTS_TOPIC
from src.repositories.processed_event_repository import (
    ProcessedEventRepository,
)
from src.repositories.notification_repository import (
    NotificationRepository,
)

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    def __init__(self):
        self.topic = ORDER_EVENTS_TOPIC
        self.consumer_name = "order-event-consumer"

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.consumer_name,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )

    async def start(self):
        await self.consumer.start()
        logger.info("Order event consumer started")

    async def consume(self):
        try:
            async for message in self.consumer:
                await self.process_message(message)
        except Exception:
            logger.exception("Kafka consumer encountered an error")
            raise

    async def process_message(self, message):
        event = json.loads(message.value.decode("utf-8"))

        event_id = UUID(
            event.get("event_id") or event.get("event-id")
        )

        event_type = (
            event.get("event_type") or event.get("event-type")
        )

        db = SessionLocal()

        try:
            repository = ProcessedEventRepository(db)

            is_new = repository.claim_event(
                event_id=event_id,
                consumer_name=self.consumer_name,
            )

            if is_new:
                self.handle_event(event_type, event, db)
                logger.info("Processed event: %s", event_id)
            else:
                logger.info("Duplicate event skipped: %s", event_id)

            # Commit Inbox record and business changes together.
            db.commit()

            # Acknowledge Kafka only after the DB commit.
            await self.consumer.commit()

        except Exception:
            db.rollback()
            logger.exception("Failed to process event: %s", event_id)
            raise

        finally:
            db.close()

    def handle_event(self, event_type, event, db):
        if event_type == "order.created":
            self.handle_order_created(event, db)
        else:
            logger.warning("Unknown event type: %s", event_type)

    
    def handle_order_created(self, event, db):
        payload = event.get("payload", {})

        user_id = UUID(payload["user_id"])
        order_id = UUID(payload["order_id"])

        notification_repository = NotificationRepository(db)

        notification_repository.create_order_confirmation(
            user_id=user_id,
            order_id=order_id,
        )

        logger.info(
            "Order confirmation notification created for order: %s",
            order_id,
        )


    async def stop(self):
        await self.consumer.stop()
        logger.info("Order event consumer stopped")
