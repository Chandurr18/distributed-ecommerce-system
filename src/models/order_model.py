
import uuid

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class Order(Base):
    __tablename__ = "orders"

    # Ensures that the order's total amount cannot be negative.
    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_nonnegative",
        ),
    )

    # Unique identifier for each order, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References the user who placed the order.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Stores the total monetary amount of the order.
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Stores the current order status, defaulting to pending.
    status = Column(String(30), default="pending", nullable=False)

    # Automatically stores the date and time when the order is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
