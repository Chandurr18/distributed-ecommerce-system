from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from typing import Literal

from src.dependencies.database import get_db
from src.schemas.product_schema import ProductResponse, ProductCreate, ProductUpdate, ProductListResponse
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.post(
    "",
    response_model = ProductResponse,
    status_code = status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    return product_service.create_product(product_data)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)

    if(product is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product

@router.get(
    "",
    response_model=ProductListResponse,
)
def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    sort_by: Literal["price", "created_at", "name"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price cannot be greater than max_price",
        )

    product_service = ProductService(db)

    return product_service.get_all_products(
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product_service = ProductService(db)

    product = product_service.update_product(
        product_id,
        product_data
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    product_service = ProductService(db)

    deleted = product_service.delete_product(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )