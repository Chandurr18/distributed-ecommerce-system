
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from src.models.inventory_model import Inventory


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_id(
        self,
        product_id: UUID,
    ) -> Inventory | None:

        return (
            self.db.query(Inventory)
            .filter(Inventory.product_id == product_id)
            .first()
        )

    def add_stock(
        self,
        product_id: UUID,
        quantity: int,
    ) -> Inventory:

        statement = (
            insert(Inventory)
            .values(
                product_id=product_id,
                quantity=quantity,
            )
            .on_conflict_do_update(
                index_elements=[Inventory.product_id],
                set_={
                    "quantity": Inventory.quantity + quantity,
                    "updated_at": func.now(),
                },
            )
            .returning(Inventory.id)
        )

        try:
            inventory_id = self.db.execute(
                statement
            ).scalar_one()

            self.db.commit()

            return (
                self.db.query(Inventory)
                .filter(Inventory.id == inventory_id)
                .one()
            )

        except Exception:
            self.db.rollback()
            raise

    def deduct_stock(
        self,
        product_id: UUID,
        quantity: int,
    ) -> Inventory | None:

        statement = (
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.quantity >= quantity,
            )
            .values(
                quantity=Inventory.quantity - quantity,
                updated_at=func.now(),
            )
            .returning(Inventory.id)
        )

        try:
            inventory_id = self.db.execute(
                statement
            ).scalar_one_or_none()

            if inventory_id is None:
                self.db.rollback()
                return None

            self.db.commit()

            return (
                self.db.query(Inventory)
                .filter(Inventory.id == inventory_id)
                .one()
            )

        except Exception:
            self.db.rollback()
            raise
