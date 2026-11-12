from fastapi import FastAPI, APIRouter

from src.api.health import router as health_router
from src.api.products import router as products_router
from src.api.inventory import router as inventory_router
from src.api.orders import router as order_router

app = FastAPI(
    title="E-Commerce Backend",
    description="Production-style E-Commerce Backend API",
    version="1.0.0",
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(order_router)


app.include_router(api_router)