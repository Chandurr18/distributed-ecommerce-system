import logging
import hashlib
import json

from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal

from src.repositories.product_repository import ProductRepository
from src.schemas.product_schema import ProductCreate, ProductUpdate, ProductResponse
from src.models.product_model import Product

logger = logging.getLogger(__name__)
PRODUCT_CACHE_TTL = 300  # 5 minutes 

class ProductService:
    def __init__(self, db: Session, redis_client = None):
        self.repository = ProductRepository(db)
        self.redis = redis_client

    def create_product(self, product_data: ProductCreate):
        product = self.repository.create(product_data)

        if product is not None:
            self._invalidate_product_list_cache()

        return product

    def get_product_by_id(self, product_id: UUID) -> Product | None:

        cache_key = f"product:{product_id}"

        # Step 1: Check Redis
        if self.redis is not None:
            try:
                cached_product = self.redis.get(cache_key)

                if(cached_product):
                    logger.debug("Product cache HIT: %s", product_id)
                    return ProductResponse.model_validate_json(
                        cached_product
                    )
            except Exception:
                logger.exception(
                    "Redis cache read failed for product: %s",
                    product_id
                )

        # Step 2: Fetch from PostgreSQL
        logger.debug("Product cache MISS: %s", product_id)

        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        # Step 3: Store in Redis
        if self.redis is not None:
            try:
                serialized_product = ProductResponse.model_validate(
                    product
                ).model_dump_json()

                self.redis.setex(
                    cache_key,
                    PRODUCT_CACHE_TTL,
                    serialized_product
                )

                logger.debug("Product cached: %s", product_id)

            except Exception:
                logger.exception(
                    "Redis cache write failed for product: %s",
                    product_id
                )
        return product

    def _generate_product_list_cache_key(
        self,
        skip: int,
        limit: int,
        search: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        sort_by: str,
        sort_order: str,
    ) -> str:

        filters = {
            "skip": skip,
            "limit": limit,
            "search": search,
            "min_price": str(min_price) if min_price is not None else None,
            "max_price": str(max_price) if max_price is not None else None,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        normalized_filters = json.dumps(
            filters,
            sort_keys=True
        )

        filters_hash = hashlib.sha256(
            normalized_filters.encode()
        ).hexdigest()

        return f"products:list:{filters_hash}"

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

        cache_key = self._generate_product_list_cache_key(
            skip=skip,
            limit=limit,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Step 1: Check Redis
        if self.redis is not None:
            try:
                cached_products = self.redis.get(cache_key)

                if cached_products:
                    logger.debug("Product list cache HIT: %s", cache_key)

                    return json.loads(cached_products)

            except Exception:
                logger.exception("Product list cache read failed")

        # Step 2: Fetch from PostgreSQL
        logger.debug("Product list cache MISS: %s", cache_key)

        products, total = self.repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": [
                ProductResponse.model_validate(product).model_dump(mode="json")
                for product in products
            ],
        }

        # Step 3: Store in Redis
        if self.redis is not None:
            try:
                self.redis.setex(
                    cache_key,
                    PRODUCT_CACHE_TTL,
                    json.dumps(result)
                )

                logger.debug("Product list cached: %s", cache_key)

            except Exception:
                logger.exception("Product list cache write failed")

        return result
    
    def update_product(
        self,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Product | None:

        product = self.repository.update(
            product_id,
            product_data
        )

        if product is not None:
            self._invalidate_product_cache(product_id)
            self._invalidate_product_list_cache()

        return product

    def delete_product(self, product_id: UUID) -> bool:
        deleted_product = self.repository.soft_delete(product_id)

        if deleted_product:
            self._invalidate_product_cache(product_id)
            self._invalidate_product_list_cache()

        return deleted_product


    def _invalidate_product_cache(self, product_id: UUID):
        if self.redis is None:
            return

        try:
            self.redis.delete(f"product:{product_id}")

            logger.debug("Product cache invalidated: %s", product_id)

        except Exception:
            logger.exception(
                "Product cache invalidation failed: %s",
                product_id
            )

    def _invalidate_product_list_cache(self):
        if self.redis is None:
            return

        try:
            cursor = 0

            while True:
                cursor, keys = self.redis.scan(
                    cursor=cursor,
                    match="products:list:*",
                    count=100
                )

                if keys:
                    self.redis.delete(*keys)

                if cursor == 0:
                    break

            logger.debug("Product list cache invalidated")

        except Exception:
            logger.exception("Product list cache invalidation failed")