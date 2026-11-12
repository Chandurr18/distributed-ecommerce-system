
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Header,
    Query,
    Response,
)

from sqlalchemy.orm import Session

from src.core.db import get_db

from src.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
)

from src.services.order_service import (
    OrderService,
    UserNotFoundError,
    ProductNotFoundError,
    InventoryNotFoundError,
    InsufficientStockError,
    OrderNotFoundError,
    OrderCannotBeCancelledError,
    IdempotencyConflictError,
)


router = APIRouter(prefix="/orders", tags=["Orders"])


def handle_order_error(error):
    if isinstance(error, (UserNotFoundError,
                          ProductNotFoundError,
                          OrderNotFoundError)):
        raise HTTPException(status_code=404, detail=str(error))

    if isinstance(error, (
        InventoryNotFoundError,
        InsufficientStockError,
        OrderCannotBeCancelledError,
        IdempotencyConflictError,
    )):
        raise HTTPException(status_code=409, detail=str(error))

    raise error


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
)
def create_order(
    payload: OrderCreate,
    response: Response,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:
        body, status = service.create_order(
            payload,
            idempotency_key,
        )

        response.status_code = status

        return body

    except Exception as error:
        handle_order_error(error)


@router.get(
    "",
    response_model=OrderListResponse,
)
def get_orders(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    return service.get_all_orders(user_id, skip, limit)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:
        return service.get_order_by_id(order_id, user_id)

    except Exception as error:
        handle_order_error(error)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order(
    order_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:
        return service.cancel_order(order_id, user_id)

    except Exception as error:
        handle_order_error(error)
