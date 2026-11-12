from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal

from src.repositories.product_repository import ProductRepository
from src.schemas.product_schema import ProductCreate, ProductUpdate
from src.models.product_model import Product

class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def create_product(self, product_data: ProductCreate):
        return self.repository.create(product_data)

    def get_product_by_id(self, product_id: UUID) -> Product | None:
        return self.repository.get_by_id(product_id)

    def get_all_products(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        products, total = self.repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": products
        }

    def update_product(
        self,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Product | None:

        return self.repository.update(
            product_id,
            product_data
        )

    def delete_product(self, product_id: UUID) -> bool:
        return self.repository.soft_delete(product_id)