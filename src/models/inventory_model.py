
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class Inventory(Base):
    __tablename__ = "inventory"

    # Ensures that product quantity can never be negative.
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="ck_inventory_quantity_nonnegative",
        ),
    )

    # Unique identifier for each inventory record, automatically generated as a UUID.
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # References the product whose stock is being tracked; each product has one inventory record.
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        unique=True,
        nullable=False,
    )

    # Stores the current available stock quantity of the product.
    quantity = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # Stores the last update time and automatically changes whenever the record is updated.
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
