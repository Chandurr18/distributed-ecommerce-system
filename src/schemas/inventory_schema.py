
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockAdjustmentRequest(BaseModel):
    quantity: int = Field(gt=0)


class InventoryResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
