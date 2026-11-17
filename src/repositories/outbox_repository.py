from sqlalchemy import select, func

from src.models.outbox_event_model import OutboxEvent

class OutboxRepository:
    def __init__(self, db):
        self.db = db

    def mark_event_published(self, event):
        event.status = "published"
        event.published_at = func.now()

        self.db.add(event)

    def get_pending_events(self, limit = 1):
        statement = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        return self.db.execute(statement).scalars().all()

    