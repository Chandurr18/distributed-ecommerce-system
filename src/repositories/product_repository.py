from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from decimal import Decimal

from src.models.product_model import Product
from src.schemas.product_schema import ProductCreate, ProductUpdate

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, product_data: ProductCreate) -> Product:
        new_product = Product(
            name = product_data.name,
            description = product_data.description,
            price = product_data.price
        )

        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)

        return new_product

    def get_by_id(self, product_id: UUID) -> Product | None :
        return (
            self.db.query(Product)
            .filter(
                Product.id == product_id, 
                Product.is_active == True
            )
            .first()
        )

    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 10,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",   
    ) -> tuple[list[Product], int]:
        query = self.db.query(Product).filter(
            Product.is_active.is_(True)
        )

        if search:
            query = query.filter(
                Product.name.ilike(f"%{search}%")  # ilike: It performs case-insensitive searches.
            )

        if min_price is not None:
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        total = query.count()

        sort_columns = {
            "price": Product.price,
            "created_at": Product.created_at,
            "name": func.lower(Product.name),
        }

        sort_column = sort_columns[sort_by]

        if sort_order == 'asc':
            products = query.order_by(
                sort_column.asc(),
                Product.id.asc()
            )
        else:
            products = query.order_by(
                sort_column.desc(),
                Product.id.asc()
            )

        products = (
            products
            .offset(skip)
            .limit(limit)
            .all()
        )

        return products, total

    def update(
        self,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Product | None:

        product = self.get_by_id(product_id)

        if product is None:
            return None

        product.name = product_data.name
        product.description = product_data.description
        product.price = product_data.price
        product.is_active = product_data.is_active

        self.db.commit()
        self.db.refresh(product)

        return product

    def soft_delete(self, product_id: UUID) -> bool:
        product = self.get_by_id(product_id)

        if product is None:
            return False

        product.is_active = False

        self.db.commit()
        self.db.refresh(product)

        return True