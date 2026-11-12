
import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class Payment(Base):
    __tablename__ = "payments"

    # Unique identifier for each payment, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References the order for which this payment is being made.
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)

    # Stores the total amount paid or to be paid for the order.
    amount = Column(Numeric(10, 2), nullable=False)

    # Stores the current payment status, defaulting to pending.
    status = Column(String(30), default="pending", nullable=False)

    # Stores the payment method used, such as card, UPI, or cash.
    payment_method = Column(String(50), nullable=False)

    # Stores the optional unique transaction ID provided by the payment gateway.
    transaction_id = Column(String(100), unique=True, nullable=True)

    # Automatically stores the date and time when the payment record is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
