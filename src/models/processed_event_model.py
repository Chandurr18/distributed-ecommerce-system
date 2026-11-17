import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID


from src.core.db import Base

class ProcessedEvent(Base):
    __tablename__ = "processed_events"


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True
    )

    consumer_name = Column(String(100), nullable=False)

    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )