
import uuid

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.db import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    # Ensures that the quantity of an ordered product is always greater than zero.
    # Ensures that the unit price of an ordered product cannot be negative.
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_order_items_unit_price_nonnegative",
        ),
    )

    # Unique identifier for each order item, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References the order to which this item belongs.
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)

    # References the product included in this order item.
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Stores the number of units of the product included in the order.
    quantity = Column(Integer, nullable=False)

    # Stores the product's price per unit at the time the order was placed.
    unit_price = Column(Numeric(10, 2), nullable=False)
