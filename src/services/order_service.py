
import hashlib
import json

from decimal import Decimal

from src.models.order_model import Order
from src.models.order_item_model import OrderItem
from src.models.outbox_event_model import OutboxEvent
from src.repositories.order_repository import OrderRepository


class UserNotFoundError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class InventoryNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderCannotBeCancelledError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


class OrderService:

    def __init__(self, db):
        self.db = db
        self.repository = OrderRepository(db)

    def _serialize_order(self, order, items):
        return {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "total_amount": str(order.total_amount),
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                }
                for item in items
            ],
        }

    def create_order(self, payload, idempotency_key):
        request_data = {
            "user_id": str(payload.user_id),
            "items": sorted(
                [
                    {
                        "product_id": str(item.product_id),
                        "quantity": item.quantity,
                    }
                    for item in payload.items
                ],
                key=lambda item: item["product_id"],
            ),
        }

        request_hash = hashlib.sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()

        try:
            record, is_new = self.repository.claim_idempotency_key(
                payload.user_id,
                idempotency_key,
                request_hash,
            )

            if not is_new:
                if record.request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "Idempotency key was used with a different request"
                    )

                if record.response_body is None:
                    raise IdempotencyConflictError(
                        "This request is still being processed"
                    )

                body = record.response_body
                status = record.response_status or 201

                self.db.commit()
                return body, status

            user = self.repository.get_user(payload.user_id)

            if not user:
                raise UserNotFoundError("User not found")

            product_ids = [item.product_id for item in payload.items]

            products = self.repository.get_active_products(product_ids)

            product_map = {product.id: product for product in products}

            if len(product_map) != len(set(product_ids)):
                raise ProductNotFoundError(
                    "One or more products do not exist or are inactive"
                )

            total_amount = Decimal("0.00")
            order_items = []

            # Lock and deduct each product's inventory.
            for requested_item in payload.items:

                product = product_map[requested_item.product_id]

                inventory = self.repository.get_inventory_for_update(
                    requested_item.product_id
                )

                if not inventory:
                    raise InventoryNotFoundError(
                        f"Inventory not found for product {product.name}"
                    )

                if inventory.quantity < requested_item.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for product {product.name}"
                    )

                inventory.quantity -= requested_item.quantity

                unit_price = Decimal(str(product.price))

                total_amount += unit_price * requested_item.quantity

                order_items.append(
                    OrderItem(
                        product_id=product.id,
                        quantity=requested_item.quantity,
                        unit_price=unit_price,
                    )
                )

            total_amount = total_amount.quantize(Decimal("0.01"))

            order = Order(
                user_id=payload.user_id,
                total_amount=total_amount,
                status="pending",
            )

            self.repository.add_order(order)

            for item in order_items:
                item.order_id = order.id

            self.repository.add_order_items(order_items)

            self.db.refresh(order)

            response_body = self._serialize_order(order, order_items)

            # Store the response for idempotent retries.
            record.response_status = 201
            record.response_body = response_body

            # Store the event in the same database transaction.
            self.repository.add_outbox_event(
                OutboxEvent(
                    event_type="order.created",
                    payload={
                        "order_id": str(order.id),
                        "user_id": str(order.user_id),
                        "total_amount": str(total_amount),
                        "items": [
                            {
                                "product_id": str(item.product_id),
                                "quantity": item.quantity,
                            }
                            for item in order_items
                        ],
                    },
                    status="pending",
                )
            )

            self.db.commit()

            return response_body, 201

        except Exception:
            self.db.rollback()
            raise

    def get_order_by_id(self, order_id, user_id):

        order = self.repository.get_order(order_id, user_id)

        if not order:
            raise OrderNotFoundError("Order not found")

        items = self.repository.get_order_items(order.id)

        return self._serialize_order(order, items)

    def get_all_orders(self, user_id, skip, limit):

        orders, total = self.repository.get_orders(
            user_id,
            skip,
            limit,
        )

        items = self.repository.get_items_for_orders(
            [order.id for order in orders]
        )

        items_map = {}

        for item in items:
            items_map.setdefault(item.order_id, []).append(item)

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": [
                self._serialize_order(
                    order,
                    items_map.get(order.id, []),
                )
                for order in orders
            ],
        }

    def cancel_order(self, order_id, user_id):

        try:
            order = self.repository.get_order(
                order_id,
                user_id,
                lock=True,
            )

            if not order:
                raise OrderNotFoundError("Order not found")

            if order.status != "pending":
                raise OrderCannotBeCancelledError(
                    "Only pending orders can be cancelled"
                )

            items = self.repository.get_order_items(order.id)

            # Restore stock inside the same transaction.
            for item in items:

                inventory = self.repository.get_inventory_for_update(
                    item.product_id
                )

                if not inventory:
                    raise InventoryNotFoundError(
                        "Inventory record missing during cancellation"
                    )

                inventory.quantity += item.quantity

            order.status = "cancelled"

            self.repository.add_outbox_event(
                OutboxEvent(
                    event_type="order.cancelled",
                    payload={
                        "order_id": str(order.id),
                        "user_id": str(order.user_id),
                    },
                    status="pending",
                )
            )

            self.db.commit()

            return self._serialize_order(order, items)

        except Exception:
            self.db.rollback()
            raise
