
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.inventory_model import Inventory
from src.repositories.inventory_repository import InventoryRepository
from src.repositories.product_repository import ProductRepository


class ProductNotFoundError(Exception):
    pass


class InventoryNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class InventoryService:
    def __init__(self, db: Session):
        self.inventory_repository = InventoryRepository(db)
        self.product_repository = ProductRepository(db)

    def get_inventory(self, product_id: UUID) -> Inventory:
        product = self.product_repository.get_by_id(product_id)

        if product is None:
            raise ProductNotFoundError("Product not found")

        inventory = self.inventory_repository.get_by_product_id(
            product_id
        )

        if inventory is None:
            raise InventoryNotFoundError("Inventory not found")

        return inventory

    def add_stock(
        self,
        product_id: UUID,
        quantity: int,
    ) -> Inventory:
        product = self.product_repository.get_by_id(product_id)

        if product is None:
            raise ProductNotFoundError("Product not found")

        return self.inventory_repository.add_stock(
            product_id,
            quantity,
        )

    def deduct_stock(
        self,
        product_id: UUID,
        quantity: int,
    ) -> Inventory:
        product = self.product_repository.get_by_id(product_id)

        if product is None:
            raise ProductNotFoundError("Product not found")

        inventory = self.inventory_repository.get_by_product_id(
            product_id
        )

        if inventory is None:
            raise InventoryNotFoundError("Inventory not found")

        updated_inventory = self.inventory_repository.deduct_stock(
            product_id,
            quantity,
        )

        if updated_inventory is None:
            raise InsufficientStockError("Insufficient stock available")

        return updated_inventory
