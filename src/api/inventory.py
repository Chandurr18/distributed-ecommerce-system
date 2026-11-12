
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.dependencies.database import get_db

from src.schemas.inventory_schema import (
    InventoryResponse,
    StockAdjustmentRequest,
)

from src.services.inventory_service import (
    InventoryService,
    ProductNotFoundError,
    InventoryNotFoundError,
    InsufficientStockError,
)


router = APIRouter(tags=["Inventory"])


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
)
def get_inventory(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    inventory_service = InventoryService(db)

    try:
        return inventory_service.get_inventory(product_id)

    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    except InventoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )


@router.post(
    "/{product_id}/stock",
    response_model=InventoryResponse,
)
def add_stock(
    product_id: UUID,
    stock_data: StockAdjustmentRequest,
    db: Session = Depends(get_db),
):

    inventory_service = InventoryService(db)

    try:
        return inventory_service.add_stock(
            product_id,
            stock_data.quantity,
        )

    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


@router.post(
    "/{product_id}/deduct",
    response_model=InventoryResponse,
)
def deduct_stock(
    product_id: UUID,
    stock_data: StockAdjustmentRequest,
    db: Session = Depends(get_db),
):

    inventory_service = InventoryService(db)

    try:
        return inventory_service.deduct_stock(
            product_id,
            stock_data.quantity,
        )

    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    except InventoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )

    except InsufficientStockError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient stock available",
        )
