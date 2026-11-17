from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.models.processed_event_model import ProcessedEvent


class ProcessedEventRepository:
    def __init__(self, db):
        self.db = db

    def claim_event(self, event_id, consumer_name):
        statement = (
            insert(ProcessedEvent)
            .values(
                event_id=event_id,
                consumer_name=consumer_name,
            )
            .on_conflict_do_nothing(
                index_elements=["event_id"]
            )
            .returning(ProcessedEvent.id)
        )

        inserted_id = self.db.execute(statement).scalar_one_or_none()

        return inserted_id is not None