
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.order_model import Order
from src.models.order_item_model import OrderItem
from src.models.product_model import Product
from src.models.inventory_model import Inventory
from src.models.user_model import User
from src.models.idempotency_model import IdempotencyRecord
from src.models.outbox_event_model import OutboxEvent


class OrderRepository:

    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        return self.db.get(User, user_id)

    def get_active_products(self, product_ids):
        statement = select(Product).where(
            Product.id.in_(product_ids),
            Product.is_active.is_(True),
        )

        return self.db.execute(statement).scalars().all()

    def get_inventory_for_update(self, product_id):
        statement = (
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )

        return self.db.execute(statement).scalar_one_or_none()

    def add_order(self, order):
        self.db.add(order)
        self.db.flush()
        return order

    def add_order_items(self, items):
        self.db.add_all(items)
        self.db.flush()

    def claim_idempotency_key(self, user_id, key, request_hash):
        statement = (
            pg_insert(IdempotencyRecord)
            .values(
                user_id=user_id,
                idempotency_key=key,
                request_hash=request_hash,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    IdempotencyRecord.user_id,
                    IdempotencyRecord.idempotency_key
                ]
            )
            .returning(IdempotencyRecord.id)
        )

        inserted_id = self.db.execute(statement).scalar_one_or_none()

        if inserted_id:
            return self.db.get(IdempotencyRecord, inserted_id), True

        existing = self.db.execute(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.idempotency_key == key
            )
            .with_for_update()
        ).scalar_one()

        return existing, False

    def get_order(self, order_id, user_id, lock=False):
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )

        if lock:
            statement = statement.with_for_update()

        return self.db.execute(statement).scalar_one_or_none()

    def get_order_items(self, order_id):
        statement = select(OrderItem).where(
            OrderItem.order_id == order_id
        )

        return self.db.execute(statement).scalars().all()

    def get_items_for_orders(self, order_ids):
        if not order_ids:
            return []

        statement = select(OrderItem).where(
            OrderItem.order_id.in_(order_ids)
        )

        return self.db.execute(statement).scalars().all()

    def get_orders(self, user_id, skip, limit):
        count_statement = select(func.count()).select_from(Order).where(
            Order.user_id == user_id
        )

        total = self.db.execute(count_statement).scalar_one()

        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.asc())
            .offset(skip)
            .limit(limit)
        )

        orders = self.db.execute(statement).scalars().all()

        return orders, total

    def add_outbox_event(self, event):
        self.db.add(event)
