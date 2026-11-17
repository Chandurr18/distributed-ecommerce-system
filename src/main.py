
import asyncio
import logging

from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, APIRouter

from src.core.kafka import create_kafka_producer
from src.api.health import router as health_router
from src.api.products import router as products_router
from src.api.inventory import router as inventory_router
from src.api.orders import router as order_router
from src.services.outbox_worker import run_outbox_worker
from src.services.event_consumer_service import OrderEventConsumer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Kafka producer
    producer = create_kafka_producer()
    await producer.start()
    app.state.kafka_producer = producer
    print("Kafka producer started successfully")

    # Start Outbox publisher worker
    worker_task = asyncio.create_task(
        run_outbox_worker(producer)
    )
    app.state.worker_task = worker_task
    print("Outbox worker started successfully")

    # Start Kafka consumer
    event_consumer = OrderEventConsumer()
    await event_consumer.start()

    consumer_task = asyncio.create_task(
        event_consumer.consume()
    )
    app.state.event_consumer = event_consumer
    app.state.consumer_task = consumer_task
    print("Kafka consumer started successfully")

    yield

    # Stop background tasks
    worker_task.cancel()
    consumer_task.cancel()

    with suppress(asyncio.CancelledError):
        await worker_task

    with suppress(asyncio.CancelledError):
        await consumer_task

    # Stop Kafka consumer and producer
    await event_consumer.stop()
    await producer.stop()

    print("Kafka services stopped")


app = FastAPI(
    title="E-Commerce Backend",
    description="Production-style E-Commerce Backend API",
    version="1.0.0",
    lifespan=lifespan
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(order_router)

app.include_router(api_router)
