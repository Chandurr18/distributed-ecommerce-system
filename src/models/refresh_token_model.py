
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # Unique identifier for each refresh token record, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References the user who owns this refresh token.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Stores the hashed refresh token to keep the original token secure.
    token_hash = Column(String, unique=True, nullable=False)

    # Stores the date and time when the refresh token expires.
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Indicates whether the refresh token has been revoked and can no longer be used.
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Automatically stores the date and time when the refresh token is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
