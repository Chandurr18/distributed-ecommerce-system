
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.db import Base


class Product(Base):
    __tablename__ = "products"

    # Unique identifier for each product, automatically generated as a UUID.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Stores the product name, which is required and limited to 150 characters.
    name = Column(String(150), nullable=False)

    # Stores an optional detailed description of the product.
    description = Column(Text, nullable=True)

    # Stores the product price with up to 10 digits and 2 decimal places.
    price = Column(Numeric(10, 2), nullable=False)

    # Indicates whether the product is currently available for sale.
    is_active = Column(Boolean, default=True, nullable=False)

    # Automatically stores the date and time when the product is created.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
