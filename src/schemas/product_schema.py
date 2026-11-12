from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    products: list[ProductResponse]


class ProductUpdate(BaseModel):
    name: str
    description: str | None
    price: Decimal
    is_active: bool