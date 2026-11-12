
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    # Temporary until authentication is implemented.
    user_id: UUID

    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_products(self):
        product_ids = [item.product_id for item in self.items]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate products are not allowed")

        return self


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    orders: list[OrderResponse]
