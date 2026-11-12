
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    # Unique identifier for each outbox event, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Stores the type or name of the event that needs to be published.
    event_type = Column(String(100), nullable=False)

    # Stores the event data in JSON format for processing by consumers.
    payload = Column(JSON, nullable=False)

    # Tracks the publishing status of the event, defaulting to pending.
    status = Column(String(30), default="pending", nullable=False)

    # Automatically stores the date and time when the event is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Stores the date and time when the event was successfully published.
    published_at = Column(DateTime(timezone=True), nullable=True)
