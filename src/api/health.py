
import json
import logging

from fastapi import APIRouter, HTTPException, Request

from src.core.kafka import ORDER_EVENTS_TOPIC

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "message": "E-Commerce Backend is running"
    }


@router.get("/health/redis", tags=["Redis"])
def redis_health_check(request: Request):

    redis_client = request.app.state.redis

    try:
        redis_client.ping()

        return {
            "status": "healthy",
            "service": "redis",
            "message": "Redis connection successful"
        }

    except Exception:
        logger.exception("Redis health check failed")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "redis",
                "message": "Redis is unavailable"
            }
        )

    
@router.post("/health/kafka", tags=["Kafka"])
async def kafka_test(request: Request):

    producer = request.app.state.kafka_producer

    message = {
        "event_type": "order.created",
        "event_id": "101",
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
