import logging
from typing import Generator

import redis

from src.dependencies.config import Config

logger = logging.getLogger(__name__)
config = Config()

redis_host = config.get("REDIS_HOST", "localhost")
redis_port = int(config.get("REDIS_PORT", "6379"))

# Global Redis client - used for production
redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    decode_responses=True,
)


def get_redis_client() -> Generator[redis.Redis, None, None]:
    """
    FastAPI dependency that provides a Redis client.

    Usage:
        @router.get("/feed")
        def get_feed(redis: redis.Redis = Depends(get_redis_client)):
            return redis.lrange("key", 0, -1)
    """
    yield redis_client


def get_feed_tweet_ids(
    redis_conn: redis.Redis,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[str]:
    """
    Get tweet IDs from user's feed stored in Redis.
    Feed key pattern: feed:{user_id}
    Returns list of tweet IDs (newest first).
    """
    feed_key = f"feed:{user_id}"
    end = offset + limit - 1

    tweet_ids = redis_conn.lrange(feed_key, offset, end)

    logger.info(f"Retrieved {len(tweet_ids)} tweet IDs from feed for user {user_id}")
    return tweet_ids
