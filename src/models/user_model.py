
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base

class User(Base):
    __tablename__ = "users"

    # Unique identifier for each user, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User's email address; must be unique and cannot be empty.
    email = Column(String, unique=True, nullable=False, index=True)

    # Stores the securely hashed password instead of the original password.
    password_hash = Column(String, nullable=False)

    # Automatically stores the date and time when the user is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
