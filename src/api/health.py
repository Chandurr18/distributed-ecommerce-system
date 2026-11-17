
import json

from fastapi import APIRouter, Request

from src.core.kafka import ORDER_EVENTS_TOPIC

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "message": "E-Commerce Backend is running"
    }

@router.post("/kafka-test", tags=["Kafka"])
async def kafka_test(request: Request):

    producer = request.app.state.kafka_producer

    message = {
        "event_type": "order.created",
        "order_id": "101",
        "message": "Hello from FastAPI!"
    }

    await producer.send_and_wait(
        ORDER_EVENTS_TOPIC,
        value=json.dumps(message).encode("utf-8")
    )

    return {
        "status": "success",
        "message": "Event published to Kafka",
        "event": message
    }
