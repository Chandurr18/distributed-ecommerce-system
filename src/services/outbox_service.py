import json

from src.repositories.outbox_repository import OutboxRepository
from src.core.kafka import ORDER_EVENTS_TOPIC

class OutboxPublisher:
    def __init__(self, db, kafka_producer):
        self.db = db
        self.repository = OutboxRepository(db)
        self.kafka_producer = kafka_producer

    async def publish_pending_events(self):

        pending_events = self.repository.get_pending_events()

        published_count = 0

        for event in pending_events:

            try:
                message = {
                    "event-id": str(event.id),
                    "event-type": event.event_type,
                    "payload": event.payload
                }

                await self.kafka_producer.send_and_wait(
                    ORDER_EVENTS_TOPIC,
                    value = json.dumps(message).encode("utf-8"),
                )

                self.repository.mark_event_published(event)

                self.db.commit()

                published_count += 1

            except Exception:
                self.db.rollback()
                raise

        return published_count