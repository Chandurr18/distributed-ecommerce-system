
import os

from redis import Redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)


def create_redis_client() -> Redis:
    return Redis.from_url(
        REDIS_URL,
        decode_responses=True
    )


def close_redis_client(client: Redis) -> None:
    client.close()
