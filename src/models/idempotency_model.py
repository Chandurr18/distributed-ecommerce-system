
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

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_user_idempotency_key",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    idempotency_key = Column(
        String(255),
        nullable=False,
    )

    request_hash = Column(String(64), nullable=False)

    response_status = Column(Integer, nullable=True)

    response_body = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
