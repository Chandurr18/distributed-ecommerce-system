
import asyncio

from src.core.redis import create_redis_client

async def main():
    redis_client = create_redis_client()

    try:
        response = await redis_client.ping()
        logger.debug("Redis connection successful:", response)

        await redis_client.set("test:key", "Hello Redis")

        value = await redis_client.get("test:key")
        logger.debug("Retrieved value:", value)

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
