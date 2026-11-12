
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    # Ensures the same idempotency key cannot be reused by the same user.
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_user_idempotency_key",
        ),
    )

    # Unique identifier for each idempotency record, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References the user who made the request.
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Stores a unique key used to identify and prevent duplicate requests from the same user.
    idempotency_key = Column(
        String(255),
        nullable=False,
    )

    # Stores the hash of the original request to identify whether a repeated request has changed.
    request_hash = Column(String(64), nullable=False)

    # Stores the HTTP status code of the original response.
    response_status = Column(Integer, nullable=True)

    # Stores the original response data so it can be returned for duplicate requests.
    response_body = Column(JSON, nullable=True)

    # Automatically stores the date and time when the idempotency record is created.
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
